#!/usr/bin/env python3
"""
Downscale an AI-upscaled image to hardware target size and compare to original.

Produces:
  - downscaled PNG (hardware target)
  - side-by-side contact sheet (original | downscaled | optional abs-diff)
  - metrics JSON (PSNR, SSIM if available, dimensions)

Pipeline stage: after AI upscale, before game-format encode/inject.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageEnhance
except ImportError:
    print("ERROR: Pillow required (pip install pillow)", file=sys.stderr)
    raise SystemExit(2)


def psnr(a: Image.Image, b: Image.Image) -> float:
    a = a.convert("RGB")
    b = b.convert("RGB")
    if a.size != b.size:
        raise ValueError("PSNR size mismatch")
    # Flattened RGB bytes (Pillow 10+ friendly)
    try:
        pa = a.tobytes()
        pb = b.tobytes()
    except Exception:
        pa = bytes(a.getdata())  # pragma: no cover
        pb = bytes(b.getdata())
    err = 0.0
    n = len(pa)
    for x, y in zip(pa, pb):
        d = x - y
        err += d * d
    mse = err / n if n else 0.0
    if mse == 0:
        return float("inf")
    return 10 * math.log10((255.0 * 255.0) / mse)


def ssim_simple(a: Image.Image, b: Image.Image) -> float | None:
    """Optional SSIM via scikit-image / numpy; returns None if unavailable."""
    try:
        import numpy as np
        from skimage.metrics import structural_similarity as ssim
    except ImportError:
        return None
    a = a.convert("RGB")
    b = b.convert("RGB")
    aa = np.asarray(a)
    bb = np.asarray(b)
    # channel_axis for recent skimage
    try:
        return float(ssim(aa, bb, channel_axis=2, data_range=255))
    except TypeError:
        return float(ssim(aa, bb, multichannel=True, data_range=255))


def label(im: Image.Image, text: str) -> Image.Image:
    bar_h = 22
    out = Image.new("RGB", (im.width, im.height + bar_h), (20, 20, 20))
    out.paste(im.convert("RGB"), (0, bar_h))
    d = ImageDraw.Draw(out)
    d.text((6, 4), text, fill=(220, 220, 220))
    return out


def abs_diff(a: Image.Image, b: Image.Image, boost: float = 4.0) -> Image.Image:
    a = a.convert("RGB")
    b = b.convert("RGB")
    diff = ImageChops.difference(a, b)
    return ImageEnhance.Brightness(diff).enhance(boost)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original", type=Path, required=True, help="Ripped original PNG")
    ap.add_argument(
        "--upscaled",
        type=Path,
        required=True,
        help="AI-upscaled master (larger than target)",
    )
    ap.add_argument("--target-w", type=int, default=None)
    ap.add_argument("--target-h", type=int, default=None)
    ap.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Directory for downscaled + compare outputs",
    )
    ap.add_argument(
        "--filter",
        choices=("lanczos", "box", "bilinear", "hamming", "bicubic"),
        default="lanczos",
    )
    args = ap.parse_args()

    for p in (args.original, args.upscaled):
        if not p.is_file():
            print(f"ERROR: missing {p}", file=sys.stderr)
            return 1

    orig = Image.open(args.original)
    up = Image.open(args.upscaled)

    tw = args.target_w or orig.size[0]
    th = args.target_h or orig.size[1]

    filt = {
        "lanczos": Image.Resampling.LANCZOS,
        "box": Image.Resampling.BOX,
        "bilinear": Image.Resampling.BILINEAR,
        "hamming": Image.Resampling.HAMMING,
        "bicubic": Image.Resampling.BICUBIC,
    }[args.filter]

    down = up.resize((tw, th), filt)
    # Also produce naive upscale-of-original to same size for fair AI vs classic compare
    # (if original already target size, this is identity)
    naive = orig.resize((tw, th), filt)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    down_path = args.out_dir / "downscaled_from_ai.png"
    naive_path = args.out_dir / "scaled_original.png"
    down.save(down_path)
    naive.save(naive_path)

    # Metrics vs original at target size
    orig_t = orig.resize((tw, th), filt) if orig.size != (tw, th) else orig
    metrics = {
        "target": [tw, th],
        "original_size": list(orig.size),
        "upscaled_size": list(up.size),
        "filter": args.filter,
        "psnr_ai_vs_original": psnr(orig_t, down),
        "psnr_naive_vs_original": psnr(orig_t, naive),
        "ssim_ai_vs_original": ssim_simple(orig_t, down),
        "ssim_naive_vs_original": ssim_simple(orig_t, naive),
    }
    # Note: high PSNR vs original is NOT always desired — AI should improve
    # over blocky original. Prefer visual contact sheet + encode-size metrics.
    metrics["note"] = (
        "PSNR/SSIM vs original measure deviation, not 'better'. "
        "Use contact sheet + in-game look; lower blockiness may reduce PSNR."
    )

    (args.out_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2) + "\n", encoding="utf-8"
    )

    # Contact sheet
    panels = [
        label(orig_t.resize((tw, th)), f"original {tw}x{th}"),
        label(down, "AI→downscale"),
        label(abs_diff(orig_t, down), "abs diff x4"),
    ]
    gap = 8
    sheet_w = sum(p.width for p in panels) + gap * (len(panels) - 1)
    sheet_h = max(p.height for p in panels)
    sheet = Image.new("RGB", (sheet_w, sheet_h), (10, 10, 10))
    x = 0
    for p in panels:
        sheet.paste(p, (x, 0))
        x += p.width + gap
    sheet_path = args.out_dir / "compare_sheet.png"
    sheet.save(sheet_path)

    print(f"downscaled → {down_path}")
    print(f"sheet      → {sheet_path}")
    print(f"metrics    → {args.out_dir / 'metrics.json'}")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
