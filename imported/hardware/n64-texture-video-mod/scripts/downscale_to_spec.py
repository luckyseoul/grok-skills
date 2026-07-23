#!/usr/bin/env python3
"""Downscale an image to exact N64 target dimensions (batch-friendly)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow required (pip install pillow)", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--w", type=int, required=True)
    ap.add_argument("--h", type=int, required=True)
    ap.add_argument(
        "--filter",
        default="lanczos",
        choices=("lanczos", "box", "bilinear", "bicubic", "nearest"),
    )
    ap.add_argument(
        "--mode",
        default=None,
        help="Optional PIL mode convert before save (e.g. RGB, RGBA, P)",
    )
    args = ap.parse_args()

    if not args.input.is_file():
        print(f"ERROR: {args.input} not found", file=sys.stderr)
        return 1

    filt = getattr(Image.Resampling, args.filter.upper())
    im = Image.open(args.input)
    out = im.resize((args.w, args.h), filt)
    if args.mode:
        out = out.convert(args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    out.save(args.output)
    print(f"{args.input} {im.size} → {args.output} {out.size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
