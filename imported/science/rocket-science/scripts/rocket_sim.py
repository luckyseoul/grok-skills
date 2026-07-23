#!/usr/bin/env python3
"""
rocket_sim.py — Physics-accurate rocket & jet propulsion simulator.

Features:
- 2D variable-mass dynamics with inverse-square gravity + realistic atmosphere
- Accurate numerical integration (scipy.solve_ivp RK45 + dense)
- Configurable multi-stage rockets with staging events
- Sea-level / vacuum thrust distinction + simple pressure thrust
- Basic air-breathing jet model (ram drag, altitude lapse, mach effects)
- New: "electric" mode – battery energy limited + power-to-thrust (high Isp, reaction mass still required). Novel concepts: resistojet, ion, railgun pellet.
- Telemetry logging to .npz (everything: state, forces, Mach, q, battery_frac, etc.)
- Cinematic / engineering visualization with matplotlib Agg
- Direct MP4 video export via FFMpegWriter (serial) OR massively parallel (multiprocessing + ffmpeg)
- GPU-accelerated exhaust particles via CuPy on V100 (falls back to numpy)
- CLI with presets, overrides, video + data export; --workers (0=auto-parallel on 88 cores)
- Leverages this machine: 88-core Xeon + V100 16GB + 60 GiB RAM

Run examples:
  python rocket_sim.py --preset falcon9-booster --video falcon9.mp4 --duration 180
  python rocket_sim.py --preset sounding --video sounding.mp4 --fps 60 --res 1920x1080 --workers 40
  # Starship 3 (full stack, large booster + ship)
  python rocket_sim.py --preset starship3 --video starship3.mp4 --duration 350 --fps 15 --res 1280x720
  # Lunar gravity launch (3D, from Moon surface, vacuum)
  python rocket_sim.py --preset lunar-launch --video lunar.mp4 --duration 120 --fps 20 --res 1280x720
  # Kettle tea kettle second stage projectile (gun launch + ejects kettle stage while propelling)
  python rocket_sim.py --preset kettle-projectile --video kettle4k.mp4 --duration 30 --fps 20 --res 3840x2160
  # Hypothetical battery electric
  python rocket_sim.py --preset battery-resistojet --duration 120 --video /tmp/batt.mp4
  python rocket_sim.py --preset battery-railgun --no-video --data /tmp/rail
  python rocket_sim.py --config myrocket.json --particles 800 --use-gpu --workers 0  # auto 88-core parallel

Physics notes:
- State: x (downrange), h (altitude), vx, vy, m (current mass)
- Thrust direction follows body angle theta (0 = vertical). Simple pitch program + gravity turn.
- Drag: 0.5 * rho * v^2 * Cd(M) * Aref
- Variable Cd with Mach (sub/trans/super)
- Mass flow from Isp or direct mdot. Propellant consumed until stage depletion.
- Events: burnout, apogee, impact.
"""

import argparse
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Tuple, Callable, Dict, Any

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
from matplotlib.patches import Polygon, Circle, FancyArrowPatch
from matplotlib.collections import LineCollection
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from mpl_toolkits.mplot3d import Axes3D

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import shutil
import tempfile
import glob

# --------------------------- Hardware / Backend ---------------------------

def detect_gpu_backend():
    # Suppress banner inside worker processes
    quiet = os.environ.get("ROCKET_SIM_QUIET_GPU", "") == "1"
    try:
        import cupy as cp
        if cp.cuda.is_available():
            dev = cp.cuda.runtime.getDeviceProperties(0)
            name = dev['name'].decode() if isinstance(dev['name'], bytes) else dev['name']
            if not quiet:
                print(f"[GPU] CuPy + {name} available (using for particles)")
            return "cupy", cp
    except Exception as e:
        pass
    if not quiet:
        print("[GPU] CuPy not available or no CUDA, using numpy for particles")
    return "numpy", np


GPU_BACKEND, XP = detect_gpu_backend()  # XP is cupy or numpy

# --------------------------- Physical Constants ---------------------------

G0 = 9.80665          # m/s^2 standard gravity
R_EARTH = 6371000.0   # m mean radius
GM_EARTH = 3.986004418e14  # m^3/s^2
OMEGA_EARTH = 7.292115e-5  # rad/s

# Lunar constants for "launch from lunar gravity"
R_MOON = 1737400.0    # m mean radius
GM_MOON = 4.9048695e12  # m^3/s^2
G_MOON = 1.622         # m/s^2 surface gravity (approx)
RHO0 = 1.225          # kg/m3 sea level
H_SCALE = 8500.0      # m approximate scale height (troposphere/lower)
GAMMA = 1.4           # air
R_AIR = 287.05        # J/(kg K)
MU = 1.7894e-5        # dynamic viscosity approx at SL

# --------------------------- Atmosphere & Aero ---------------------------

def atmosphere(h: float, body: str = "earth") -> Dict[str, float]:
    """Simple atmosphere model.
    For 'moon' returns vacuum (rho=0).
    Returns T (K), P (Pa), rho (kg/m3), a (m/s)
    """
    h = max(0.0, float(h))
    if body == "moon":
        return {"T": 250.0, "P": 0.0, "rho": 0.0, "a": 0.0}  # vacuum, no sound speed meaningful
    if h < 11000:
        T = 288.15 - 0.0065 * h
        P = 101325 * (T / 288.15) ** 5.25588
    elif h < 20000:
        T = 216.65
        P = 22632.1 * math.exp(-0.00015769 * (h - 11000))
    elif h < 32000:
        T = 216.65 + 0.001 * (h - 20000)
        P = 5474.89 * (T / 216.65) ** -34.1632
    else:
        # Stratosphere / simple exponential tail
        T = 228.65 + 0.0028 * (h - 32000)
        P = 868.02 * math.exp(-0.000115 * (h - 32000))
    rho = P / (R_AIR * T)
    a = math.sqrt(GAMMA * R_AIR * T)
    return {"T": T, "P": P, "rho": rho, "a": a}


def mach_number(v: float, h: float) -> float:
    atm = atmosphere(h)
    return abs(v) / max(1e-6, atm["a"])


def cd_mach(mach: float) -> float:
    """Approximate Cd vs Mach for a slender rocket (typical 0.3-0.8 base).
    Includes transonic drag rise.
    """
    if mach < 0.8:
        return 0.45 + 0.05 * mach
    elif mach < 1.2:
        # Transonic bump
        return 0.45 + 0.85 * (mach - 0.8) / 0.4
    elif mach < 2.5:
        return 1.1 - 0.35 * (mach - 1.2) / 1.3
    else:
        # Supersonic decrease
        return 0.75 - 0.12 * min(3.0, (mach - 2.5)) / 3.0


def density(h: float, body: str = "earth") -> float:
    return atmosphere(h, body=body)["rho"]


def get_initial_state_3d(cfg: RocketConfig) -> np.ndarray:
    """Return initial [x,y,z, vx,vy,vz, m] for 3D launch from site."""
    if not cfg.three_d:
        # Fallback 2D-ish in x-z plane or something, but caller should handle
        return np.array([0., 0., 0., 0., 0., 0., 0.])
    r_body = R_MOON if cfg.body == "moon" else R_EARTH
    omega = 0.0 if cfg.body == "moon" else OMEGA_EARTH  # Moon tidally locked, negligible for sim
    lat = np.radians(cfg.launch_lat)
    lon = np.radians(cfg.launch_lon)
    r = r_body + cfg.initial_alt
    x = r * np.cos(lat) * np.cos(lon)
    y = r * np.cos(lat) * np.sin(lon)
    z = r * np.sin(lat)
    # Rotation velocity (east component) - 0 for Moon
    v_rot = omega * (r * np.cos(lat))
    # East unit vector in body-fixed -> ECI approx
    ex = -np.sin(lon)
    ey = np.cos(lon)
    ez = 0.0
    vx = v_rot * ex
    vy = v_rot * ey
    vz = 0.0
    # Add any initial_vel if set (for testing)
    if len(cfg.initial_vel) >= 2:
        # simplistic add to horizontal
        vx += cfg.initial_vel[0]
        vy += cfg.initial_vel[1]
    # Gun launch boost for projectile
    if cfg.gun_velocity > 0:
        az = np.radians(cfg.gun_azimuth)
        # Add gun velocity in horizontal plane (azimuth direction)
        gx = cfg.gun_velocity * np.cos(az)
        gy = cfg.gun_velocity * np.sin(az)
        # Rotate to ECI-ish
        vx += gx * np.cos(lon) - gy * np.sin(lon)  # approx
        vy += gx * np.sin(lon) + gy * np.cos(lon)
    m = cfg.total_initial_mass()
    return np.array([x, y, z, vx, vy, vz, m])


# --------------------------- Config & Presets ---------------------------

@dataclass
class Stage:
    name: str = "s1"
    dry_mass: float = 2000.0      # kg structure + engines after propellant
    prop_mass: float = 18000.0    # kg usable propellant
    thrust_sl: float = 250000.0   # N sea level
    thrust_vac: float = 280000.0  # N vacuum
    isp_sl: float = 260.0         # s
    isp_vac: float = 290.0        # s
    # Optional: fixed mdot overrides Isp calc
    mdot: Optional[float] = None
    # Burn time limit (if positive, used for solid motors etc)
    burn_time: Optional[float] = None
    # New for tea-kettle inspired second stage (electric steam kettle)
    # The stage "ejects itself" (jettisons vessel) while the steam propels the remainder (payload)
    is_kettle: bool = False
    water_mass: float = 0.0          # kg water to be boiled into steam
    heater_power_w: float = 0.0      # electric heater power (W) from battery/vehicle
    steam_ve: float = 450.0          # m/s steam exhaust velocity (low Isp ~45s, but simple)
    kettle_vessel_mass: float = 0.0  # kg dry mass of the "kettle" that ejects/jettisons at end
    kettle_eject_rel_vel: float = 5.0  # m/s relative velocity when ejecting the vessel itself (extra kick to remainder)


@dataclass
class RocketConfig:
    name: str = "generic"
    # Vehicle
    diameter: float = 1.8          # m reference
    cd0: float = 0.5               # base Cd (overridden by mach func)
    # Initial
    initial_mass: float = 0.0      # if 0, computed from stages
    initial_alt: float = 0.0
    initial_vel: Tuple[float, float] = (0.0, 0.0)  # vx, vy m/s
    initial_theta: float = 90.0    # deg from horizontal? 90 = vertical up
    # Guidance (very simple)
    pitch_start_t: float = 12.0    # begin gravity turn / pitch program
    pitch_rate: float = 0.7        # deg/s after pitch start (negative for turn)
    final_pitch: float = 10.0      # target minimum pitch (deg from vertical? Wait: 0=up, 90=flat)
    # NOTE: theta = 90 deg = straight up, 0 deg = horizontal
    # Control gains (for simple proportional follow)
    # Propulsion mode
    mode: str = "rocket"           # "rocket" | "jet"
    # Jet specific
    jet_thrust0: float = 80000.0
    jet_isp: float = 1800.0        # low for airbreathing effective?
    intake_area: float = 0.6
    # Electric / battery-powered hypothetical mode
    # Still requires reaction mass (prop_mass in stages). Battery provides energy for acceleration of that mass.
    # Physics: P_jet = eff * power ; mdot = 2*P_jet / ve**2 ; thrust = mdot * ve
    electric_power_w: float = 0.0
    electric_isp: float = 2000.0   # s  (high for ion/arcjet, lower for resistojet)
    electric_eff: float = 0.55     # wall-plug to jet kinetic efficiency
    battery_energy_j: float = 0.0  # total usable battery energy (Joules)
    # 3D support (fully 3D Cartesian ECI trajectory + gravity)
    three_d: bool = False
    launch_lat: float = 0.0   # degrees
    launch_lon: float = 0.0
    launch_azimuth: float = 90.0  # 0=north, 90=east
    body: str = "earth"  # "earth" or "moon" for gravity/atmosphere
    # Gun launch for projectile
    gun_velocity: float = 0.0  # initial muzzle velocity m/s (for projectile launch)
    gun_azimuth: float = 90.0  # deg for direction of gun launch
    # Environment / sim
    use_variable_gravity: bool = True
    use_pressure_thrust: bool = True
    # Particles
    exhaust_v_frac: float = 0.92   # fraction of ve for particle initial speed
    # Stages
    stages: List[Stage] = field(default_factory=list)

    def __post_init__(self):
        if not self.stages:
            # default single stage sounding-ish
            self.stages = [Stage()]

    def total_initial_mass(self) -> float:
        if self.initial_mass > 0:
            return self.initial_mass
        m = 0.0
        for s in self.stages:
            if s.is_kettle:
                m += s.dry_mass + s.water_mass + s.kettle_vessel_mass
            else:
                m += s.dry_mass + s.prop_mass
        return m

    def reference_area(self) -> float:
        return math.pi * (self.diameter / 2.0) ** 2


