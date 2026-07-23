---
name: n64-texture-video-mod
description: >
  Hardware-faithful texture, background, and FMV/video modding for Nintendo 64
  games that must run on genuine N64 and FPGA (Analogue 3D) via flashcart.
  Maximizes quality under Expansion Pak / TMEM / decode limits. ROM size may
  grow to the ~252 MiB mapped cart ceiling (not stuck at retail 64 MiB). Pipeline:
  rip → AI upscale → downscale to runtime hardware spec → compare → re-encode
  inject. Use when the user says N64 texture mod, N64 HD textures, N64 FMV
  upgrade, SummerCart64 / Summerdrive / 64drive asset patch, rip and upscale N64
  backgrounds, Resident Evil 2 N64 HD, or runs /n64-texture-video-mod.
metadata:
  short-description: "N64 texture/BG/FMV mods for real hardware (max quality)"
---

# N64 Texture & Video Modding (Hardware / FPGA)

ROM-level asset upgrade skill. **Not** emulator texture packs (GLideN64).
Output must boot on **genuine N64 + Expansion Pak** and **FPGA** (e.g. Analogue 3D)
through a flashcart that can hold the image.

**Project docs override these defaults** when more specific (e.g. `Projects/re2-n64-hd/docs/`).

## Hard defaults (unless user or project overrides)

| Setting | Default |
|---------|---------|
| Quality | **Maximize** under runtime silicon (RDRAM / TMEM / FMV decode) |
| ROM size | Grow as needed up to **~252 MiB** mapped cart domain; **not** capped at 64 MiB |
| Flashcart | Prefer cart with enough SDRAM for the build (**64drive ~256 MiB** for full HD; SC64/ED often 64 MiB only — optional small tier) |
| Memory | **Expansion Pak (8 MiB RDRAM)** assumed and required |
| ROM path | Prefer project `rom/*.z64` after normalize; also home-folder dumps |
| Legal | Work only on dumps the user owns; never redistribute game assets |

Read `references/hardware-limits.md` before proposing dimensions, bit depths, or ROM budgets.
See project `docs/PLATFORM_LIMITS.md` when present.

---

## When invoked — first actions

1. **Locate ROM**
   - Check project `rom/`, then `~/Downloads/*.{n64,z64,v64}`, then ask.
   - Normalize to big-endian `.z64` (byte-swap `.n64` / `.v64`).
2. **Fingerprint**
   - Size, internal name, CRC, region; note headroom to **252 MiB**.
   - State target build tier: `hd` (≤252 MiB) vs optional `sc64` (≤64 MiB).
3. **State the pipeline mode**
   - Textures / pre-rendered backgrounds / FMV — or all three.
4. **Never invent formats**
   - Until reverse-engineered, treat compression and tables as TBD; measure from the dump.

Helper entry points (prefer project tools if present under `Projects/re2-n64-hd/tools/`):

```bash
# Normalize + fingerprint
python3 ~/.grok/skills/n64-texture-video-mod/scripts/rom_normalize.py \
  --in ~/Downloads/GAME.n64 --out rom/game.z64 --info

# Spec check an image before inject
python3 ~/.grok/skills/n64-texture-video-mod/scripts/check_image_spec.py path.png \
  --kind background   # or texture / depth

# Rip→upscale→downscale→compare (batch one asset)
python3 ~/.grok/skills/n64-texture-video-mod/scripts/compare_pipeline.py \
  --original ripped/room_001.png \
  --upscaled upscaled/room_001.png \
  --target-w 448 --target-h 328 \
  --out-dir compare/room_001
```

---

## Canonical pipeline (images / backgrounds)

```
  ROM dump (.n64/.z64)
       │
       ▼
  [1] RIP     extract raw asset → lossless PNG/PPM (original pixels)
       │
       ▼
  [2] AI UPSCALE  2×–4× (Real-ESRGAN / user tool / image_edit) → masters only
       │
       ▼
  [3] DOWNSCALE   Lanczos/area → hardware target W×H + legal RDP format
       │
       ▼
  [4] COMPARE     side-by-side + PSNR/SSIM vs original + vs naive upscale
       │
       ▼
  [5] ENCODE      game-specific compressor / palette / CI4/CI8/RGBA16
       │
       ▼
  [6] INJECT      same slot if size fits; else relocate + patch into expanded ROM (≤252 MiB)
       │
       ▼
  [7] VERIFY      emulator (LLE) then hardware flashcart large enough for the image
```

### Rules for each stage

**[1] RIP**
- Prefer lossless dumps of what the game actually uses (after decompress if known).
- Record: room/asset ID, ROM offset, compressed size, uncompressed W×H, format, depth-mask sibling.
- Keep originals under `assets/ripped/` — never overwrite.

**[2] AI UPSCALE**
- Upscale is for **detail synthesis into a master**, not final in-ROM size.
- Do not inject 2K/4K images. Masters live in `assets/upscaled/`.
- Prefer game-art-aware models; avoid oversharpening UI/text (re-composite text from original when possible).
- For photoreal FMV frames, upscale then treat as encode source only if the **video player** path uses that resolution.

**[3] DOWNSCALE (hardware binding — maximize within runtime limits)**
- Backgrounds (FB / BgCopy): start at original W×H with **max encode quality**; then try controlled W×H bumps if **8 MiB RDRAM** budget allows (measure heap/FB).
- Do **not** leave assets at AI master resolution (2K/4K) for inject — runtime dims only.
- RDP textures (TMEM): fit **4 KiB TMEM** for the format; best source into those tiles.
- Color: match original bit depth unless a proven code path allows upgrade.
- Prefer even dimensions; many N64 paths want multiples of 4 or 8 for DMA.

