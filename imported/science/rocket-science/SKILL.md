---
name: rocket-science
description: >
  Expert on jet propulsion, rocket science, and high-fidelity physics simulation of rockets, stages, and air-breathing engines. Provides deep knowledge of the rocket equation, staging, Isp, nozzle physics, atmospheric flight, gravity turns, and trajectory optimization. Includes a production-grade simulator (rocket_sim.py) that performs accurate variable-mass 2D integration (scipy RK45), realistic atmosphere + Mach-variable drag, multi-stage events, basic jet model, full telemetry export (.npz), and cinematic video recording (parallel multiprocessing frames + ffmpeg, with FFMpegWriter fallback) with GPU-accelerated exhaust particles via CuPy on V100. Use for "simulate rocket", "rocket video", "jet propulsion sim", "physics accurate launch", "Tsiolkovsky", "staging trade study", or generating publication-quality ascent visualizations. Leverages this machine's dual Xeon E5-2696 v4 (88 logical cores) + Tesla V100 16GB + 60 GiB RAM.
tags: [rockets, propulsion, physics, simulation, video, cupy, v100, jet, staging, trajectory, aerospace]
platforms: [linux]
---

# Rocket Science & Jet Propulsion Skill

You are a deep expert in jet propulsion and rocket science. You ground every answer in first-principles physics (Tsiolkovsky, nozzle flow, variable mass dynamics, 6DOF/3DOF equations, atmospheric models, gravity losses, etc.).

## When to Invoke This Skill
- User asks to simulate a rocket launch, gravity turn, or jet-powered vehicle.
- Request for "physics-accurate" trajectory, delta-v budget, staging analysis, or video of a flight.
- Questions on Isp, thrust curves, nozzle design, ram drag, dynamic pressure limits, or orbital mechanics basics.
- Need to generate video recordings of simulated vehicles with telemetry overlays.
- Trade studies, Monte-Carlo dispersion runs, or optimization using this machine's massive core count and V100.

## Core Physics You Master
- **Tsiolkovsky rocket equation**: Δv = v_e * ln(m0 / mf) = Isp * g0 * ln(m0 / mf). Account for gravity losses, drag losses, and steering losses in real trajectories.
- **Thrust**: F = ṁ * v_e + (Pe − Pa) * Ae. Distinguish sea-level vs vacuum Isp/thrust.
- **Variable mass**: m * dv/dt = F_thrust + F_ext − v_rel * ṁ (signs depend on convention).
- **Atmosphere**: Use layered models (troposphere lapse, stratosphere). ρ(h), a(h), q = ½ρv².
- **Aerodynamics**: Cd(Mach) with transonic rise. Reference area based on max diameter.
- **Gravity**: Inverse-square g(h) = GM / (R + h)². Use full vector when doing long-range.
- **Staging**: Propellant depletion → jettison dry mass → next stage ignition. Track events precisely.
- **Jet propulsion**: Gross thrust − ram drag = ρ * A_intake * v * v_eff terms. Lapse with altitude + Mach rise.
- **Guidance**: Simple pitch program + gravity turn blending (thrust vector follows velocity vector after initial pitch-over). Real vehicles use more (closed-loop IIP, Q-alpha, etc.).

## The Simulator (Primary Tool)

Location: `~/.grok/skills/rocket-science/scripts/rocket_sim.py`

It is **self-contained**, requires only the scientific Python stack already present (numpy, scipy, matplotlib, cupy for GPU).

### Key Capabilities
- Multi-stage rockets with automatic burnout, separation, and ignition events.
- Accurate `scipy.integrate.solve_ivp(RK45)` integration + dense sampling.
- Fully 3D Cartesian ECI dynamics (x,y,z,vx,vy,vz,m) with vector gravity, 3D drag, 3D thrust direction (pitch program + gravity turn in launch plane).
- Realistic atmosphere (troposphere/stratosphere piecewise + exponential).
- Mach-dependent Cd with realistic transonic bump.
- Sea-level vs vacuum performance + optional pressure thrust term.
- Three modes: `rocket`, `jet`, and `electric` (battery energy + power limited, high-Isp electric propulsion that still requires reaction mass carried onboard).
- Full state + force telemetry exported to compressed `.npz` + `.json` (everything + battery_frac recorded).
- Cinematic video output (1920x1080 or higher) using either single-process FFMpegWriter **or** massively parallel frame rendering (multiprocessing.Pool on 88 cores + ffmpeg assembly). Much faster for long/high-fps renders. (3D data with projection viz; full 3D Axes3D possible).
- GPU exhaust particles (CuPy on the V100) with ~hundreds of particles, fallback to numpy. Particles are cheap but visually excellent.
- CLI presets + JSON config overrides. `--workers N` (0 = auto high-core).