PRESETS: Dict[str, RocketConfig] = {}


def _make_presets():
    global PRESETS
    # Sounding rocket (small, fast apogee ~80-120 km). Stay near-vertical.
    sounding = RocketConfig(
        name="sounding",
        diameter=0.32,
        cd0=0.38,
        pitch_start_t=8.0,
        pitch_rate=0.55,
        final_pitch=55.0,
        mode="rocket",
        stages=[Stage(
            name="s1",
            dry_mass=85.0,
            prop_mass=420.0,
            thrust_sl=18000,
            thrust_vac=19500,
            isp_sl=235,
            isp_vac=252,
        )]
    )
    PRESETS["sounding"] = sounding

    # Falcon 9-like first stage booster (approx for RTLS-ish profile)
    f9 = RocketConfig(
        name="falcon9-booster",
        diameter=3.66,
        cd0=0.42,
        pitch_start_t=15.0,
        pitch_rate=0.65,
        final_pitch=5.0,
        mode="rocket",
        stages=[
            Stage(
                name="booster",
                dry_mass=25600.0,
                prop_mass=395700.0,
                thrust_sl=7600000.0,   # ~9 Merlin 1D SL
                thrust_vac=8220000.0,
                isp_sl=282,
                isp_vac=311,
            ),
            # Upper stage stub (quick separation sim)
            Stage(
                name="upper",
                dry_mass=4500.0,
                prop_mass=95000.0,
                thrust_sl=950000.0,
                thrust_vac=981000.0,
                isp_sl=320,
                isp_vac=348,
            ),
        ],
    )
    PRESETS["falcon9-booster"] = f9

    # Small jet (fighter afterburner takeoff + climb example)
    jet = RocketConfig(
        name="fighter-jet",
        diameter=1.4,
        cd0=0.28,
        initial_theta=0.0,  # start more level for runway sim, but we do vertical-ish launch pad
        pitch_start_t=3.0,
        pitch_rate=-1.5,  # negative to nose up? adjust
        final_pitch=35.0,
        mode="jet",
        jet_thrust0=125000.0,
        jet_isp=1400.0,
        intake_area=0.9,
        stages=[Stage(
            name="jet",
            dry_mass=9200.0,
            prop_mass=4200.0,
            thrust_sl=125000.0,
            thrust_vac=125000.0,
            isp_sl=1400,
            isp_vac=1400,
            mdot=None,
        )]
    )
    PRESETS["fighter-jet"] = jet

    # Minimal orbital attempt (needs ~7.8 km/s, this is demo only)
    heavy = RocketConfig(
        name="heavy-demo",
        diameter=5.0,
        cd0=0.55,
        pitch_start_t=20.0,
        pitch_rate=0.55,
        final_pitch=0.0,
        mode="rocket",
        stages=[
            Stage(name="core1", dry_mass=22000, prop_mass=400000, thrust_sl=8200000, thrust_vac=9000000, isp_sl=285, isp_vac=312),
            Stage(name="core2", dry_mass=18000, prop_mass=380000, thrust_sl=8200000, thrust_vac=9000000, isp_sl=285, isp_vac=312),
            Stage(name="upper", dry_mass=5500, prop_mass=105000, thrust_sl=1100000, thrust_vac=1200000, isp_sl=330, isp_vac=360),
        ]
    )
    PRESETS["heavy-demo"] = heavy

    # Starship 3 (SpaceX fully-reusable methalox vehicle, ~2026 config)
    # Two-stage: Super Heavy booster + Starship upper stage.
    # Large diameter, high thrust, realistic Isp for Raptor 3 class engines.
    # Note: 2D sim, no circularization burn, so ends in high suborbital arc.
    # Use --duration 600+ for full profile. Expect ~7+ km/s at SECO before coast.
    starship = RocketConfig(
        name="starship3",
        diameter=9.0,
        cd0=0.42,
        pitch_start_t=12.0,
        pitch_rate=0.35,
        final_pitch=0.0,
        mode="rocket",
        three_d=True,
        launch_lat=26.0,
        launch_lon=0.0,
        launch_azimuth=90.0,
        stages=[
            Stage(
                name="super-heavy",
                dry_mass=250000.0,
                prop_mass=3600000.0,
                thrust_sl=75900000.0,   # ~76 MN total (33 Raptor 3 class)
                thrust_vac=82000000.0,
                isp_sl=330.0,
                isp_vac=370.0,
            ),
            Stage(
                name="starship",
                dry_mass=130000.0,
                prop_mass=1200000.0,
                thrust_sl=6900000.0,    # 3 sea-level Raptors
                thrust_vac=9000000.0,   # 3 vacuum-optimized Raptors
                isp_sl=350.0,
                isp_vac=380.0,
            ),
        ]
    )
    PRESETS["starship3"] = starship

    # Lunar launch preset (Starship-derived vehicle launching from Moon surface)
    # No atmosphere, low gravity (1.62 m/s²), aim for lunar orbit or escape.
    # Uses 3D sim. Smaller prop load than Earth Starship since delta-v to lunar orbit ~1.7 km/s.
    lunar = RocketConfig(
        name="lunar-launch",
        diameter=9.0,
        cd0=0.3,  # less relevant, no atm
        pitch_start_t=5.0,
        pitch_rate=0.8,
        final_pitch=10.0,
        mode="rocket",
        three_d=True,
        launch_lat=0.0,  # arbitrary for Moon
        launch_lon=0.0,
        launch_azimuth=90.0,
        body="moon",
        stages=[
            Stage(
                name="lunar-ascent",
                dry_mass=30000.0,  # lighter for lunar
                prop_mass=250000.0,
                thrust_sl=5000000.0,  # strong thrust for impressive lunar lift
                thrust_vac=5500000.0,
                isp_sl=320.0,
                isp_vac=350.0,
            ),
        ]
    )
    PRESETS["lunar-launch"] = lunar

    # New: Gun-launched projectile with tea-kettle second stage (electric steam)
    # First stage: chemical rocket
    # Second stage: electric tea kettle - ejects steam for propulsion, then ejects the vessel itself (kettle) while propelling the payload remainder
    # "English electric tea kettle" inspiration: electric heating boils water -> high pressure steam ejected from nozzle for thrust; vessel ejects at end.
    # Use gun_velocity for initial projectile launch velocity. Body can be earth/moon.
    kettle_proj = RocketConfig(
        name="kettle-projectile",
        diameter=0.3,
        cd0=0.4,
        pitch_start_t=0.1,
        pitch_rate=0.5,
        final_pitch=5.0,
        mode="rocket",
        three_d=True,
        launch_lat=26.0,
        launch_lon=0.0,
        launch_azimuth=90.0,
        gun_velocity=800.0,  # m/s muzzle velocity for projectile launch
        gun_azimuth=45.0,   # elevation-ish for launch angle
        body="earth",
        stages=[
            Stage(
                name="boost-stage",
                dry_mass=20.0,
                prop_mass=80.0,
                thrust_sl=15000.0,
                thrust_vac=16000.0,
                isp_sl=220.0,
                isp_vac=240.0,
            ),
            Stage(
                name="tea-kettle-stage",
                dry_mass=5.0,  # minimal structure
                prop_mass=0.0,
                thrust_sl=0,
                thrust_vac=0,
                isp_sl=0,
                isp_vac=0,
                is_kettle=True,
                water_mass=25.0,          # water to boil
                heater_power_w=50000.0,   # 50 kW electric heater (improvised power source)
                steam_ve=450.0,
                kettle_vessel_mass=15.0,  # the kettle ejects itself
                kettle_eject_rel_vel=20.0, # ejects backward while propelling remainder
            ),
        ]
    )
    PRESETS["kettle-projectile"] = kettle_proj

    # ------------------------------------------------------------
    # Hypothetical battery + electric propulsion presets
    # These illustrate fundamental limits: batteries store *energy*, rockets need *reaction mass*.
    # Even with optimistic future batteries, thrust is low for given power + Isp.
    # Useful for "what if" studies, upper stages, or in-space vehicles.
    # ------------------------------------------------------------

    # Small "battery resistojet" sounding rocket attempt.
    # Water as reaction mass (safe, dense). Battery provides heat/power.
    # Very optimistic future numbers (MW-scale power from compact pack, high discharge).
    # Demonstrates: even then, high Isp = low thrust. Tradeoff is fundamental.
    resistojet = RocketConfig(
        name="battery-resistojet",
        diameter=0.18,
        cd0=0.30,
        pitch_start_t=3.0,
        pitch_rate=1.0,
        final_pitch=75.0,
        mode="electric",
        electric_power_w=2200000.0,     # 2.2 MW electric (extreme hypothetical)
        electric_isp=350.0,             # lower Isp => much higher mdot/thrust for lift
        electric_eff=0.60,
        battery_energy_j=1.8e9,         # 500 kWh (aggressive pack)
        stages=[Stage(
            name="s1",
            dry_mass=11.0,              # light structure + battery + engine
            prop_mass=32.0,             # water reaction mass
            thrust_sl=0, thrust_vac=0,
            isp_sl=0, isp_vac=0,
        )]
    )
    PRESETS["battery-resistojet"] = resistojet

    # Ultra high-Isp battery ion "probe" or upper stage.
    # Extremely low thrust. Can only work in vacuum after being carried aloft.
    # Demonstrates the thrust vs Isp trade-off for fixed power.
    ion_probe = RocketConfig(
        name="battery-ion-probe",
        diameter=0.8,
        cd0=0.25,
        initial_alt=85000.0,  # start high in thin atmosphere / "space" (simulates deployment)
        initial_vel=[1200.0, 300.0],  # some orbital-ish velocity
        pitch_start_t=2.0,
        pitch_rate=0.05,
        final_pitch=2.0,
        mode="electric",
        electric_power_w=45000.0,      # 45 kW
        electric_isp=3200.0,           # gridded ion or Hall thruster
        electric_eff=0.70,
        battery_energy_j=1.44e9,       # 400 kWh
        stages=[Stage(
            name="electric",
            dry_mass=140.0,            # includes heavy battery + power processing + xenon tank
            prop_mass=28.0,            # small amount of reaction mass (xenon-like)
            thrust_sl=0, thrust_vac=0,
        )]
    )
    PRESETS["battery-ion-probe"] = ion_probe

    # Novel idea: "battery railgun pellet launcher"
    # Battery charges capacitor bank; expels small solid/liquid conductor pellets at high velocity.
    # Very high effective exhaust vel (low mdot, high energy per mass).
    # Pulsed operation approximated as average power.
    # Fun physics demo: kinetic energy directly converted to momentum.
    railgun = RocketConfig(
        name="battery-railgun",
        diameter=0.28,
        cd0=0.38,
        pitch_start_t=4.0,
        pitch_rate=0.9,
        final_pitch=55.0,
        mode="electric",
        electric_power_w=6200000.0,    # 6+ MW average (wildly hypothetical pulsed power system)
        electric_isp=520.0,            # lower equiv Isp for thrust (still "fast pellets")
        electric_eff=0.40,
        battery_energy_j=2.8e9,        # ~780 kWh
        stages=[Stage(
            name="pellet-gun",
            dry_mass=18.0,
            prop_mass=35.0,            # pellets / slugs / droplets (reaction mass)
            thrust_sl=0, thrust_vac=0,
        )]
    )
    PRESETS["battery-railgun"] = railgun

    # Railgun + second stage (no chemical fuel stage)
    # Railgun: battery powered, ejects pellets at high velocity (reaction mass, not "fuel")
    # Second stage: ejects itself (the stage/vessel mass) with rel_vel, propelling the remainder (payload)
    # Inspired by railgun for main boost, and tea-kettle for the ejecting pusher stage (ejects "itself" while providing the kick)
    # To fire properly: high electric power, sufficient battery energy for burn time, high ve for pellets, 3D trajectory.
    railgun_kettle = RocketConfig(
        name="railgun-kettle",
        diameter=0.5,
        cd0=0.35,
        pitch_start_t=0.6,
        pitch_rate=1.2,
        final_pitch=12.0,  # modest loft for nicer visible arc
        mode="electric",
        electric_power_w=280000000.0,
        electric_isp=520.0,
        electric_eff=0.58,
        battery_energy_j=220e9,
        three_d=True,
        launch_lat=0.0,
        launch_lon=0.0,
        launch_azimuth=90.0,
        gun_velocity=2500.0,
        stages=[
            Stage(
                name="railgun",
                dry_mass=45.0,
                prop_mass=380.0,       # heavy pellet load for long visible drive + low mass at eject
                thrust_sl=0, thrust_vac=0,
                burn_time=14.0,
            ),
            Stage(
                name="ejector",
                dry_mass=8.0,
                prop_mass=0.0,
                thrust_sl=0, thrust_vac=0,
                burn_time=0.1,
                is_kettle=True,
                water_mass=0.0,               # strictly no fuel / chemical
                heater_power_w=0.0,
                steam_ve=0.0,
                kettle_vessel_mass=48.0,      # ejects itself
                kettle_eject_rel_vel=1400.0,  # very strong kick for clear demo effect
            ),
        ]
    )
    PRESETS["railgun-kettle"] = railgun_kettle


