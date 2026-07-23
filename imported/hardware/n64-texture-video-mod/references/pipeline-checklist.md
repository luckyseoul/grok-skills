# Per-asset checklist (rip → AI → downscale → compare → inject)

Copy into `research/` or asset `notes.md` per room/clip.

## Identity

- Game / region / CRC:
- Asset ID / room / FMV id:
- ROM offset / table index:
- Compressed size (bytes):
- Uncompressed W×H / format:
- Sibling depth mask offset (if any):

## Rip

- [ ] Lossless PNG/PPM saved under `assets/ripped/`
- [ ] Original not modified
- [ ] Checksum of raw blob recorded

## AI upscale

- [ ] Master under `assets/upscaled/` (2×–4×)
- [ ] Tool / model / scale factor noted
- [ ] UI/text handled (preserve or re-composite)

## Downscale to spec

- [ ] Target W×H = original (default) or approved bump
- [ ] `check_image_spec.py` PASS for kind
- [ ] Output under `assets/downscaled/`

## Compare

- [ ] `compare_pipeline.py` contact sheet reviewed
- [ ] No melted geometry / critical UI damage
- [ ] Accepted for encode

## Encode / inject

- [ ] Game format encode size ≤ slot **or** relocation within **64 MiB**
- [ ] Pointer/size table patched
- [ ] Depth mask updated if BG changed

## Verify

- [ ] Emulator LLE smoke
- [ ] SummerCart64 + Expansion Pak hardware smoke
