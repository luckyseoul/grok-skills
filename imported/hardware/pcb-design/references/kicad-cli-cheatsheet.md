# kicad-cli Cheatsheet

Verify flags for your installed version:

```bash
kicad-cli version
kicad-cli --help
kicad-cli pcb export --help
kicad-cli sch export --help
```

## ERC / DRC

```bash
kicad-cli sch erc --output erc.rpt --format report my.kicad_sch
kicad-cli pcb drc --output drc.rpt --format report my.kicad_pcb
```

## Schematic exports

```bash
kicad-cli sch export pdf --output sch.pdf my.kicad_sch
kicad-cli sch export bom --output bom.csv my.kicad_sch
# netlist if needed:
kicad-cli sch export netlist --output board.net my.kicad_sch
```

## PCB exports (fab)

```bash
mkdir -p fabrication/gerbers
kicad-cli pcb export gerbers --output fabrication/gerbers/ my.kicad_pcb
kicad-cli pcb export drill --output fabrication/gerbers/ my.kicad_pcb
kicad-cli pcb export pos --format csv --units mm --side both \
  --output fabrication/ my.kicad_pcb
kicad-cli pcb export pdf --output board.pdf my.kicad_pcb
kicad-cli pcb export svg --output board.svg my.kicad_pcb
```

## 3D / STEP (mechanical)

```bash
kicad-cli pcb export step --output board.step my.kicad_pcb
```

## Footprint / symbol library ops

```bash
kicad-cli fp export --help
kicad-cli sym export --help
```

## Jobsets (KiCad 9+)

If available, prefer project jobsets for one-command fab packages—inspect:

```bash
kicad-cli jobset --help 2>/dev/null || true
```

## Version drift

KiCad 8 vs 9 may rename subcommands slightly. Always prefer `--help` over memorized flags.
If CLI is missing, document GUI: **File → Fabrication Outputs** and list exact files produced.