_make_presets()


def get_preset(name: str) -> RocketConfig:
    if name not in PRESETS:
        print(f"Unknown preset '{name}'. Available: {list(PRESETS.keys())}")
        sys.exit(1)
    # Return a deep copy
    cfg = PRESETS[name]
    return RocketConfig(
        name=cfg.name,
        diameter=cfg.diameter,
        cd0=cfg.cd0,
        initial_mass=cfg.initial_mass,
        initial_alt=cfg.initial_alt,
        initial_vel=cfg.initial_vel,
        initial_theta=cfg.initial_theta,
        pitch_start_t=cfg.pitch_start_t,
        pitch_rate=cfg.pitch_rate,
        final_pitch=cfg.final_pitch,
        mode=cfg.mode,
        jet_thrust0=cfg.jet_thrust0,
        jet_isp=cfg.jet_isp,
        intake_area=cfg.intake_area,
        electric_power_w=cfg.electric_power_w,
        electric_isp=cfg.electric_isp,
        electric_eff=cfg.electric_eff,
        battery_energy_j=cfg.battery_energy_j,
        three_d=cfg.three_d,
        launch_lat=cfg.launch_lat,
        launch_lon=cfg.launch_lon,
        launch_azimuth=cfg.launch_azimuth,
        body=cfg.body,
        gun_velocity=cfg.gun_velocity,
        gun_azimuth=cfg.gun_azimuth,
        use_variable_gravity=cfg.use_variable_gravity,
        use_pressure_thrust=cfg.use_pressure_thrust,
        exhaust_v_frac=cfg.exhaust_v_frac,
        stages=[Stage(**asdict(s)) for s in cfg.stages],
    )


# --------------------------- Guidance & Control ---------------------------

def compute_theta(t: float, state: np.ndarray, cfg: Any, stage_idx: int) -> float:
    """Return body pitch angle theta in degrees. 90 = vertical, 0 = horizontal.
    Simple time-based pitch program + rudimentary gravity turn.
    Accepts RocketConfig dataclass or plain dict (from saved history).
    """
    x, h, vx, vy, m = state
    v = math.hypot(vx, vy)

    # Support both dataclass and dict (from npz/json history)
    if isinstance(cfg, dict):
        pitch_start_t = cfg.get("pitch_start_t", 10.0)
        initial_theta = cfg.get("initial_theta", 90.0)
        pitch_rate = cfg.get("pitch_rate", 0.8)
        final_pitch = cfg.get("final_pitch", 15.0)
        mode = cfg.get("mode", "rocket")
    else:
        pitch_start_t = getattr(cfg, "pitch_start_t", 10.0)
        initial_theta = getattr(cfg, "initial_theta", 90.0)
        pitch_rate = getattr(cfg, "pitch_rate", 0.8)
        final_pitch = getattr(cfg, "final_pitch", 15.0)
        mode = getattr(cfg, "mode", "rocket")

    # Start straight up
    if t < pitch_start_t:
        return initial_theta

    # Pitch program: linear ramp toward final_pitch
    elapsed = t - pitch_start_t
    target = max(final_pitch, initial_theta - pitch_rate * elapsed)

    # After significant velocity, bias toward prograde (gravity turn assist)
    if v > 120.0 and h > 3000:
        vel_angle = math.degrees(math.atan2(vy, max(1e-6, vx)))
        # Blend for rockets and electric (electric probes often use it too in long burns)
        if mode in ("rocket", "electric"):
            target = 0.65 * target + 0.35 * vel_angle
    return max(0.0, min(90.0, target))


def compute_thrust_dir_3d(t: float, pos: np.ndarray, vel: np.ndarray, cfg: Any, stage_idx: int) -> np.ndarray:
    """Return unit thrust direction vector in 3D ECI for the current time/state.
    Simple pitch program + gravity turn in the launch plane.
    Supports 3D launch site via lat/lon/azimuth.
    """
    r_body = R_MOON if getattr(cfg, "body", "earth") == "moon" else R_EARTH
    r = np.linalg.norm(pos)
    if r < 100:
        r = r_body
    up = pos / r

    # Get pitch angle (elevation from horizontal? reuse logic: 90=vertical)
    # We will use a 2D-like pitch computation but in 3D plane.
    v_mag = np.linalg.norm(vel)
    # Support dict or dataclass
    if isinstance(cfg, dict):
        pitch_start_t = cfg.get("pitch_start_t", 10.0)
        initial_theta = cfg.get("initial_theta", 90.0)
        pitch_rate = cfg.get("pitch_rate", 0.8)
        final_pitch = cfg.get("final_pitch", 15.0)
        azimuth = cfg.get("launch_azimuth", 90.0)
    else:
        pitch_start_t = getattr(cfg, "pitch_start_t", 10.0)
        initial_theta = getattr(cfg, "initial_theta", 90.0)
        pitch_rate = getattr(cfg, "pitch_rate", 0.8)
        final_pitch = getattr(cfg, "final_pitch", 15.0)
        azimuth = getattr(cfg, "launch_azimuth", 90.0)

    if t < pitch_start_t:
        pitch_elev = initial_theta
    else:
        elapsed = t - pitch_start_t
        pitch_elev = max(final_pitch, initial_theta - pitch_rate * elapsed)

    # Blend with velocity direction for gravity turn
    if v_mag > 120.0 and r > r_body + 3000:
        vel_dir = vel / v_mag
        # Project vel onto local horizontal for better turn
        vel_horiz = vel_dir - np.dot(vel_dir, up) * up
        if np.linalg.norm(vel_horiz) > 0.01:
            vel_horiz /= np.linalg.norm(vel_horiz)
            blend = 0.35
            pitch_elev = 0.65 * pitch_elev + 0.35 * (90.0 - np.degrees(np.arcsin(np.clip(np.dot(vel_dir, up), -1, 1))))
            # use vel_horiz for direction

    # Build the horizontal direction in the launch azimuth plane
    # For simplicity, use a fixed plane based on azimuth.
    # Approximate: assume initial launch plane.
    az = np.radians(azimuth)
    # A simple horizontal basis (this is approximate; for better, use local ENU rotation)
    # For equatorial or general, use cross product for perpendicular.
    # Use a target "downrange" direction.
    # For demo, use a combination that turns "east".
    # A robust way: the desired horizontal is the projection perpendicular to up in the velocity or fixed azimuth.
    # Simple: use [cos az, sin az, 0] rotated, but to make it local:
    # Use the direction orthogonal to up in a chosen plane.
    # For this sim, we'll use a fixed "east" turn for simplicity, adjusted by azimuth.
    horiz = np.array([np.cos(az), np.sin(az), 0.0])
    # Make it local horizontal: subtract up component
    horiz = horiz - np.dot(horiz, up) * up
    hnorm = np.linalg.norm(horiz)
    if hnorm > 1e-6:
        horiz /= hnorm
    else:
        horiz = np.array([0., 1., 0.])

    # pitch_elev: 90 vertical, 0 horizontal
    # direction = sin(pitch) * up + cos(pitch) * horiz
    pitch_rad = np.radians(pitch_elev)
    thrust_dir = np.sin(pitch_rad) * up + np.cos(pitch_rad) * horiz
    n = np.linalg.norm(thrust_dir)
    if n > 1e-9:
        thrust_dir /= n
    else:
        thrust_dir = up
    return thrust_dir


def thrust_and_mdot(t: float, h: float, v: float, theta_deg: float,
                    stage: Stage, cfg: RocketConfig, remaining_water: float = None) -> Tuple[float, float, float]:
    """Return (thrust_N, mdot_kgps, effective_isp).
    For rockets uses pressure correction.
    For jets applies simple lapse + ram drag adjustment (thrust returned is net).
    For kettle (tea kettle second stage): uses electric heater to produce steam thrust.
    """
    body = getattr(cfg, 'body', 'earth')
    atm = atmosphere(h, body=body)
    P_amb = atm["P"]
    P_sl = 101325.0

    if stage.is_kettle:
        # Tea kettle / steam stage: electric heating of water -> steam ejection
        # "ejects itself" (jettisons vessel) while propelling the remainder via steam
        if remaining_water is None or remaining_water <= 0:
            return 0.0, 0.0, stage.steam_ve / G0 if stage.steam_ve > 0 else 0.0
        # Boil rate limited by heater power (latent heat ~2.26 MJ/kg for water)
        latent_heat = 2.26e6  # J/kg
        mdot = min(stage.heater_power_w / latent_heat, remaining_water / 0.1)  # avoid div0
        thrust = mdot * stage.steam_ve
        isp_eff = stage.steam_ve / G0
        return thrust, mdot, isp_eff

    if cfg.mode == "rocket":
        # Linear interpolate between SL and vac using ambient pressure
        frac = max(0.0, min(1.0, (P_sl - P_amb) / P_sl))
        thrust = stage.thrust_sl + frac * (stage.thrust_vac - stage.thrust_sl)
        if not cfg.use_pressure_thrust:
            thrust = stage.thrust_sl   # conservative

        # mdot from Isp or explicit
        if stage.mdot is not None:
            mdot = stage.mdot
            isp_eff = thrust / (mdot * G0) if mdot > 0 else stage.isp_vac
        else:
            isp_eff = stage.isp_sl + frac * (stage.isp_vac - stage.isp_sl)
            mdot = thrust / (isp_eff * G0) if isp_eff > 0 else 0.0

        # Simple nozzle pressure term already approximated in vac/sl thrust diff
        return thrust, mdot, isp_eff

    elif cfg.mode == "electric":
        # Battery electric propulsion. Thrust/power independent of atmosphere (approximately).
        # mdot still consumes the onboard reaction mass (water, xenon simulant, etc.).
        th, md, isp = electric_thrust_and_mdot(cfg)
        return th, md, isp

    else:
        # Jet mode: thrust lapse with altitude + mach effect, simple
        lapse = math.exp(-h / 9000.0)
        mach = mach_number(v, h)
        mach_factor = 1.0 + 0.12 * min(2.0, max(0.0, mach - 0.4))  # ram rise
        thrust_gross = cfg.jet_thrust0 * lapse * mach_factor

        # Intake momentum drag (ram drag)
        rho = atm["rho"]
        v_inf = v
        mdot_air = rho * v_inf * cfg.intake_area * 0.85  # capture eff
        ram_drag = mdot_air * v_inf

        thrust_net = max(0.0, thrust_gross - ram_drag)
        # effective mdot for fuel (much lower than air)
        isp = cfg.jet_isp
        mdot_fuel = thrust_net / (isp * G0) if isp > 0 else 0.0
        return thrust_net, mdot_fuel, isp


