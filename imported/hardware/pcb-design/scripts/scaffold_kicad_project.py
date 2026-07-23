#!/usr/bin/env python3
"""Scaffold a PCB project directory with design notes templates.

Does not require KiCad installed. Creates a working tree the agent and user
can open in KiCad later (user creates .kicad_pro via KiCad if needed).
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

DESIGN_NOTES = """# Design Notes — {name}

**Created:** {date}
**Layers (planned):** {layers}
**Fab target:** (TBD)
**Revision:** A0

## Purpose

(one paragraph)

## Assumptions

- Stackup: {layers}-layer FR-4, 1.6 mm, 1 oz copper (adjust after fab calc)
- Finish: ENIG (default)
- Min trace/space: per fab (e.g. 0.15 / 0.15 mm)

## Block diagram

```
(power) → (MCU / FPGA) → (interfaces)
                ↓
             (connectors / RF)
```

## Power tree

| Rail | Source | Load estimate | Notes |
|------|--------|---------------|-------|
| 3V3  |        |               |       |
| 1V8  |        |               |       |

## Critical nets

| Net | Type | Impedance / rules |
|-----|------|-------------------|
|     |      |                   |

## Open risks

- [ ]

## ERC/DRC log

- ERC: not run
- DRC: not run

## Fab order notes

- Quantity:
- Color / thickness / impedance control:
"""

BOM_MD = """# BOM — {name}

| Ref | Qty | MPN | Description | Footprint | LCSC/DigiKey | DNP |
|-----|-----|-----|-------------|-----------|--------------|-----|
|     |     |     |             |           |              |     |
"""

README = """# {name}

KiCad PCB project scaffolded by `pcb-design` skill.

## Layout

- `DESIGN_NOTES.md` — architecture, stackup, risks
- `BOM.md` — working BOM
- `schematic/` — export PDFs (optional)
- `fabrication/` — Gerbers, drill, CPL, fab zip
- `libraries/` — project-local symbols/footprints

## Create KiCad project files

Open KiCad → New Project → set path to this folder, **or**:

```bash
# If kicad-cli supports project creation on your version:
kicad-cli --help
```

Then save `{name}.kicad_pro`, `{name}.kicad_sch`, `{name}.kicad_pcb` here.

## Pre-fab

```bash
python3 ~/.grok/skills/pcb-design/scripts/dfm_preflight.py DESIGN_NOTES.md
```
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Scaffold PCB project tree")
    ap.add_argument("--name", required=True, help="Project / board name (slug ok)")
    ap.add_argument("--path", required=True, help="Parent or full project path")
    ap.add_argument("--layers", type=int, default=4, help="Planned layer count")
    args = ap.parse_args()

    name = args.name.strip().replace(" ", "-")
    root = Path(args.path).expanduser().resolve()
    if root.name != name and not (root / "DESIGN_NOTES.md").exists():
        # If path is parent, create name subdir
        if not root.exists() or root.is_dir():
            candidate = root / name
            if not root.exists() or not any(root.iterdir()) or root.name != name:
                # Prefer path as project root if user passed .../my-board
                if root.name == name or str(args.path).rstrip("/").endswith(name):
                    pass
                else:
                    root = candidate

    root.mkdir(parents=True, exist_ok=True)
    for sub in ("libraries", "fabrication/gerbers", "schematic", "docs"):
        (root / sub).mkdir(parents=True, exist_ok=True)

    date = dt.date.today().isoformat()
    (root / "DESIGN_NOTES.md").write_text(
        DESIGN_NOTES.format(name=name, date=date, layers=args.layers), encoding="utf-8"
    )
    (root / "BOM.md").write_text(BOM_MD.format(name=name), encoding="utf-8")
    (root / "README.md").write_text(README.format(name=name), encoding="utf-8")
    (root / "fabrication" / ".gitkeep").write_text("", encoding="utf-8")

    print(f"Scaffolded PCB project at: {root}")
    print(f"  layers planned: {args.layers}")
    print("Next: create KiCad project files in this directory, then schematic.")


if __name__ == "__main__":
    main()