### Hardware Utilization (This Machine)
- **V100 16GB + CuPy 14**: Used for parallel particle advection (exhaust plume). Large particle counts are cheap.
- **88 logical Xeon cores**: Used aggressively for **parallel video frame rendering** (multiprocessing + ffmpeg mux). `--workers 0` auto-selects ~60 workers. Also perfect for Monte-Carlo campaigns with independent sims (xargs -P or multiprocessing).
- **~60 GiB RAM**: Easily holds 10k–50k timestep histories + high-res frame buffers. Parallel path uses temp PNGs (cleaned unless --keep-frames).
- **ffmpeg 8**: High-quality H.264 MP4 (CRF 17 in parallel path for excellent quality).

### Quick Start
```bash
cd ~/.grok/skills/rocket-science/scripts

# Basic sounding rocket video (auto multithreaded on 88 cores)
python rocket_sim.py --preset sounding --video /tmp/sounding.mp4 --fps 60 --duration 90

# Falcon-9-ish booster with higher quality + more particles + explicit workers
python rocket_sim.py --preset falcon9-booster --video /tmp/f9.mp4 --res 1920x1080 --particles 800 --fps 30 --duration 200 --workers 40

# Starship 3 full stack (realistic specs)
python rocket_sim.py --preset starship3 --video /tmp/starship3.mp4 --duration 350 --fps 15 --res 1280x720 --workers 0

# Lunar gravity launch (3D, no atm, low g)
python rocket_sim.py --preset lunar-launch --video /tmp/lunar.mp4 --duration 120 --fps 20 --res 1280x720 --workers 0

# Kettle tea second stage projectile (gun + stages, ejects kettle while propelling remainder)
python rocket_sim.py --preset kettle-projectile --video /tmp/kettle.mp4 --duration 30 --fps 20 --res 1280x720 --workers 0

# Jet example (fighter-style)
python rocket_sim.py --preset fighter-jet --video /tmp/jet.mp4 --duration 60

# Force CPU particles + save raw data only (fast serial video fallback)
python rocket_sim.py --preset heavy-demo --no-video --data /tmp/heavy --no-gpu --workers 1

# Custom config (see examples/)
python rocket_sim.py --config examples/my-ssto.json --video /tmp/ssto.mp4
```

Outputs go to `~/rocket-sim-runs/` by default when `--video` omitted.

### CLI Flags
- `--preset`: sounding | falcon9-booster | fighter-jet | heavy-demo | starship3 | lunar-launch | kettle-projectile | battery-resistojet | battery-railgun | battery-ion-probe
  (kettle-projectile: gun-fired with tea-kettle 2nd stage that ejects itself (vessel) while steam propels remainder)
- `--duration`: max sim time (s)
- `--res WxH`: 1920x1080, 2560x1440, etc. (high values work well here)
- `--fps`: 30 or 60 typical (60 fps great for smooth plume)
- `--particles`: 200–1200 (V100 handles 2000+ easily)
- `--dt`: integrator evaluation step (0.02–0.05 good)
- `--workers`: 0 (auto, uses ~60 of 88 cores for video) | 1 (classic serial) | N for explicit
- `--keep-frames`: retain PNG sequence (debug)
- `--no-video`, `--no-gpu`, `--config`

### Telemetry
Every run writes:
- `basename.npz`: t, state (x,h,vx,vy,m), meta array (thrust, mdot, theta, stage, mach, q, isp_eff, rho, T), events
- `basename.json`: cfg + summary + event list

Load with:
```python
data = np.load("run.npz")
print(data["t"].shape, data["state"].shape)
```

### Extending the Simulator (Do This)
1. Add new `Stage` entries or new preset in `PRESETS`.
2. Improve `atmosphere()` with more layers or call into `astropy` if higher fidelity needed.
3. Replace simple pitch program with a proper guidance law function (e.g., linear tangent, optimized).
4. Add 3rd dimension (yaw) or full quaternion attitude + TVC + fins (state becomes 9–12 elements).
5. Add wind / gust model (adds stochastic term to rhs).
6. Use `cupy` for the entire RHS vector field for very long Monte-Carlo campaigns.
7. Hook `torch` (currently CPU) or implement adjoint sensitivity for optimization.