def electric_thrust_and_mdot(cfg: RocketConfig) -> Tuple[float, float, float]:
    """Compute thrust from battery electric power.
    Reaction mass flow (mdot) is derived from jet power and desired Isp (ve).
    thrust = 2 * P_jet / ve
    """
    if cfg.electric_power_w <= 0 or cfg.electric_isp <= 0:
        return 0.0, 0.0, cfg.electric_isp
    P_jet = cfg.electric_power_w * max(0.01, min(1.0, cfg.electric_eff))
    ve = cfg.electric_isp * G0
    if ve < 1.0:
        return 0.0, 0.0, cfg.electric_isp
    mdot = (2.0 * P_jet) / (ve * ve)
    thrust = mdot * ve
    return thrust, mdot, cfg.electric_isp


# --------------------------- Dynamics ---------------------------

def rhs(t: float, y: np.ndarray, cfg: RocketConfig, stage: Stage,
        stage_start_mass: float, stage_prop_mass: float) -> np.ndarray:
    """Right-hand side for state.
    2D: [x, h, vx, vy, m]
    3D: [x, y, z, vx, vy, vz, m]
    """
    n = len(y)
    if cfg.three_d or n == 7:
        # 3D ECI
        pos = np.array(y[0:3])
        vel = np.array(y[3:6])
        m = y[6]
        body = getattr(cfg, "body", "earth")
        r_body = R_MOON if body == "moon" else R_EARTH
        gm = GM_MOON if body == "moon" else GM_EARTH
        r = np.linalg.norm(pos)
        h = max(0.0, r - r_body)
        v_mag = np.linalg.norm(vel)

        # Gravity vector
        if cfg.use_variable_gravity and r > 100:
            g_vec = -gm * pos / (r ** 3)
        else:
            g_m = G_MOON if body == "moon" else G0
            g_vec = np.array([0., 0., -g_m])

        # Atmosphere + Aero (use scalar h and v)
        atm = atmosphere(h, body=body)
        rho = atm["rho"]
        a = atm["a"]
        mach = v_mag / max(1e-9, a)
        Cd = cd_mach(mach) * (cfg.cd0 / 0.5)
        A = cfg.reference_area()
        q = 0.5 * rho * v_mag * v_mag
        drag_mag = q * Cd * A
        if v_mag > 1e-6:
            drag_vec = - (drag_mag / max(1.0, m)) * (vel / v_mag)
        else:
            drag_vec = np.zeros(3)

        # Thrust direction (3D)
        thrust_dir = compute_thrust_dir_3d(t, pos, vel, cfg, 0)

        remaining_water = None
        if stage.is_kettle:
            remaining_water = max(0.0, stage.water_mass - (stage_start_mass - m))
        thrust, mdot, _isp = thrust_and_mdot(t, h, v_mag, 0.0, stage, cfg, remaining_water=remaining_water)

        # Limit propellant / water
        if stage.is_kettle:
            water_left = remaining_water
            if water_left <= 0.0:
                thrust = 0.0
                mdot = 0.0
        else:
            prop_left = stage_prop_mass - (stage_start_mass - m)
            if prop_left <= 0.0:
                thrust = 0.0
                mdot = 0.0

        thrust_vec = (thrust / max(1.0, m)) * thrust_dir

        acc = g_vec + drag_vec + thrust_vec
        dm = -mdot
        return np.concatenate([vel, acc, [dm]])

    else:
        # Legacy 2D
        x, h, vx, vy, m = y
        h = max(0.0, h)
        vel = math.hypot(vx, vy)
        theta = math.radians(compute_theta(t, y, cfg, 0))

        if cfg.use_variable_gravity:
            g = GM_EARTH / (R_EARTH + h) ** 2
        else:
            g = G0
        ax_g = 0.0
        ay_g = -g

        atm = atmosphere(h)
        rho = atm["rho"]
        a = atm["a"]
        mach = vel / max(1e-9, a)
        Cd = cd_mach(mach) * (cfg.cd0 / 0.5)
        A = cfg.reference_area()
        q = 0.5 * rho * vel * vel
        drag_mag = q * Cd * A
        if vel > 1e-6:
            ax_d = - (drag_mag / max(1.0, m)) * (vx / vel)
            ay_d = - (drag_mag / max(1.0, m)) * (vy / vel)
        else:
            ax_d = ay_d = 0.0

        remaining_water = None
        if stage.is_kettle:
            remaining_water = max(0.0, stage.water_mass - (stage_start_mass - m))
        thrust, mdot, _isp = thrust_and_mdot(t, h, vel, math.degrees(theta), stage, cfg, remaining_water=remaining_water)

        if stage.is_kettle:
            if remaining_water <= 0.0:
                thrust = 0.0
                mdot = 0.0
        else:
            prop_left = stage_prop_mass - (stage_start_mass - m)
            if prop_left <= 0.0:
                thrust = 0.0
                mdot = 0.0

        ax_t = thrust * math.cos(theta) / max(1.0, m)
        ay_t = thrust * math.sin(theta) / max(1.0, m)

        ax = ax_g + ax_d + ax_t
        ay = ay_g + ay_d + ay_t
        dm = -mdot
        return np.array([vx, vy, ax, ay, dm])