**[4] COMPARE (mandatory before mass inject)**
- Produce: `original | downscaled_from_AI | (optional) naive_scale` contact sheet.
- Metrics: PSNR, SSIM (and file size after encode).
- Human gate: fewer blockies, stable geometry, no melted faces/UI.
- Script: `scripts/compare_pipeline.py`.

**[5–6] ENCODE / INJECT**
- Round-trip test first: extract → re-encode identical → inject → boot (no visual change).
- Strategy (max quality):
  1. Re-encode at highest quality; **relocate** oversized assets into expanded ROM (≤ **252 MiB** mapped ceiling).
  2. Patch offset/size tables; fix CIC checksums.
  3. Optional `sc64` tier: recompress/select assets to fit ≤64 MiB for SummerCart64/ED.
  4. Watch flashcart SDRAM limits separately from console limits.

**[7] VERIFY**
- Emulator with accurate RDP (Angrylion / Parallel-RDP) for FB/depth games; confirm large-ROM support.
- Hardware: flashcart that can load the image size (64drive for ~256 MiB; SC64 only for ≤64 MiB tier).
- Expansion Pak inserted; test room transitions + at least one full FMV.

---

## Canonical pipeline (video / FMV)

```
  higher-quality source (owned PS1/STR, remaster, cleaned capture)
       │
       ▼
  scale / crop to player frame size (often 320×160 or game-native)
       │
       ▼
  encode with game codec OR documented bitrate/keyframe settings
       │
       ▼
  fit stream into table slot; patch duration/size if required
       │
       ▼
  real-time decode check (no audio desync, no hang)
```

### Video rules

- **Decode budget binds more than cart size** once ROM can grow. Prefer:
  - HQ source, highest bitrate that stays real-time on hardware
  - same player frame size first; resolution bumps only after profiling
  - full frame rate only if the original player supports it
- Keep YUV/color range consistent with the original player.
- Audio: stay within MusyX / game audio RAM budgets; mux as the game expects.
- Expanded FMV region is fine up to mapped cart ceiling; still test decode hitching.
- Until the game’s codec is RE’d: document bitstream headers from dumps; do not invent containers.

`references/video-encoding.md` has starter encode recipes (placeholders per game until RE’d).

---

## Asset class cheat sheet

| Class | Storage path | Limit driver | HD approach |
|-------|--------------|--------------|-------------|
| RDP texture (models/UI) | TMEM tiles | **4 KiB TMEM** | Better source → same tile size; multipage only if game already streams |
| Pre-rendered BG | RDRAM FB via BgCopy/DMA | **8 MiB RDRAM** + game alloc | Max encode quality; W×H bump only if RDRAM allows |
| Depth / Z image | RDRAM | Must match BG W×H | Upscale carefully or regenerate; 16-bit depth semantics |
| FMV | Cart + decode heap | CPU/RSP real-time (ROM can grow) | HQ master → max real-time bitrate; res bump only if profiled |

---

## Project layout (create if missing)

```
<game>-n64-hd/
  rom/                  # owned dump (.z64 preferred; gitignore)
  assets/
    ripped/             # lossless extracts
    upscaled/           # AI masters (large)
    downscaled/         # hardware-target PNGs
    compare/            # contact sheets + metrics JSON
    encoded/            # game-format blobs ready to inject
    fmv/
      source/           # high-quality masters
      encoded/
  patches/
  build/                # final .z64 (hd ≤252 MiB; optional sc64 ≤64 MiB)
  research/             # offsets, tables, notes
  tools/                # game-specific extract/inject
```

## Deliverable checklist

- [ ] Image is `.z64`; primary HD build ≤ **~252 MiB** (mapped domain)
- [ ] Optional small tier ≤ 64 MiB if user wants SC64/ED
- [ ] Boots past IPL / CIC (checksum fixed if code patched)
- [ ] Expansion Pak required/documented
- [ ] Save type works on target flashcart
- [ ] No asset pointer past end of ROM or outside cart map used
- [ ] Spot-check rooms + one FMV on **real hardware**

## Anti-patterns (refuse / correct)

- Shipping AI upscale **without** downscale to runtime hardware dims
- Emulator-only `.htc` / Rice texture packs as the “hardware” solution
- Artificially crushing quality to fit 64 MiB when user allows larger ROM
- Exceeding **252 MiB** without an explicit PI/banking plan and cart support
- Increasing BG resolution without depth-mask + RDRAM budget
- Overwriting `assets/ripped/` originals
- Distributing Capcom/Nintendo assets in the skill or git repo

## Collaboration with other skills

- **imagine**: only for marketing stills / pipeline diagrams — not for inventing game textures when a rip exists (always rip-first).
- **check-work**: after inject tooling changes.
- Game-specific project docs (e.g. `Projects/re2-n64-hd/docs/`) override generic advice when more precise.

## Response style when this skill is active

1. State ROM size target vs **252 MiB** ceiling and flashcart implication.
2. State asset class + **runtime** limit that binds quality (RDRAM / TMEM / decode).
3. Maximize quality under those runtime limits; use cart space liberally within ceiling.
4. Show compare metrics before mass-processing.
5. End with next concrete command the user (or agent) should run.
