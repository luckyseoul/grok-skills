# rocket-science

Physics-accurate jet propulsion and rocket simulator with video recording.

## Files
- `SKILL.md` — The skill definition (auto-loaded by Grok)
- `scripts/rocket_sim.py` — The complete simulator (run this directly)
- `examples/` — Sample configs and a batch demo script

## Quick Commands
```bash
# From anywhere
python ~/.grok/skills/rocket-science/scripts/rocket_sim.py --preset sounding --video /tmp/test.mp4 --fps 60 --workers 0

# Or use the batch demo
~/.grok/skills/rocket-science/examples/run_demo.sh
```

Videos + telemetry land in `~/rocket-sim-runs/`.

## Hardware Notes (current machine)
- Dual Intel Xeon E5-2696 v4 (~88 logical cores) — **video frames are now rendered in parallel by default** (`--workers 0` auto-selects up to ~60 workers + ffmpeg mux for big speedups)
- NVIDIA Tesla V100-SXM2 16 GB (CuPy 14 + CUDA 13)
- 60 GiB RAM
- ffmpeg 8 + full matplotlib animation writers

The simulator automatically uses the V100 for particle advection when CuPy is importable. Use `--no-gpu` to force CPU. Use `--workers 1` for classic serial path.

## Physics Fidelity
- Variable mass 2D dynamics (x, altitude, vx, vy, mass)
- `scipy.integrate.solve_ivp` (RK45) with event detection for burnout / impact / apogee
- Layered atmosphere + Mach-dependent Cd
- SL vs vacuum thrust + optional pressure thrust term
- Multi-stage with realistic mass jettison on separation
- Simple but effective gravity turn + pitch program
- Jet mode with altitude lapse + ram drag
- Electric / battery mode: power-limited thrust from battery energy + carried reaction mass. Supports novel concepts (resistojet, railgun pellets, ion) with full telemetry of battery state.

## Output
- High-quality MP4 (H.264) with trajectory, animated exhaust particles, rocket silhouette, and live telemetry panels.
- `.npz` + `.json` containing **everything** for later analysis or replays.

## Extending
Edit `rocket_sim.py` directly (single file, easy to hack). Common extensions:
- More sophisticated guidance (linear tangent, optimized pitch)
- Wind field
- 6DOF + fins + TVC
- Monte-Carlo driver (use the 88 cores — video path already does multiprocessing)
- Export to Poliastro for validation

See `SKILL.md` for deeper usage, theory, and patterns. Use `--workers 1` if you want the classic writer.