def simulate(cfg: RocketConfig, t_end: float = 300.0, dt_eval: float = 0.05,
             rtol: float = 1e-7, atol: float = 1e-7) -> Dict[str, Any]:
    """Run the full multi-stage simulation.
    2D: state [x, h, vx, vy, m]
    3D: state [x, y, z, vx, vy, vz, m]
    Returns dict with t, state, meta, events, cfg
    """
    print(f"[SIM] Starting '{cfg.name}'  mode={cfg.mode}  3D={cfg.three_d}  duration<= {t_end}s")
    stages = cfg.stages
    total_mass = cfg.total_initial_mass()

    # Build cumulative stage masses
    stage_masses = []
    m = total_mass
    for s in stages:
        stage_masses.append((s, m))
        if s.is_kettle:
            m -= (s.dry_mass + s.water_mass + s.kettle_vessel_mass)
        else:
            m -= (s.dry_mass + s.prop_mass)

    t_all = []
    state_all = []
    meta_all = []   # per point: thrust, mdot, theta, stage, mach, q, ...

    current_t = 0.0
    current_mass = total_mass
    stage_idx = 0
    events = []
    pending_dv_boost = 0.0  # for kettle eject kicks etc.

    # Battery state for electric mode (energy in Joules). Not part of vehicle mass.
    remaining_battery = float(cfg.battery_energy_j)
    power_draw = float(cfg.electric_power_w) if cfg.mode == "electric" else 0.0
    battery_capacity = max(1.0, remaining_battery)

    while stage_idx < len(stages) and current_t < t_end:
        stage, stage_start_mass = stage_masses[stage_idx]
        if stage.is_kettle:
            stage_prop = stage.water_mass
        else:
            stage_prop = stage.prop_mass

        # Initial state for this stage
        if stage_idx == 0:
            if cfg.three_d:
                y0 = get_initial_state_3d(cfg)
                y0[6] = current_mass  # ensure mass
            else:
                y0 = np.array([0.0, cfg.initial_alt,
                               cfg.initial_vel[0], cfg.initial_vel[1],
                               current_mass])
        else:
            # carry over
            prev = state_all[-1]
            if cfg.three_d:
                y0 = np.array(list(prev[0:6]) + [current_mass])
                if pending_dv_boost > 0:
                    v = np.array(y0[3:6])
                    vnorm = np.linalg.norm(v) or 1.0
                    y0[3:6] = v + pending_dv_boost * (v / vnorm)
                    pending_dv_boost = 0.0
            else:
                y0 = np.array(prev[0:4] + [current_mass])
                if pending_dv_boost > 0:
                    vx, vy = y0[2], y0[3]
                    vel = math.hypot(vx, vy) or 1.0
                    y0[2] = vx + pending_dv_boost * vx / vel
                    y0[3] = vy + pending_dv_boost * vy / vel
                    pending_dv_boost = 0.0

        # Time span for this stage
        t_span = (current_t, min(t_end, current_t + (stage.burn_time or 1e9)))

        def prop_left_event(ti, yi):
            # when propellant in this stage exhausted
            m_idx = 6 if len(yi) > 5 else 4
            m_now = yi[m_idx]
            used = stage_start_mass - m_now
            return stage_prop - used
        prop_left_event.terminal = True
        prop_left_event.direction = -1

        def impact_event(ti, yi):
            if cfg.three_d or len(yi) > 5:
                return np.linalg.norm(yi[0:3]) - (R_MOON if getattr(cfg,"body","earth")=="moon" else R_EARTH)
            return yi[1]
        impact_event.terminal = True
        impact_event.direction = -1

        def apogee_event(ti, yi):
            # Robust apogee detection: radial velocity crossing zero (positive to negative)
            # Works for both 2D (vy) and 3D (pos·vel / r)
            if len(yi) > 5:  # 3D ECI
                pos = np.array(yi[0:3])
                vel = np.array(yi[3:6])
                r = np.linalg.norm(pos)
                if r > 1e-6:
                    return np.dot(pos, vel) / r
                return 0.0
            else:
                return yi[3]  # vy in 2D
        apogee_event.terminal = False
        apogee_event.direction = -1

        events_list = [prop_left_event, impact_event, apogee_event]

        # For electric: add battery depletion event (constant power draw assumption)
        if cfg.mode == "electric" and remaining_battery > 1.0 and power_draw > 0:
            def battery_empty_event(ti, yi):
                # Energy used since start of this burn segment
                elapsed = ti - current_t
                return remaining_battery - power_draw * max(0.0, elapsed)
            battery_empty_event.terminal = True
            battery_empty_event.direction = -1
            events_list.append(battery_empty_event)

        sol = solve_ivp(
            lambda t, y: rhs(t, y, cfg, stage, stage_start_mass, stage_prop),
            t_span,
            y0,
            method="RK45",
            rtol=rtol,
            atol=atol,
            dense_output=False,
            events=events_list,
            t_eval=np.arange(t_span[0], t_span[1] + 1e-9, dt_eval) if (t_span[1] - t_span[0]) > dt_eval else None,
        )

        t_seg = sol.t
        y_seg = sol.y.T

        # Record
        batt_start_seg = remaining_battery
        for i in range(len(t_seg)):
            ti = t_seg[i]
            yi = y_seg[i]
            if cfg.three_d or len(yi) == 7:
                xi, yi_, zi, vxi, vyi, vzi, mi = yi
                posi = np.array([xi, yi_, zi])
                veli = np.array([vxi, vyi, vzi])
                hi = np.linalg.norm(posi) - R_EARTH
                vel = np.linalg.norm(veli)
                # For meta, use a representative "theta" or 0
                theta = 0.0
                rem_w = max(0.0, stage.water_mass - (stage_start_mass - mi)) if stage.is_kettle else None
                th, md, isp = thrust_and_mdot(ti, max(0, hi), vel, theta, stage, cfg, remaining_water=rem_w)
                atm = atmosphere(hi)
                qdyn = 0.5 * atm["rho"] * vel * vel
                ma = mach_number(vel, hi)
                state_all.append([xi, yi_, zi, vxi, vyi, vzi, mi])
            else:
                xi, hi, vxi, vyi, mi = yi
                vel = math.hypot(vxi, vyi)
                theta = compute_theta(ti, [xi, hi, vxi, vyi, mi], cfg, stage_idx)
                rem_w = max(0.0, stage.water_mass - (stage_start_mass - mi)) if stage.is_kettle else None
                th, md, isp = thrust_and_mdot(ti, max(0, hi), vel, theta, stage, cfg, remaining_water=rem_w)
                atm = atmosphere(hi)
                qdyn = 0.5 * atm["rho"] * vel * vel
                ma = mach_number(vel, hi)
                state_all.append([xi, hi, vxi, vyi, mi])

            # Approximate remaining battery at this instant (linear within segment)
            if cfg.mode == "electric" and power_draw > 0 and len(t_seg) > 1:
                seg_elapsed = ti - t_seg[0]
                seg_dur = max(1e-9, t_seg[-1] - t_seg[0])
                batt_now = max(0.0, batt_start_seg - power_draw * seg_elapsed)
            else:
                batt_now = batt_start_seg

            t_all.append(ti)
            meta_all.append({
                "thrust": th,
                "mdot": md,
                "theta": theta,
                "stage": stage_idx,
                "mach": ma,
                "q": qdyn,
                "isp_eff": isp,
                "rho": atm["rho"],
                "T": atm["T"],
                "battery_j": batt_now,
                "battery_frac": batt_now / battery_capacity if battery_capacity > 0 else 0.0,
            })

        current_t = t_seg[-1]
        current_mass = y_seg[-1, -1] if cfg.three_d or len(y_seg[0]) == 7 else y_seg[-1, 4]

        # For kettle stage (even with water=0), eject the vessel after the segment (ejects itself while propelling remainder)
        if stage.is_kettle and stage.kettle_vessel_mass > 0:
            vessel = stage.kettle_vessel_mass
            current_mass -= vessel
            kick = 0.0
            if vessel > 0 and stage.kettle_eject_rel_vel > 0 and current_mass > 0:
                kick = (vessel / current_mass) * stage.kettle_eject_rel_vel
                pending_dv_boost += kick
            events.append({"t": current_t, "type": "kettle_eject", "stage": stage_idx, "kick_dv": kick})

        # Deplete battery based on actual segment duration (constant power assumption)
        if cfg.mode == "electric" and power_draw > 0:
            seg_duration = max(0.0, current_t - (t_seg[0] if len(t_seg) else current_t))
            used = power_draw * seg_duration
            remaining_battery = max(0.0, remaining_battery - used)

        # Event recording (dedup apogee to avoid spam)
        seen_apogee = False
        if sol.t_events is not None:
            n_base_events = 3  # prop, impact, apogee
            for ev_idx, ev_times in enumerate(sol.t_events):
                for et in ev_times:
                    ev_type = None
                    if ev_idx == 0:
                        ev_type = "burnout"
                    elif ev_idx == 1:
                        ev_type = "impact"
                    elif ev_idx == 2:
                        if not seen_apogee:
                            ev_type = "apogee"
                            seen_apogee = True
                    elif cfg.mode == "electric" and power_draw > 0 and ev_idx >= n_base_events:
                        ev_type = "battery_empty"
                    if ev_type:
                        events.append({"t": et, "type": ev_type, "stage": stage_idx})

        # Stage transition
        stage_idx += 1
        if stage_idx < len(stages):
            prev_stage = stages[stage_idx-1]
            if prev_stage.is_kettle:
                # Eject the vessel (ejects itself) while propelling the remainder via the kick
                vessel = prev_stage.kettle_vessel_mass
                current_mass -= vessel
                kick = 0.0
                if vessel > 0 and prev_stage.kettle_eject_rel_vel > 0 and current_mass > 0:
                    kick = (vessel / current_mass) * prev_stage.kettle_eject_rel_vel
                    pending_dv_boost += kick
                current_mass = max(current_mass, stages[stage_idx].dry_mass + 10)
                events.append({"t": current_t, "type": "kettle_eject", "stage": stage_idx-1, "kick_dv": kick})
            else:
                # Drop previous stage dry mass
                prev_dry = prev_stage.dry_mass
                current_mass -= prev_dry
                current_mass = max(current_mass, stages[stage_idx].dry_mass + 10)
                events.append({"t": current_t, "type": "stage_sep", "stage": stage_idx-1})
            # Small coast before next ignition
            current_t += 1.5

    # Dedup apogee events (they can still accumulate from coast phase)
    final_events = []
    seen_apo = set()
    for e in events:
        if e.get("type") == "apogee":
            key = (e.get("stage"), round(e.get("t", 0), 1))
            if key in seen_apo:
                continue
            seen_apo.add(key)
        final_events.append(e)
    events = final_events

    # --- Coast phase after final burnout (critical for apogee/impact visualization) ---
    if len(state_all) > 0 and current_t < t_end:
        last_state = state_all[-1]
        if cfg.three_d:
            r_last = np.linalg.norm(last_state[:3])
            h_last = r_last - R_EARTH
        else:
            h_last = last_state[1]
        if h_last > 1.0:
            coast_t0 = float(current_t)
            coast_t1 = float(min(t_end, current_t + 180.0))
            if coast_t1 - coast_t0 < 0.2:
                coast_t1 = coast_t0 + 30.0  # guarantee some coast
            y_coast0 = np.array(last_state, dtype=float).copy()

            if cfg.three_d:
                def coast_rhs(ti, yi):
                    pos = yi[:3]
                    vel = yi[3:6]
                    m = yi[6]
                    r = np.linalg.norm(pos)
                    h = max(0.0, r - R_EARTH)
                    v_mag = np.linalg.norm(vel)
                    if cfg.use_variable_gravity:
                        g = GM_EARTH / r ** 2
                        g_vec = -g * pos / r
                    else:
                        g_vec = np.array([0., 0., -G0])
                    atm = atmosphere(h)
                    rho = atm["rho"]
                    a = atm["a"]
                    mach = v_mag / max(1e-9, a)
                    Cd = cd_mach(mach) * (cfg.cd0 / 0.5)
                    A = cfg.reference_area()
                    q = 0.5 * rho * v_mag * v_mag
                    drag_mag = q * Cd * A
                    if v_mag > 1e-6:
                        drag_vec = - (drag_mag / max(1.0, m)) * (vel / v_mag)
                    else:
                        drag_vec = np.zeros(3)
                    acc = g_vec + drag_vec
                    return np.array([vel[0], vel[1], vel[2], acc[0], acc[1], acc[2], 0.0])

                def impact_coast(ti, yi):
                    pos = yi[:3]
                    r = np.linalg.norm(pos)
                    return r - R_EARTH
                impact_coast.terminal = True
                impact_coast.direction = -1

                def apogee_coast(ti, yi):
                    vel = yi[3:6]
                    return vel[2]  # vertical vel component
                apogee_coast.terminal = False
                apogee_coast.direction = -1
            else:
                def coast_rhs(ti, yi):
                    x, h, vx, vy, m = yi
                    h = max(0.0, h)
                    vel = math.hypot(vx, vy)
                    if cfg.use_variable_gravity:
                        g = GM_EARTH / (R_EARTH + h) ** 2
                    else:
                        g = G0
                    ax_g, ay_g = 0.0, -g
                    atm = atmosphere(h)
                    rho = atm["rho"]
                    a = atm["a"]
                    mach = vel / max(1e-9, a)
                    Cd = cd_mach(mach) * (cfg.cd0 / 0.5)
                    A = cfg.reference_area()
                    q = 0.5 * rho * vel * vel
                    drag_mag = q * Cd * A
                    if vel > 1e-6:
                        ax_d = - (drag_mag / max(1.0, m)) * (vx / vel)
                        ay_d = - (drag_mag / max(1.0, m)) * (vy / vel)
                    else:
                        ax_d = ay_d = 0.0
                    return np.array([vx, vy, ax_g + ax_d, ay_g + ay_d, 0.0])

                def impact_coast(ti, yi):
                    return yi[1]
                impact_coast.terminal = True
                impact_coast.direction = -1

                def apogee_coast(ti, yi):
                    return yi[3]
                apogee_coast.terminal = False
                apogee_coast.direction = -1

            sol_c = solve_ivp(
                coast_rhs, (coast_t0, coast_t1), y_coast0,
                method="RK45", rtol=rtol, atol=atol,
                events=[impact_coast, apogee_coast],
            )
            for i in range(len(sol_c.t)):
                ti = sol_c.t[i]
                if cfg.three_d:
                    xi, yi_, zi, vxi, vyi, vzi, mi = sol_c.y[:, i]
                    r = np.linalg.norm([xi, yi_, zi])
                    hi = r - R_EARTH
                    vel = math.hypot(vxi, vyi, vzi)  # approx
                    theta = 0.0
                    atm = atmosphere(hi)
                    qdyn = 0.5 * atm["rho"] * vel * vel
                    ma = mach_number(vel, hi)
                    t_all.append(ti)
                    state_all.append([xi, yi_, zi, vxi, vyi, vzi, mi])
                    meta_all.append({
                        "thrust": 0.0, "mdot": 0.0, "theta": theta,
                        "stage": stage_idx-1, "mach": ma, "q": qdyn,
                        "isp_eff": 0.0, "rho": atm["rho"], "T": atm["T"],
                    })
                else:
                    xi, hi, vxi, vyi, mi = sol_c.y[:, i]
                    vel = math.hypot(vxi, vyi)
                    theta = compute_theta(ti, [xi, hi, vxi, vyi, mi], cfg, stage_idx-1)
                    atm = atmosphere(hi)
                    qdyn = 0.5 * atm["rho"] * vel * vel
                    ma = mach_number(vel, hi)
                    t_all.append(ti)
                    state_all.append([xi, hi, vxi, vyi, mi])
                    meta_all.append({
                        "thrust": 0.0, "mdot": 0.0, "theta": theta,
                        "stage": stage_idx-1, "mach": ma, "q": qdyn,
                        "isp_eff": 0.0, "rho": atm["rho"], "T": atm["T"],
                    })
            current_t = sol_c.t[-1]
            if sol_c.t_events is not None:
                for ev_idx, ev_times in enumerate(sol_c.t_events):
                    for et in ev_times:
                        if ev_idx == 0:
                            events.append({"t": et, "type": "impact", "stage": stage_idx-1})
                        elif ev_idx == 1:
                            events.append({"t": et, "type": "apogee", "stage": stage_idx-1})

    t_all = np.array(t_all)
    state_all = np.array(state_all)
    print(f"[SIM] Completed. t_final={t_all[-1]:.1f}s  stages={stage_idx}  events={len(events)}")

    return {
        "t": t_all,
        "state": state_all,   # 2D: [N,5] or 3D: [N,7]
        "meta": meta_all,
        "events": events,
        "cfg": asdict(cfg),
    }


# --------------------------- Standalone drawing helpers (for parallel workers) ---------------------------


def _draw_rocket_points(x: float, h: float, theta_deg: float, scale: float = 1.0) -> np.ndarray:
    th = math.radians(theta_deg)
    c, s = math.cos(th), math.sin(th)
    L = 18.0 * scale
    W = 3.2 * scale
    pts = np.array([
        [0.0, L * 0.5],
        [-W*0.5, 0.0],
        [-W*0.42, -L * 0.35],
        [-W*0.55, -L * 0.42],
        [-W*0.15, -L * 0.38],
        [ W*0.15, -L * 0.38],
        [ W*0.55, -L * 0.42],
        [ W*0.42, -L * 0.35],
        [ W*0.5, 0.0],
        [0.0, L * 0.5],
    ])
    rot = np.array([[c, -s], [s, c]])
    pts = pts @ rot.T
    pts[:, 0] += x
    pts[:, 1] += h
    return pts


