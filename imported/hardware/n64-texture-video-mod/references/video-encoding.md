# N64 FMV / video encoding notes

Game-specific codecs dominate. Treat this file as **policy + research template**, not a universal encoder.

## Goals under SummerCart64 + Expansion Pak

1. Visually cleaner video than retail cart compress.
2. Real-time decode on VR4300 + RSP (no multi-second hitches).
3. Streams fit inside **remaining ROM** after code + backgrounds (64 MiB total).
4. Audio stays in sync with the game’s mux / separate audio table.

## Preferred strategy (v1)

```
owned high-quality source
  → scale/crop to original player frame size
  → optional denoise / deinterlace (match progressive vs interlaced original)
  → encode with reverse-engineered game settings OR bitrate ladder tests
  → inject; measure CPU time / dropped frames on hardware
```

**Quality levers that usually work without a new player**

- Better source (less source blockiness)
- Mild denoise before encode (prevents codec spending bits on noise)
- Higher bitrate **if** the player is size-agnostic and RAM buffers allow
- Fewer recompress generations (don’t cascade YouTube rips)

**Levers that usually need code**

- Higher resolution
- Higher frame rate than the player’s design
- Different colorspace without converter changes

## Research checklist per game

- [ ] Locate FMV table (offset, size, count)
- [ ] Dump 2–3 streams; hex-diff headers
- [ ] Capture decoded frame size (W×H) and fps from emulator hooks or framebuffer
- [ ] Note audio: interleave vs separate bank
- [ ] Measure max stream size and free ROM slack
- [ ] Build a round-trip: dump → unaltered reinsert → boot

## Placeholder encode recipe (generic pre-process only)

Use when preparing a **master** before a game-specific encoder:

```bash
# Example: produce a clean 320x160 progressive master from a higher-res source
# Adjust fps/size to the game after measurement.

ffmpeg -i source_hq.mkv \
  -vf "scale=320:160:flags=lanczos,fps=15,format=yuv420p" \
  -an \
  masters/clip_001_320x160.y4m
```

Do **not** assume 320×160 or 15 fps — measure first (RE2 N64 is in that neighborhood historically).

## Bitrate ladder (when size-flexible)

Test on hardware in order; pick highest that stays real-time and in budget:

1. Original compressed size (quality-only re-encode)
2. +25% size
3. +50% size
4. Stop if room transitions or audio suffer (RDRAM / PI contention)

## What not to do

- Ship H.264/AV1 inside the ROM without a decoder (N64 cannot play it natively)
- Replace FMV with emulator texture-frame packs and call it hardware-ready
- Blow the 64 MiB SummerCart64 cap for one intro video

## Deliverables for each clip

```
assets/fmv/<id>/
  source/           # HQ master (user-owned)
  preprocessed/     # sized/fps-matched lossless or y4m
  encoded/          # game bitstream
  notes.md          # offset, size in/out, fps, W×H, audio
```
