#!/usr/bin/env python3
"""
Validate an image against N64 hardware-oriented limits.

Kinds:
  texture     — must fit TMEM for a given format (default rgba16)
  background  — FB-style; checks even dims + RDRAM cost estimate (Exp Pak)
  depth       — same dims rules as background; prefer 16-bit greyscale
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow required (pip install pillow)", file=sys.stderr)
    raise SystemExit(2)

# Bytes per texel for TMEM budget math
FORMAT_BPT = {
    "rgba32": 4.0,
    "rgba16": 2.0,
    "ia16": 2.0,
    "ia8": 1.0,
    "i8": 1.0,
    "ia4": 0.5,
    "i4": 0.5,
    "ci8": 1.0,  # TLUT extra not included
    "ci4": 0.5,
}

TMEM = 4096
RDRAM = 8 * 1024 * 1024


def is_pow2(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image", type=Path)
    ap.add_argument(
        "--kind",
        choices=("texture", "background", "depth"),
        default="background",
    )
    ap.add_argument(
        "--format",
        default="rgba16",
        choices=sorted(FORMAT_BPT.keys()),
        help="Texel format for TMEM / size estimates",
    )
    ap.add_argument(
        "--max-w",
        type=int,
        default=None,
        help="Optional max width (e.g. original room width)",
    )
    ap.add_argument(
        "--max-h",
        type=int,
        default=None,
        help="Optional max height",
    )
    ap.add_argument(
        "--require-pow2",
        action="store_true",
        help="Require power-of-two W and H (common for RDP textures)",
    )
    args = ap.parse_args()

    if not args.image.is_file():
        print(f"ERROR: {args.image} not found", file=sys.stderr)
        return 1

    im = Image.open(args.image)
    w, h = im.size
    mode = im.mode
    print(f"file:   {args.image}")
    print(f"size:   {w}×{h}  mode={mode}")
    print(f"kind:   {args.kind}  format={args.format}")

    ok = True
    bpt = FORMAT_BPT[args.format]
    nbytes = int(w * h * bpt)

    if args.max_w and w > args.max_w:
        print(f"FAIL: width {w} > max {args.max_w}")
        ok = False
    if args.max_h and h > args.max_h:
        print(f"FAIL: height {h} > max {args.max_h}")
        ok = False

    if args.kind == "texture" or args.require_pow2:
        if args.require_pow2 or args.kind == "texture":
            # textures: warn if not pow2; fail only with --require-pow2
            if not is_pow2(w) or not is_pow2(h):
                msg = f"W,H not both power-of-two ({w}×{h})"
                if args.require_pow2:
                    print(f"FAIL: {msg}")
                    ok = False
                else:
                    print(f"WARN: {msg} — OK if game uses non-pow2 tiles")

        print(f"TMEM:   payload ~{nbytes} bytes (limit {TMEM})")
        if nbytes > TMEM:
            print("FAIL: exceeds 4 KiB TMEM for a single tile at this format")
            ok = False
        else:
            print(f"TMEM:   OK ({TMEM - nbytes} bytes free in tile budget)")

    if args.kind in ("background", "depth"):
        # 16-bit color + 16-bit depth estimate for backgrounds
        color = w * h * 2
        depth = w * h * 2
        both = color + depth
        print(f"RDRAM:  color16~{color} depth16~{depth} sum~{both} bytes")
        print(f"RDRAM:  {100 * both / RDRAM:.2f}% of 8 MiB (buffers only, not whole game)")
        if both > 2 * 1024 * 1024:
            print("WARN: single room color+depth > 2 MiB — risky under game heap")
        if w % 2 or h % 2:
            print("WARN: odd dimension — many FB paths prefer even sizes")
        if w > 640 or h > 480:
            print("WARN: larger than common VI modes — confirm game FB alloc")
            ok = False

    if (w % 4) or (h % 4):
        print("WARN: not multiple of 4 — check DMA/tile alignment for this game")

    if ok:
        print("RESULT: PASS (within checked hardware-oriented rules)")
        return 0
    print("RESULT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