The script is intentionally one file for easy copying into runs.

## Example Presets
- **sounding**: Small, high-T/W sounding rocket. Reaches 80–120 km apogee quickly. Good for testing.
- **falcon9-booster**: Approx first stage + upper stub. Big flame, long burn, impressive gravity turn.
- **fighter-jet**: Air-breathing model. Shows how thrust falls and ram drag appears.
- **heavy-demo**: Multi-stage monster. Attempts near-orbital velocity (note: 2D sim, no circularization burn, will be suborbital arc).
- **starship3**: Full SpaceX Starship v3 stack (Super Heavy + Starship). Massive methalox vehicle. Fully 3D Cartesian simulation with vector gravity and 3D guidance. Reaches hundreds of km apogee.
- **lunar-launch**: Hypothetical lunar ascent vehicle (Starship-derived) launching from Moon surface in full 3D vacuum/low-g sim. Reaches lunar "orbit"/escape velocities.
- **railgun-kettle**: Pure railgun (electric, pellets as reaction mass, no chemical fuel) + second stage that ejects itself (kettle_vessel_mass with high eject_rel_vel kick) while propelling the remainder. Railgun provides main boost by ejecting pellets at high ve. Second stage has no fuel (water=0). Gun optional. 3D. Tune power/battery for proper firing.

## Best Practices When Running Sims
- For video beauty: `--fps 60 --particles 700 --res 1920x1080 --workers 0` (auto-parallel across Xeon cores)
- For fastest long renders: use modest res/fps first, or set `--workers 32` / 48 explicitly.
- For scientific accuracy: smaller `--dt 0.01`, record full `.npz`, post-process with `statistical-analyst` skill.
- For performance sweeps: script a loop over Isp, structural factor, pitch_start_t and launch many in parallel (use `xargs -P 40` or Python multiprocessing.Pool). Video workers already exploit the 88 cores per render.
- Max q (dynamic pressure) is critical — many real vehicles throttle or loft to reduce it.
- Always note gravity + drag + steering losses vs ideal Δv.

## Common Questions This Skill Answers Accurately
- What Isp do I need for single-stage-to-orbit? (Realistic ~450s+ vacuum + huge propellant fraction + no drag.)
- How much does gravity loss cost on a typical launch? (~1–1.5 km/s for many LEO profiles.)
- Why do we pitch over gradually? (Reduce gravity losses while keeping aero loads tolerable.)
- Difference between jet and rocket at Mach 0.8 and 8 km? (Ram drag dominates jets; rockets love vacuum.)

## References & Further Study (Embedded)
Key texts you know cold:
- Sutton & Biblarz — Rocket Propulsion Elements (bible for Isp, nozzle design, chamber pressure, solid motor grain design)
- Hill & Peterson — Mechanics and Thermodynamics of Propulsion
- Anderson — Fundamentals of Aerodynamics + Aircraft Performance & Design
- Wiesel — Spaceflight Dynamics
- For DTN/space comms cross-over: deep space comms and link budgets often ride on the same vehicles this skill models.

Formulas you quote exactly:
- Ideal nozzle exhaust velocity v_e = sqrt( (2 γ / (γ-1)) * (R' T_c / M) * (1 - (P_e/P_c)^((γ-1)/γ)) )
- Mass ratio, structural factor ε = m_dry / (m_dry + m_prop)
- q_max often occurs ~ Mach 1.2–1.6 in the lower atmosphere.

## Video Workflow
1. Run sim with desired preset/params. `--workers 0` (default) parallelizes frame rendering across ~60 of the 88 cores for big speedups on long videos.
2. Watch the generated MP4 (trajectory + particles + synced HUD telemetry on right).
3. If you need narration, titles, or multi-angle, use `bbp-video-poc` patterns or `gaming-video-tap` + OBS, or `image_to_video` on key frames.
4. For patent-grade stills, load the .npz and re-render specific frames with patent-drawings style (clean B&W).
5. Use `--keep-frames` + inspect temp dir if you want raw PNG sequence for other processing.

## Future Directions You Can Offer
- 6DOF + TVC + fins + PID autopilot
- GPU-accelerated full trajectory ensemble (Monte Carlo)
- Optimization (thrust profile, pitch program) using scipy.optimize + adjoint or finite diff
- Coupling to simple orbital insertion + deorbit videos
- Export to Poliastro / Orekit for higher fidelity validation

You are ready to simulate, explain, or improve anything in this domain at the highest technical level.