def _render_single_frame(task):
    """Worker function: render one frame to PNG using Agg canvas (no pyplot state).
    Task tuple: (fi, ft, png_path, sampled, particles_snap, cfg_dict, resolution, max_trail)
    sampled: dict of pre-interp arrays for all frames (x,h,vx,vy,m,thrust,mach,q,vel, times)
    particles_snap: tuple (px, ph, alpha) or empty for this frame
    """
    (fi, ft, png_path, sampled, p_snap, cfg_dict, resolution, max_trail) = task
    dpi = 100
    fig_w = resolution[0] / dpi
    fig_h = resolution[1] / dpi

    fig = Figure(figsize=(fig_w, fig_h), dpi=dpi, facecolor="#0a0a0f")
    # Force 2D plot for now (3D data uses projection for x/h); 3D ax has signature differences in text etc.
    ax = fig.add_axes([0.02, 0.08, 0.68, 0.82])
    ax.set_facecolor("#050508")
    ax.set_aspect("equal")

    # telemetry subplots
    ax_t1 = fig.add_axes([0.72, 0.70, 0.26, 0.20], facecolor="#111115")
    ax_t2 = fig.add_axes([0.72, 0.46, 0.26, 0.20], facecolor="#111115")
    ax_t3 = fig.add_axes([0.72, 0.22, 0.26, 0.20], facecolor="#111115")
    ax_t4 = fig.add_axes([0.72, 0.02, 0.26, 0.16], facecolor="#111115")

    for a in [ax_t1, ax_t2, ax_t3, ax_t4]:
        a.tick_params(colors="#aaaaaa", labelsize=7)
        for spine in a.spines.values():
            spine.set_color("#444444")

    # Data
    times = sampled["t"]
    xs = sampled["x"]
    hs = sampled["h"]
    vxs = sampled["vx"]
    vys = sampled["vy"]
    ms = sampled["m"]
    thrusts = sampled["thrust"]
    machs = sampled["mach"]
    qs = sampled["q"]
    vels = sampled["vel"]

    # Scene limits (fixed from precompute)
    max_h = float(sampled.get("max_h", max(hs.max(), 5000.0)))
    max_x = float(sampled.get("max_x", max(abs(xs).max(), 12000.0)))
    ax.set_xlim(-max_x * 0.15, max_x * 1.15)
    ax.set_ylim(-200, max_h * 1.12)
    ax.set_xlabel("Downrange (m)", color="#888888", fontsize=8)
    ax.set_ylabel("Altitude (m)", color="#888888", fontsize=8)
    ax.tick_params(colors="#666666")

    ax.axhspan(-500, 0, color="#1a1a22", zorder=0)
    ax.axhline(0, color="#334455", lw=1.0)

    # Title area (static-ish)
    fig.text(0.02, 0.965, f"ROCKET SIM — {cfg_dict.get('name', 'flight').upper()}",
             color="#e0e0e0", fontsize=11, fontweight="bold", family="monospace")
    fig.text(0.02, 0.935, f"Physics-accurate  •  PARALLEL  •  {int(sampled.get('fps', 30))} fps",
             color="#777777", fontsize=8, family="monospace")

    # Current values
    xi = float(xs[fi]) if fi < len(xs) else float(xs[-1])
    hi = float(hs[fi]) if fi < len(hs) else float(hs[-1])
    vxi = float(vxs[fi]) if fi < len(vxs) else float(vxs[-1])
    vyi = float(vys[fi]) if fi < len(vys) else float(vys[-1])
    mi = float(ms[fi]) if fi < len(ms) else float(ms[-1])
    thi = compute_theta(ft, [xi, hi, vxi, vyi, mi], cfg_dict, 0)
    thrust_i = float(thrusts[fi]) if fi < len(thrusts) else float(thrusts[-1])
    mach_i = float(machs[fi]) if fi < len(machs) else float(machs[-1])
    q_i = float(qs[fi]) if fi < len(qs) else float(qs[-1])
    vel_i = float(vels[fi]) if fi < len(vels) else float(vels[-1])

    # Dynamic rocket visual size (hoisted so particles/flame can use it)
    max_h = float(sampled.get("max_h", max(hs.max(), 5000.0)))
    max_x = float(sampled.get("max_x", max(abs(xs).max(), 12000.0)))
    view_span = max(max_x, max_h, 2000.0)
    rocket_len = max(180.0, view_span * 0.08)  # more prominent projectile icon
    draw_scale = rocket_len / 18.0

    # Trail (last N)
    t0 = max(0, fi - max_trail)
    tx = xs[t0:fi+1]
    thh = hs[t0:fi+1]
    if len(tx) > 2:
        ax.plot(tx, thh, color="#4488ff", alpha=0.45, lw=1.2, zorder=1)

    # Particles for this frame (pre-baked)
    if p_snap and len(p_snap[0]) > 0:
        px, ph, alpha = p_snap
        psize = max(1.2, 2.5 * (draw_scale / 3.0))  # larger for visibility at 4K / wide views
        ax.scatter(px, ph, s=psize, c="#ffaa33", alpha=alpha, linewidths=0, zorder=3)

    # Rocket (draw_scale computed earlier for particles too)
    rpts = _draw_rocket_points(xi, hi, thi, scale=draw_scale)
    rocket = Polygon(rpts, closed=True, facecolor="#cccccc", edgecolor="#222222",
                     linewidth=1.2, zorder=5)
    ax.add_patch(rocket)

    # Flame (scales with rocket icon)
    th = math.radians(thi)
    ex, ey = -math.cos(th), -math.sin(th)
    flame_len = (4.0 + 6.0 * min(1.0, thrust_i / 2e6)) * draw_scale
    flame_pts = np.array([
        [0, 0],
        [ex * flame_len * 0.6 + 1.6*draw_scale, ey * flame_len * 0.6],
        [ex * flame_len * 0.6 - 1.6*draw_scale, ey * flame_len * 0.6],
    ])
    rot = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    flame_pts = flame_pts @ rot.T
    flame_pts[:, 0] += xi
    flame_pts[:, 1] += hi
    flame = Polygon(flame_pts, closed=True, facecolor="#ffaa22", alpha=0.65, zorder=4)
    ax.add_patch(flame)

    # Visual for ejected kettle vessel (second stage) when active: small object kicked backward
    stg_arr = sampled.get("stages", [0])
    if int(stg_arr[min(fi, len(stg_arr)-1)]) >= 1 and draw_scale > 0:
        # place it behind the rocket along body axis, with growing separation to dramatize the kick
        th = math.radians(thi)
        ex, ey = -math.cos(th), -math.sin(th)
        base_sep = 6.0 * rocket_len
        time_since = max(0.0, ft - 12.5)
        kick_offset = base_sep + time_since * 180.0 * (draw_scale / 12.0)
        vx, vy = ex * kick_offset, ey * kick_offset
        # distinct darker vessel shape
        w = 0.32 * rocket_len
        vessel_pts = np.array([
            [0, -0.08*rocket_len],
            [-w, 0.08*rocket_len],
            [0, 0.35*rocket_len],
            [w, 0.08*rocket_len],
        ])
        rotv = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
        vessel_pts = vessel_pts @ rotv.T
        vessel_pts[:, 0] += xi + vx
        vessel_pts[:, 1] += hi + vy
        vessel = Polygon(vessel_pts, closed=True, facecolor="#444444", edgecolor="#222222", linewidth=1.0, alpha=0.92, zorder=4)
        ax.add_patch(vessel)
        # separation indicator
        ax.plot([xi, xi + vx * 0.5], [hi, hi + vy * 0.5], color="#777777", lw=0.7, alpha=0.5, zorder=3)

    # On-scene HUD
    ax.text(0.02, 0.98, f"t = {ft:7.2f} s", transform=ax.transAxes,
            color="#ffeb3b", fontsize=11, family="monospace", verticalalignment="top")
    ax.text(0.02, 0.93, f"h = {hi:9.1f} m   v = {vel_i:7.1f} m/s",
            transform=ax.transAxes, color="#a0d8ff", fontsize=9, family="monospace",
            verticalalignment="top")
    ax.text(0.02, 0.88, f"Mach {mach_i:5.2f}   q={q_i/1000:6.2f} kPa   m={mi:8.0f} kg",
            transform=ax.transAxes, color="#a0ffa0", fontsize=9, family="monospace",
            verticalalignment="top")

    # Telemetry subplots - history up to now
    cur = fi + 1
    (l_alt,) = ax_t1.plot(times[:cur], hs[:cur], color="#4fc3f7", lw=0.9)
    ax_t1.set_xlim(0, times[-1])
    ax_t1.set_ylim(0, hs.max() * 1.05)
    ax_t1.set_title("Altitude (m)", color="#cccccc", fontsize=7, pad=1)

    (l_vel,) = ax_t2.plot(times[:cur], vels[:cur], color="#81c784", lw=0.9)
    ax_t2.set_xlim(0, times[-1])
    ax_t2.set_ylim(0, vels.max() * 1.05)
    ax_t2.set_title("Speed (m/s)", color="#cccccc", fontsize=7, pad=1)

    (l_thrust,) = ax_t3.plot(times[:cur], thrusts[:cur], color="#ffb74d", lw=0.9)
    ax_t3.set_xlim(0, times[-1])
    ax_t3.set_ylim(0, max(thrusts.max() * 1.05, 1))
    ax_t3.set_title("Thrust (N)", color="#cccccc", fontsize=7, pad=1)

    (l_mach,) = ax_t4.plot(times[:cur], machs[:cur], color="#ce93d8", lw=0.9)
    ax_t4.set_xlim(0, times[-1])
    ax_t4.set_ylim(0, max(machs.max() * 1.05, 1.5))
    ax_t4.set_title("Mach", color="#cccccc", fontsize=7, pad=1)
    ax_t4.set_xlabel("Time (s)", color="#888888", fontsize=6)

    for aa in [ax_t1, ax_t2, ax_t3, ax_t4]:
        aa.axvline(ft, color="#ffeb3b", lw=0.6, alpha=0.9)

    # Bottom labels
    fig.text(0.71, 0.965, f"{ft:0.2f}s", color="#ffeb3b", fontsize=9, family="monospace")
    stage_now = int(sampled.get("stages", np.zeros(len(times)))[min(fi, len(times)-1)])
    fig.text(0.02, 0.01, f"thrust={thrust_i/1e3:7.1f} kN  stage={stage_now}", color="#888888", fontsize=7, family="monospace")

    # Render to PNG
    canvas = FigureCanvasAgg(fig)
    canvas.print_png(png_path)
    # cleanup
    fig.clf()
    plt.close(fig)
    return png_path


# --------------------------- Video Rendering ---------------------------

