#!/bin/bash
# Quick demo launcher for the rocket-science simulator.
# Uses the hardware on this machine (V100 + 88 cores + lots of RAM).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SIM="$SCRIPT_DIR/scripts/rocket_sim.py"

mkdir -p ~/rocket-sim-runs

echo "=== rocket-science demo ==="
echo "Using simulator: $SIM"
echo ""

# 1. Fast sounding rocket (high fps, nice particles) -- auto multithread on 88 cores
echo ">>> Running preset: sounding (60 fps video)"
python "$SIM" --preset sounding --duration 85 --fps 60 --particles 650 \
  --video ~/rocket-sim-runs/sounding-demo.mp4 --workers 0

# 2. Falcon 9 style booster (parallel render)
echo ""
echo ">>> Running preset: falcon9-booster"
python "$SIM" --preset falcon9-booster --duration 210 --fps 30 --particles 720 \
  --res 1920x1080 --video ~/rocket-sim-runs/falcon9-booster.mp4 --workers 40

# 3. Jet example (short)
echo ""
echo ">>> Running preset: fighter-jet"
python "$SIM" --preset fighter-jet --duration 55 --fps 30 --particles 280 \
  --video ~/rocket-sim-runs/fighter-jet.mp4

# 4. Custom config example
echo ""
echo ">>> Running custom config from examples/"
python "$SIM" --config "$SCRIPT_DIR/examples/sounding-rocket.json" \
  --duration 70 --fps 30 --video ~/rocket-sim-runs/sounding-custom.mp4 --workers 0

# 5. Hypothetical battery electric (novel propulsion)
echo ""
echo ">>> Running preset: battery-resistojet (electric mode, water reaction mass)"
python "$SIM" --preset battery-resistojet --duration 50 --fps 24 --particles 220 \
  --res 960x540 --video ~/rocket-sim-runs/battery-resistojet.mp4 --workers 0

echo ""
echo "=== All demos complete ==="
echo "Videos and data in ~/rocket-sim-runs/"
ls -lh ~/rocket-sim-runs/
