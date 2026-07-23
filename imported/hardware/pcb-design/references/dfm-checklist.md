# PCB DFM / Release Checklist

Use before generating Gerbers or placing a fab order. Mark each item Pass / Fail / N/A.

## Schematic / ERC

- [ ] ERC clean (or written waivers with rationale)
- [ ] All power pins powered; PWR_FLAGs correct
- [ ] No floating CMOS inputs
- [ ] Reset / boot / strapping pins defined
- [ ] Connector pinouts match datasheet **and** cable/pin1 orientation
- [ ] Decoupling present per datasheet (bulk + HF)
- [ ] ESD protection on external connectors where required
- [ ] Test points on each rail + key buses
- [ ] Fuse / TVS / reverse protection if user-power exposed

## Footprints / Library

- [ ] Every footprint matched to datasheet mechanical drawing
- [ ] Pad sizes meet fab min (and assembly paste rules)
- [ ] Courtyards non-overlapping at assembly density
- [ ] Thermal pads + via strategy for QFN/QFP/power packages
- [ ] Fiducials present for SMT (global + local if needed)
- [ ] 3D models for tall/mech-critical parts reviewed

## Board / DRC

- [ ] DRC clean at fab rules (trace/space, annular ring, hole size)
- [ ] Board outline closed; tool radius / edge clearance OK
- [ ] Mounting holes sized + keepout for hardware
- [ ] Copper-to-board-edge ≥ fab minimum
- [ ] Min drill and aspect ratio within fab capability
- [ ] Via-in-pad only if fab process supports (or tented/filled called out)
- [ ] Zone fills poured; no isolated copper islands (or intentional)
- [ ] Silkscreen legible; no silkscreen on pads
- [ ] Assembly polarity marks (diodes, electrolytics, pin1)

## Power & Signal Integrity

- [ ] Power path width for current (IPC-2152 or conservative chart)
- [ ] Return path continuous under high-speed / RF
- [ ] Crystal/oscillator layout tight; load caps correct
- [ ] Diff pairs: gap, length match, ref plane documented
- [ ] Impedance targets stated for controlled-impedance nets
- [ ] ADC/analog: star ground or solid plane strategy documented

## RF-specific (if applicable)

- [ ] 50 Ω (or specified Z) geometry matches stackup calculator
- [ ] Ground vias along coplanar RF paths
- [ ] Matching network placement close to IC / antenna feed
- [ ] Antenna keep-outs free of ground pour / metal as required
- [ ] Shield cans / fence vias if designed

## Fab package

- [ ] Gerbers + drill generated from final revision
- [ ] Layer map documented (which Gerber is which layer)
- [ ] Stackup note: thickness, copper oz, material, finish
- [ ] BOM with MPN + alternates; DNP items marked
- [ ] Pick-and-place / CPL with correct rotation convention for fab
- [ ] README for fab: quantity, color, thickness, impedance, panel notes

## Revision control

- [ ] Version / date on silkscreen or copper
- [ ] Git commit or release tag recorded in DESIGN_NOTES.md
