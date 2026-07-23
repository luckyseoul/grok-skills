# Stackups & Impedance — Starting Points

Always re-validate with the **fabricator’s impedance calculator** for the final order.
These are common industry starting points for 1.6 mm FR-4 class boards, not guarantees.

## 2-layer (hobby / low speed)

| Layer | Function |
|-------|----------|
| L1 | Signals + power pours |
| L2 | Ground pour (prefer solid) |

- Target: keep short high-speed runs; avoid cross-splits on L2.
- USB FS may work with care; USB HS / fast DDR not recommended on 2L.

## 4-layer (default professional)

| Layer | Function | Notes |
|-------|----------|-------|
| L1 | Signal | Components, critical routes |
| L2 | GND | Continuous reference |
| L3 | PWR | Split rails OK if return vias planned |
| L4 | Signal | Secondary routes |

Core between L2–L3 is usually thick; prepreg L1–L2 thin for tighter coupling to GND.

**Routing rule of thumb:** high-speed on L1 referencing L2; use L4 for low-speed or carefully referenced routes.

## 6-layer (dense / faster)

Example:

| Layer | Function |
|-------|----------|
| L1 | Sig |
| L2 | GND |
| L3 | Sig (high-speed) |
| L4 | PWR |
| L5 | GND |
| L6 | Sig |

Gives two solid references and better isolation.

## Impedance notes

| Goal | Typical structure | Comments |
|------|-------------------|----------|
| 50 Ω single-ended | Microstrip L1 over L2 | Width depends on h, εr, copper |
| 50 Ω coplanar | Trace + GND coplanar + vias | RF boards / SMA launch |
| 90 Ω USB HS diff | Diff pair microstrip | Length match critical |
| 100 Ω Ethernet diff | Diff pair | Magnetics placement rules apply |
| 100 Ω PCIe / HDMI | Diff pair, often inner | Loss and length budgets matter |

**Process:**

1. Choose fab + stackup table (dielectric thicknesses).  
2. Run their calculator for W / gap.  
3. Set KiCad net classes / custom rules to those widths.  
4. Document target ± tolerance in DESIGN_NOTES.md.

## Copper weight

| Weight | Use |
|--------|-----|
| 0.5 oz | Fine pitch / density |
| 1 oz | Default signal + moderate power |
| 2 oz | Power boards (wider min features) |

## Surface finish (quick pick)

| Finish | When |
|--------|------|
| HASL (LF) | Cheap digital, not fine pitch BGA |
| ENIG | Default for fine pitch / gold fingers / reliability |
| ENEPIG | Wirebond / higher reliability |
| OSP | Flat pads, short shelf life |

## Power pour tips

- Multiple vias on high-current pad transitions (via farms).  
- Avoid thermal relief only when current is high—solid spoke or direct connect as needed.  
- Sense lines separate from power path for regulators that need it.