def render_video(history: Dict[str, Any], out_path: str, fps: int = 30,
                 resolution: Tuple[int, int] = (1920, 1080),
                 max_trail: int = 420, particle_count: int = 420,
                 particle_lifetime: float = 2.8,
                 workers: int = 0, keep_frames: bool = False) -> str:
    """Render a high-quality video of the flight.

    workers behavior:
    - 0 (default): auto-select parallel workers (up to ~60 on this 88-core machine)
    - 1: force original single-process FFMpegWriter path (classic slow loop, very reliable)
    - N>1: use exactly N worker processes for parallel frame rendering + ffmpeg mux

    The parallel path is much faster for long/high-fps renders.
    GPU particles (CuPy on V100) still used for baking the visual plume.
    Everything is recorded; use --no-video for pure data runs.
    """
    t = history["t"]
    state = history["state"]
    meta = history["meta"]
    cfg_dict = history["cfg"]

    n = len(t)
    if n < 3:
        print("[VIDEO] Not enough data")
        return ""

    # Precompute series (used by both paths)
    # Support 3D by simple cylindrical projection for visualization
    if state.shape[1] == 7:
        r = np.linalg.norm(state[:, :3], axis=1)
        hs = r - R_EARTH
        xs = np.sqrt(state[:, 0]**2 + state[:, 1]**2)
        vels = np.linalg.norm(state[:, 3:6], axis=1)
        ms = state[:, 6]
        vxs = state[:, 3]
        vys = state[:, 4]
    else:
        xs = state[:, 0]
        hs = state[:, 1]
        vxs = state[:, 2]
        vys = state[:, 3]
        ms = state[:, 4]
        vels = np.hypot(vxs, vys)
    times = t
    thrusts = np.array([m.get("thrust", 0.0) for m in meta])
    machs = np.array([m.get("mach", 0.0) for m in meta])
    qs = np.array([m.get("q", 0.0) for m in meta])
    stages_arr = np.array([m.get("stage", 0) for m in meta], dtype=int)

    is_3d_data = (state.shape[1] == 7) if hasattr(state, 'shape') else False
    body = "earth"
    try:
        # cfg may be dict or dataclass
        if isinstance(cfg_dict, dict):
            body = cfg_dict.get("body", "earth")
        else:
            body = getattr(cfg_dict, "body", "earth")
    except Exception:
        body = "earth"
    R_body = R_MOON if body == "moon" else R_EARTH

    if is_3d_data:
        pos = state[:, :3]
        r = np.linalg.norm(pos, axis=1)
        alt = r - R_body
        # Proper downrange (arc length) from launch site for 2D viz projection
        p0 = pos[0]
        r0 = np.linalg.norm(p0)
        dots = np.sum(pos * p0, axis=1)
        cosang = np.clip(dots / (r * r0 + 1e-9), -1.0, 1.0)
        dr = R_body * np.arccos(cosang)
        xs = dr
        hs = alt
        max_h = max(float(hs.max()), 1000.0)
        max_x = max(float(xs.max()), 5000.0)
    else:
        max_h = max(float(hs.max()), 5000.0)
        max_x = max(float(np.abs(xs).max()), 12000.0)

    frame_times = np.linspace(t[0], t[-1], int((t[-1] - t[0]) * fps) + 1)
    n_frames = len(frame_times)

    # Interpolate once for frame-accurate data (used for pre-sampling + old path)
    from scipy.interpolate import interp1d
    n_state = state.shape[1]
    interp_state = [interp1d(times, state[:, k], kind="linear", fill_value="extrapolate") for k in range(n_state)]
    interp_thrust = interp1d(times, thrusts, kind="linear", fill_value="extrapolate")
    interp_mach = interp1d(times, machs, kind="linear", fill_value="extrapolate")
    interp_q = interp1d(times, qs, kind="linear", fill_value="extrapolate")
    interp_vel = interp1d(times, vels, kind="linear", fill_value="extrapolate")

    # Sampled arrays for ALL video frames (used heavily by parallel path)
    sampled = {
        "t": frame_times,
        "thrust": np.array([float(interp_thrust(ft)) for ft in frame_times]),
        "mach": np.array([float(interp_mach(ft)) for ft in frame_times]),
        "q": np.array([float(interp_q(ft)) for ft in frame_times]),
        "vel": np.array([float(interp_vel(ft)) for ft in frame_times]),
        "max_h": max_h,
        "max_x": max_x,
        "fps": fps,
        "is_3d": is_3d_data,
    }
    if is_3d_data:
        sampled["pos"] = np.array([[float(interp_state[k](ft)) for k in range(3)] for ft in frame_times])
        sampled["vel_vec"] = np.array([[float(interp_state[k](ft)) for k in range(3,6)] for ft in frame_times])
        sampled["m"] = np.array([float(interp_state[6](ft)) for ft in frame_times])
        # Use correct local downrange + alt for the 2D projection plot (x starts at 0, h=alt)
        def _dr_at(ft):
            px, py, pz = [float(interp_state[k](ft)) for k in range(3)]
            pr = (px**2 + py**2 + pz**2)**0.5 + 1e-9
            p0 = state[0, :3]
            r0 = (p0**2).sum()**0.5 + 1e-9
            cos_a = max(-1.0, min(1.0, (px*p0[0] + py*p0[1] + pz*p0[2]) / (pr * r0)))
            return R_body * math.acos(cos_a)
        def _alt_at(ft):
            px, py, pz = [float(interp_state[k](ft)) for k in range(3)]
            pr = (px**2 + py**2 + pz**2)**0.5
            return pr - R_body
        sampled["x"] = np.array([_dr_at(ft) for ft in frame_times])
        sampled["h"] = np.array([_alt_at(ft) for ft in frame_times])
        sampled["vx"] = np.zeros(len(frame_times))
        sampled["vy"] = np.zeros(len(frame_times))
        # "vel" already set to full-length interp above; do not stomp with short original array
        # For 3D viz (theta/flame direction in 2D projection), use speed to keep v>0 and sensible bias
        sp = np.array([float(interp_vel(ft)) for ft in frame_times])
        sampled["vx"] = sp
        sampled["vy"] = np.zeros(len(frame_times))
    else:
        sampled["x"] = np.array([float(interp_state[0](ft)) for ft in frame_times])
        sampled["h"] = np.array([float(interp_state[1](ft)) for ft in frame_times])
        sampled["vx"] = np.array([float(interp_state[2](ft)) for ft in frame_times])
        sampled["vy"] = np.array([float(interp_state[3](ft)) for ft in frame_times])
        sampled["m"] = np.array([float(interp_state[4](ft)) for ft in frame_times])
    # stages: nearest neighbor interp
    stage_interp = interp1d(times, stages_arr, kind="nearest", fill_value="extrapolate")
    sampled["stages"] = np.array([int(round(float(stage_interp(ft)))) for ft in frame_times])

    # no override, keep the long arrays from interp above for 3D compat

    print(f"[VIDEO] Rendering to {out_path} @ {fps} fps, {resolution[0]}x{resolution[1]}, n_frames~{n_frames}")

    # Decide path
    auto_workers = 0
    if workers == 0:
        cpu = os.cpu_count() or 8
        # Use most of the cores but leave headroom; 88 core machine loves this
        auto_workers = max(2, min(cpu - 4, 60))
    use_parallel = (workers > 1) or (workers == 0 and auto_workers > 1)
    n_workers = workers if workers > 0 else auto_workers

    # ------------------ PARTICLE PRE-BAKE (sequential, cheap, deterministic) ------------------
    # Run the plume simulation once for every video frame time so parallel workers get static snapshots.
    use_gpu = (GPU_BACKEND == "cupy")
    n_particles = min(particle_count, 1200)
    p_life = particle_lifetime
    particles = XP.zeros((n_particles, 5), dtype=np.float32)  # x,h,vx,vy,age
    p_idx = 0
    last_spawn = -1.0

    def spawn_particles(x, h, vx, vy, theta_deg, thrust, n_spawn=12):
        nonlocal p_idx
        if thrust < 500:
            return
        theta = math.radians(theta_deg)
        ex = -math.cos(theta)
        ey = -math.sin(theta)
        ve = 2200.0
        for _ in range(n_spawn):
            jitter = (XP.random.rand(2) - 0.5) * 0.18
            px = x + ex * 1.8 + jitter[0] * 1.5
            ph = h + ey * 1.8 + jitter[1] * 1.5
            pvx = vx + ex * ve * (0.82 + 0.18 * XP.random.rand())
            pvy = vy + ey * ve * (0.82 + 0.18 * XP.random.rand())
            particles[p_idx, 0] = px
            particles[p_idx, 1] = ph
            particles[p_idx, 2] = pvx
            particles[p_idx, 3] = pvy
            particles[p_idx, 4] = 0.0
            p_idx = (p_idx + 1) % n_particles

    def update_particles(dt):
        g = GM_EARTH / (R_EARTH + 2000)**2 if use_gpu else G0 * 0.98
        particles[:, 4] += dt
        particles[:, 2] *= 0.995
        particles[:, 3] = particles[:, 3] * 0.995 - g * dt
        particles[:, 0] += particles[:, 2] * dt
        particles[:, 1] += particles[:, 3] * dt
        mask = particles[:, 4] < p_life
        particles[~mask, 4] = 999.0

    # Pre-bake snapshots: list of (px, py, pz, alpha) for 3D or (px, ph, alpha) 
    particles_per_frame = []
    dt_frame = 1.0 / fps
    for fi, ft in enumerate(frame_times):
        xi = float(sampled["x"][fi])
        hi = float(sampled["h"][fi])
        vxi = float(sampled["vx"][fi])
        vyi = float(sampled["vy"][fi])
        thi = compute_theta(ft, [xi, hi, vxi, vyi, float(sampled["m"][fi])], cfg_dict, 0)
        thrust_i = float(sampled["thrust"][fi])

        if ft - last_spawn > dt_frame * 0.6:
            n_sp = max(3, particle_count // 28)
            spawn_particles(xi, hi, vxi, vyi, thi, thrust_i, n_sp)
            last_spawn = ft
        update_particles(dt_frame)

        alive = particles[:, 4] < p_life
        if np.any(alive):
            px = XP.asnumpy(particles[alive, 0]) if use_gpu else particles[alive, 0].copy()
            ph = XP.asnumpy(particles[alive, 1]) if use_gpu else particles[alive, 1].copy()
            page = particles[alive, 4] if not use_gpu else XP.asnumpy(particles[alive, 4])
            alpha = np.clip(1.0 - page / p_life, 0.05, 0.85).astype(np.float32)
            particles_per_frame.append((px, ph, alpha))
        else:
            particles_per_frame.append((np.array([]), np.array([]), np.array([])))

    # ------------------ PARALLEL FRAME RENDER + FFMPEG ------------------
    if use_parallel:
        print(f"[VIDEO] Using PARALLEL path with ~{n_workers} workers (of {os.cpu_count() or '?'} cores)")
        frame_dir = tempfile.mkdtemp(prefix="rs_frames_")
        # Tell child workers to stay quiet on GPU banner
        os.environ["ROCKET_SIM_QUIET_GPU"] = "1"
        try:
            tasks = []
            for fi, ft in enumerate(frame_times):
                png = os.path.join(frame_dir, f"frame_{fi:06d}.png")
                p_snap = particles_per_frame[fi]
                tasks.append((fi, ft, png, sampled, p_snap, cfg_dict, resolution, max_trail))

            # Dispatch
            start_t = time.time()
            with ProcessPoolExecutor(max_workers=n_workers) as ex:
                # We can iterate to give progress
                completed = 0
                for _ in ex.map(_render_single_frame, tasks, chunksize=4):
                    completed += 1
                    if completed % max(1, n_frames // 12) == 0 or completed == n_frames:
                        print(f"[VIDEO] rendered {completed}/{n_frames} frames ({time.time()-start_t:.1f}s)")

            # Assemble with ffmpeg (fast, high quality)
            print("[VIDEO] Assembling MP4 with ffmpeg...")
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-loglevel", "warning",
                "-framerate", str(fps),
                "-i", os.path.join(frame_dir, "frame_%06d.png"),
                "-c:v", "hevc_nvenc",
                "-preset", "slow",      # high quality NVENC preset
                "-rc", "constqp",
                "-qp", "0",             # lossless
                "-tune", "hq",          # tune for high quality / low motion content
                "-g", "300",            # long GOP for low movement video (fewer keyframes)
                "-bf", "0",             # disable B-frames (HEVC lossless on this V100 NVENC requires it)
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                out_path
            ]
            subprocess.check_call(ffmpeg_cmd)
            print(f"[VIDEO] Assembled {out_path}")

        finally:
            if not keep_frames:
                try:
                    shutil.rmtree(frame_dir)
                except Exception:
                    pass
            else:
                print(f"[VIDEO] Frames kept in {frame_dir}")
        print(f"[VIDEO] Wrote {out_path}")
        return out_path

    # ------------------ FALLBACK: original direct FFMpegWriter (serial) ------------------
    print("[VIDEO] Using serial FFMpegWriter path (workers=1 or forced)")
    dpi = 100
    fig_w = resolution[0] / dpi
    fig_h = resolution[1] / dpi
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi, facecolor="#0a0a0f")
    ax = fig.add_axes([0.02, 0.08, 0.68, 0.82])
    ax.set_facecolor("#050508")
    ax.set_aspect("equal")

    ax_t1 = fig.add_axes([0.72, 0.70, 0.26, 0.20], facecolor="#111115")
    ax_t2 = fig.add_axes([0.72, 0.46, 0.26, 0.20], facecolor="#111115")
    ax_t3 = fig.add_axes([0.72, 0.22, 0.26, 0.20], facecolor="#111115")
    ax_t4 = fig.add_axes([0.72, 0.02, 0.26, 0.16], facecolor="#111115")
    for a in [ax_t1, ax_t2, ax_t3, ax_t4]:
        a.tick_params(colors="#aaaaaa", labelsize=7)
        for spine in a.spines.values():
            spine.set_color("#444444")

    ax.set_xlim(-max_x * 0.15, max_x * 1.15)
    ax.set_ylim(-200, max_h * 1.12)
    ax.set_xlabel("Downrange (m)", color="#888888", fontsize=8)
    ax.set_ylabel("Altitude (m)", color="#888888", fontsize=8)
    ax.tick_params(colors="#666666")

    ax.axhspan(-500, 0, color="#1a1a22", zorder=0)
    ax.axhline(0, color="#334455", lw=1.0)

    fig.text(0.02, 0.965, f"ROCKET SIM — {cfg_dict.get('name', 'flight').upper()}",
             color="#e0e0e0", fontsize=11, fontweight="bold", family="monospace")
    fig.text(0.02, 0.935, f"Physics-accurate  •  {GPU_BACKEND.upper()} particles  •  {fps} fps",
             color="#777777", fontsize=8, family="monospace")

    (l_alt,) = ax_t1.plot([], [], color="#4fc3f7", lw=0.9)
    ax_t1.set_xlim(0, t[-1])
    ax_t1.set_ylim(0, hs.max() * 1.05)
    ax_t1.set_title("Altitude (m)", color="#cccccc", fontsize=7, pad=1)

    (l_vel,) = ax_t2.plot([], [], color="#81c784", lw=0.9)
    ax_t2.set_xlim(0, t[-1])
    ax_t2.set_ylim(0, vels.max() * 1.05)
    ax_t2.set_title("Speed (m/s)", color="#cccccc", fontsize=7, pad=1)

    (l_thrust,) = ax_t3.plot([], [], color="#ffb74d", lw=0.9)
    ax_t3.set_xlim(0, t[-1])
    ax_t3.set_ylim(0, max(thrusts.max() * 1.05, 1))
    ax_t3.set_title("Thrust (N)", color="#cccccc", fontsize=7, pad=1)

    (l_mach,) = ax_t4.plot([], [], color="#ce93d8", lw=0.9)
    ax_t4.set_xlim(0, t[-1])
    ax_t4.set_ylim(0, max(machs.max() * 1.05, 1.5))
    ax_t4.set_title("Mach", color="#cccccc", fontsize=7, pad=1)
    ax_t4.set_xlabel("Time (s)", color="#888888", fontsize=6)

    time_text = fig.text(0.71, 0.965, "", color="#ffeb3b", fontsize=9, family="monospace")
    stats_text = fig.text(0.02, 0.01, "", color="#888888", fontsize=7, family="monospace")

    # Rebuild particles ring (GPU) for serial path
    particles = XP.zeros((n_particles, 5), dtype=np.float32)
    p_idx = 0
    last_spawn = -1.0

    def spawn_particles(x, h, vx, vy, theta_deg, thrust, n_spawn=12):
        nonlocal p_idx
        if thrust < 500: return
        theta = math.radians(theta_deg)
        ex = -math.cos(theta)
        ey = -math.sin(theta)
        ve = 2200.0
        for _ in range(n_spawn):
            jitter = (XP.random.rand(2) - 0.5) * 0.18
            px = x + ex * 1.8 + jitter[0] * 1.5
            ph = h + ey * 1.8 + jitter[1] * 1.5
            pvx = vx + ex * ve * (0.82 + 0.18 * XP.random.rand())
            pvy = vy + ey * ve * (0.82 + 0.18 * XP.random.rand())
            particles[p_idx, 0] = px
            particles[p_idx, 1] = ph
            particles[p_idx, 2] = pvx
            particles[p_idx, 3] = pvy
            particles[p_idx, 4] = 0.0
            p_idx = (p_idx + 1) % n_particles

    def update_particles(dt):
        g = GM_EARTH / (R_EARTH + 2000)**2 if use_gpu else G0 * 0.98
        particles[:, 4] += dt
        particles[:, 2] *= 0.995
        particles[:, 3] = particles[:, 3] * 0.995 - g * dt
        particles[:, 0] += particles[:, 2] * dt
        particles[:, 1] += particles[:, 3] * dt
        mask = particles[:, 4] < p_life
        particles[~mask, 4] = 999.0

    writer = FFMpegWriter(fps=fps, bitrate=12000, metadata={
        "title": f"RocketSim {cfg_dict.get('name')}",
        "artist": "rocket-science skill",
    })

    with writer.saving(fig, out_path, dpi):
        trail = []
        for fi, ft in enumerate(frame_times):
            xi = float(sampled["x"][fi])
            hi = float(sampled["h"][fi])
            vxi = float(sampled["vx"][fi])
            vyi = float(sampled["vy"][fi])
            mi = float(sampled["m"][fi])
            thi = compute_theta(ft, [xi, hi, vxi, vyi, mi], cfg_dict, 0)
            thrust_i = float(sampled["thrust"][fi])
            mach_i = float(sampled["mach"][fi])
            q_i = float(sampled["q"][fi])

            trail.append((xi, hi))
            if len(trail) > max_trail:
                trail.pop(0)

            ax.clear()
            ax.set_facecolor("#050508")
            ax.axhspan(-500, 0, color="#1a1a22", zorder=0)
            ax.axhline(0, color="#334455", lw=1.0)
            ax.set_xlim(-max_x * 0.15, max_x * 1.15)
            ax.set_ylim(-200, max_h * 1.12)

            if len(trail) > 2:
                tx = [p[0] for p in trail]
                thh = [p[1] for p in trail]
                ax.plot(tx, thh, color="#4488ff", alpha=0.45, lw=1.2, zorder=1)

            # dynamic rocket scale for serial path too
            view_span = max(max_x, max_h, 2000.0)
            rocket_len = max(60.0, view_span * 0.035)
            draw_scale = rocket_len / 18.0

            dtf = 1.0 / fps
            if ft - last_spawn > dtf * 0.6:
                n_sp = max(3, particle_count // 28)
                spawn_particles(xi, hi, vxi, vyi, thi, thrust_i, n_sp)
                last_spawn = ft
            update_particles(dtf)

            alive = particles[:, 4] < p_life
            if np.any(alive):
                px = XP.asnumpy(particles[alive, 0]) if use_gpu else particles[alive, 0]
                ph = XP.asnumpy(particles[alive, 1]) if use_gpu else particles[alive, 1]
                page = particles[alive, 4] if not use_gpu else XP.asnumpy(particles[alive, 4])
                alpha = np.clip(1.0 - page / p_life, 0.05, 0.85)
                psize = max(1.2, 2.5 * (draw_scale / 3.0))
                ax.scatter(px, ph, s=psize, c="#ffaa33", alpha=alpha, linewidths=0, zorder=3)

            rpts = _draw_rocket_points(xi, hi, thi, scale=draw_scale)
            rocket = Polygon(rpts, closed=True, facecolor="#cccccc", edgecolor="#222222",
                             linewidth=1.2, zorder=5)
            ax.add_patch(rocket)

            th = math.radians(thi)
            ex, ey = -math.cos(th), -math.sin(th)
            flame_len = (4.0 + 6.0 * min(1.0, thrust_i / 2e6)) * draw_scale
            flame_pts = np.array([
                [0, 0],
                [ex * flame_len * 0.6 + 1.6*draw_scale, ey * flame_len * 0.6],
                [ex * flame_len * 0.6 - 1.6*draw_scale, ey * flame_len * 0.6],
            ])
            rot = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
            flame_pts = flame_pts @ rot.T
            flame_pts[:, 0] += xi
            flame_pts[:, 1] += hi
            flame = Polygon(flame_pts, closed=True, facecolor="#ffaa22", alpha=0.65, zorder=4)
            ax.add_patch(flame)

            ax.text(0.02, 0.98, f"t = {ft:7.2f} s", transform=ax.transAxes,
                    color="#ffeb3b", fontsize=11, family="monospace", verticalalignment="top")
            ax.text(0.02, 0.93, f"h = {hi:9.1f} m   v = {math.hypot(vxi,vyi):7.1f} m/s",
                    transform=ax.transAxes, color="#a0d8ff", fontsize=9, family="monospace",
                    verticalalignment="top")
            ax.text(0.02, 0.88, f"Mach {mach_i:5.2f}   q={q_i/1000:6.2f} kPa   m={mi:8.0f} kg",
                    transform=ax.transAxes, color="#a0ffa0", fontsize=9, family="monospace",
                    verticalalignment="top")

            cur_idx = min(len(times)-1, int(ft / (times[-1] / max(1, len(times)-1))))
            l_alt.set_data(times[:cur_idx+1], hs[:cur_idx+1])
            l_vel.set_data(times[:cur_idx+1], vels[:cur_idx+1])
            l_thrust.set_data(times[:cur_idx+1], thrusts[:cur_idx+1])
            l_mach.set_data(times[:cur_idx+1], machs[:cur_idx+1])

            for aa in [ax_t1, ax_t2, ax_t3, ax_t4]:
                aa.axvline(ft, color="#ffeb3b", lw=0.6, alpha=0.9)

            time_text.set_text(f"{ft:0.2f}s")
            stats_text.set_text(f"thrust={thrust_i/1e3:7.1f} kN  stage={meta[min(cur_idx, len(meta)-1)]['stage']}")

            writer.grab_frame()

            if fi % 60 == 0:
                print(f"[VIDEO] frame {fi}/{n_frames}  t={ft:.1f}s")

    plt.close(fig)
    print(f"[VIDEO] Wrote {out_path}")
    return out_path


# --------------------------- Data Export ---------------------------

def save_history(history: Dict[str, Any], base_path: str):
    """Save everything to compressed npz + sidecar json."""
    t = history["t"]
    state = history["state"]
    meta = history["meta"]

    # Final dedup of apogee events (prevents spam from multiple crossings)
    evs = []
    seen = set()
    for e in history.get("events", []):
        if isinstance(e, dict) and e.get("type") == "apogee":
            key = (e.get("stage"), round(float(e.get("t", 0)), 1))
            if key in seen:
                continue
            seen.add(key)
        evs.append(e)
    history["events"] = evs

    # Flatten meta
    keys = ["thrust", "mdot", "theta", "stage", "mach", "q", "isp_eff", "rho", "T", "battery_j", "battery_frac"]
    meta_arr = np.zeros((len(meta), len(keys)))
    for i, m in enumerate(meta):
        for j, k in enumerate(keys):
            meta_arr[i, j] = m.get(k, 0.0)

    np.savez_compressed(
        base_path + ".npz",
        t=t,
        state=state,
        meta=meta_arr,
        meta_keys=np.array(keys, dtype="U16"),
        events=np.array([str(e) for e in history["events"]], dtype="U128"),
    )
    with open(base_path + ".json", "w") as f:
        json.dump({
            "cfg": history["cfg"],
            "n_points": len(t),
            "t_final": float(t[-1]) if len(t) else 0.0,
            "events": history["events"],
        }, f, indent=2)
    print(f"[DATA] Saved {base_path}.npz + .json")


# --------------------------- CLI ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Physics-accurate Rocket & Jet Simulator")
    parser.add_argument("--preset", type=str, default="sounding",
                        choices=list(PRESETS.keys()),
                        help="Vehicle preset (earth or lunar via body=moon in cfg)")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to JSON RocketConfig override")
    parser.add_argument("--duration", type=float, default=180.0)
    parser.add_argument("--video", type=str, default=None,
                        help="Output .mp4 path (default: ./rocket_videos/<name>-<ts>.mp4)")
    parser.add_argument("--data", type=str, default=None,
                        help="Base path for .npz telemetry (default next to video)")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--res", type=str, default="1920x1080",
                        help="WxH e.g. 1920x1080 or 1280x720")
    parser.add_argument("--particles", type=int, default=520,
                        help="Max exhaust particles")
    parser.add_argument("--no-video", action="store_true")
    parser.add_argument("--no-gpu", action="store_true", help="Force numpy particles")
    parser.add_argument("--dt", type=float, default=0.04, help="Evaluation dt")
    parser.add_argument("--workers", type=int, default=0,
                        help="0=auto parallel (most of 88 cores), 1=force serial FFMpegWriter (classic), N>1=use N parallel workers")
    parser.add_argument("--keep-frames", action="store_true",
                        help="Keep per-frame PNGs (for debugging/parallel path)")
    args = parser.parse_args()

    global GPU_BACKEND, XP
    if args.no_gpu:
        GPU_BACKEND, XP = "numpy", np
        print("[GPU] Forced numpy mode")

    if args.config:
        with open(args.config) as f:
            cfg_dict = json.load(f)
        cfg = RocketConfig(**cfg_dict)
        if cfg.stages:
            cfg.stages = [Stage(**s) for s in cfg.stages]
    else:
        cfg = get_preset(args.preset)

    # Apply simple overrides from CLI where obvious
    res = tuple(int(x) for x in args.res.lower().split("x"))
    out_dir = os.path.expanduser("~/rocket-sim-runs")
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    name = cfg.name

    if args.video is None and not args.no_video:
        args.video = os.path.join(out_dir, f"{name}-{ts}.mp4")

    history = simulate(cfg, t_end=args.duration, dt_eval=args.dt)

    data_base = args.data or (args.video.rsplit(".", 1)[0] if args.video else
                              os.path.join(out_dir, f"{name}-{ts}"))
    save_history(history, data_base)

    if not args.no_video and args.video:
        render_video(
            history,
            args.video,
            fps=args.fps,
            resolution=res,
            particle_count=args.particles,
            workers=args.workers,
            keep_frames=args.keep_frames,
        )
        print(f"\n[OK] Video: {args.video}")
    else:
        print("[OK] Simulation complete (no video requested)")

    print(f"[OK] Telemetry: {data_base}.npz")
    print("Done.")


if __name__ == "__main__":
    main()
