# N64 hardware limits (Expansion Pak; max quality)

Assume **Expansion Pak (8 MiB RDRAM)** unless the user says otherwise.

**Policy:** maximize visual/audio quality that still runs on genuine N64.
**ROM size** may grow to the mapped cart ceiling (~252 MiB). Retail 64 MiB is not a hard platform limit.

## Memory map ceilings (modding-relevant)

| Resource | Size | Notes |
|----------|------|--------|
| RDRAM (with Exp Pak) | **8 MiB** | Framebuffers, depth images, heaps, audio, OS — **primary runtime cap** |
| RDRAM (no Exp Pak) | 4 MiB | Many late ports require Exp Pak for hi-res |
| TMEM (RDP texture memory) | **4 KiB (4096 bytes)** | Hard tile budget for textured tris |
| Mapped cart ROM | **~252 MiB** | `0x10000000`–`0x1FBFFFFF` — **primary storage ceiling** for simple layouts |
| PI address space | up to ~4 GiB theoretical | Needs cart/DMA design; not default |
| Retail Game Pak max | 64 MiB | Official manufacturing max; flashcarts can exceed |
| VI output | ~320×240 … 640×480 | Internal FB can differ; VI scales |

## ROM size vs flashcart (playability)

| Cart | Approx max ROM | Use |
|------|----------------|-----|
| SummerCart64 | ~64–78 MiB | Optional small tier only |
| EverDrive (many) | ~64 MiB | Same |
| **64drive** | **~256 MiB** | Full HD builds toward 252 MiB |
| Analogue 3D | via flashcart | Same image as N64 |

Always state which cart can run the emitted image.

## TMEM texture size table (single tile, approximate max)

Load size must be ≤ 4096 bytes (plus format constraints / line alignment).

| Format | Bytes/texel | Max texels in 4 KiB | Example max square |
|--------|-------------|---------------------|--------------------|
| RGBA32 | 4 | 1024 | 32×32 |
| RGBA16 | 2 | 2048 | 64×32 or 32×64 |
| IA16 | 2 | 2048 | 64×32 |
| IA8 / I8 | 1 | 4096 | 64×64 |
| IA4 / I4 | 0.5 | 8192 | 128×64 |
| CI8 (+TLUT) | 1 + palette | ~4096 texels + TLUT | often 64×64 |
| CI4 (+TLUT) | 0.5 + palette | more texels | often 64×64 / 128×64 |

Games often use **smaller** tiles and multi-load. Palette (TLUT) counts against TMEM for CI formats.

## Pre-rendered backgrounds (FB path)

Used by Resident Evil 2 N64 and similar: BG is **not** a single TMEM texture.

- Loaded (often as **width 512** staging) then BgCopy’d into a color buffer of true W×H.
- Depth is a **pre-rendered 16-bit image**, not geometry.
- Measure per-room W×H from the game.

### RDRAM cost (16-bit color + 16-bit depth, one buffer each)

```
bytes ≈ W * H * 2  +  W * H * 2  =  4 * W * H
```

| W×H | Color+depth (1×) | Notes |
|-----|------------------|--------|
| 320×240 | 300 KiB | Light |
| 448×328 | ~574 KiB | RE2-class baseline |
| 512×384 | 768 KiB | Plausible upgrade target |
| 640×480 | 1.2 MiB | Aggressive; profile heap |

Push **encode quality** first (expanded ROM). Push **resolution** only after RDRAM profiling with models/audio live.

## FMV / decode

- No general MPEG silicon; games use **custom software + RSP** codecs.
- Cart space for video can grow with the 252 MiB ceiling.
- Bind remains **real-time decode** on VR4300 + RSP.
- Prefer HQ source + max bitrate at player frame size; res bumps only if profiled.

## DMA / alignment

- Prefer sizes multiple of **8 bytes** for PI DMA friendliness.
- Texture lines often have TMEM line constraints; keep stride consistent with original.
- BG staging at width 512 may be required (RE2) — preserve unless patching BgCopy path.

## Expansion Pak checklist

- [ ] Title requires or benefits from Exp Pak
- [ ] Do not require >8 MiB RDRAM (not available on stock N64)
- [ ] Document “Expansion Pak required” in release notes
