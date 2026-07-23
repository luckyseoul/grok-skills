#!/usr/bin/env python3
"""Normalize N64 ROM byte order to .z64 and print fingerprint."""

from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path


def detect(data: bytes) -> str:
    if len(data) < 4:
        return "unknown"
    m = data[:4]
    if m == b"\x80\x37\x12\x40":
        return "z64"
    if m == b"\x37\x80\x40\x12":
        return "v64"
    if m == b"\x40\x12\x37\x80":
        return "n64"
    return "unknown"


def to_z64(data: bytes, order: str) -> bytes:
    if order == "z64":
        return data
    if order == "v64":
        out = bytearray(len(data))
        for i in range(0, len(data) - 1, 2):
            out[i], out[i + 1] = data[i + 1], data[i]
        if len(data) & 1:
            out[-1] = data[-1]
        return bytes(out)
    if order == "n64":
        out = bytearray(len(data))
        for i in range(0, len(data) - 3, 4):
            out[i : i + 4] = data[i : i + 4][::-1]
        return bytes(out)
    raise ValueError(f"unrecognized ROM order: {order}")


def header(z64: bytes) -> dict:
    name = z64[0x20:0x34].split(b"\x00")[0].decode("ascii", errors="replace").strip()
    return {
        "name": name,
        "crc1": struct.unpack(">I", z64[0x10:0x14])[0],
        "crc2": struct.unpack(">I", z64[0x14:0x18])[0],
        "pc": struct.unpack(">I", z64[0x08:0x0C])[0],
        "cart": z64[0x3B:0x3D].decode("ascii", errors="replace"),
        "region": chr(z64[0x3E]) if len(z64) > 0x3E and z64[0x3E] else "?",
        "version": z64[0x3F] if len(z64) > 0x3F else 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="inp", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--info", action="store_true")
    ap.add_argument(
        "--summercart64-check",
        action="store_true",
        help="Warn if size > 64 MiB (optional SC64 tier)",
    )
    ap.add_argument(
        "--ceiling-check",
        action="store_true",
        default=True,
        help="Report headroom vs ~252 MiB mapped cart ceiling (default on)",
    )
    args = ap.parse_args()

    if not args.inp.is_file():
        print(f"ERROR: not found: {args.inp}", file=sys.stderr)
        print(
            "Hint: copy your owned dump to ~/Downloads/*.n64 or project rom/",
            file=sys.stderr,
        )
        return 1

    raw = args.inp.read_bytes()
    order = detect(raw)
    print(f"input:  {args.inp}")
    print(f"size:   {len(raw)} bytes ({len(raw)/(1024*1024):.3f} MiB)")
    print(f"order:  {order}")

    try:
        z64 = to_z64(raw, order if order != "unknown" else "z64")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if order == "unknown":
        print("WARNING: magic not recognized; wrote/parsed as-is")

    if args.info or True:
        if len(z64) >= 0x40:
            h = header(z64)
            print(f"name:   {h['name']!r}")
            print(f"cart:   {h['cart']}  region={h['region']}  ver={h['version']}")
            print(f"CRC:    {h['crc1']:08X} {h['crc2']:08X}")
            print(f"PC:     0x{h['pc']:08X}")
        print(f"sha256: {hashlib.sha256(z64).hexdigest()}")

    sc64 = 64 * 1024 * 1024
    ceiling = 252 * 1024 * 1024  # practical CPU-mapped cart domain
    if args.ceiling_check or True:
        if len(z64) > ceiling:
            print(
                f"MAPPED CEILING: OVER — {len(z64) - ceiling} bytes past ~252 MiB "
                f"(needs PI/banking plan)",
                file=sys.stderr,
            )
        else:
            print(
                f"MAPPED CEILING: OK — {ceiling - len(z64)} bytes free under ~252 MiB "
                f"({100 * len(z64) / ceiling:.1f}% used)"
            )
    if args.summercart64_check:
        if len(z64) > sc64:
            print(
                f"SUMMERCART64 tier: FAIL — {len(z64) - sc64} bytes over 64 MiB",
                file=sys.stderr,
            )
        else:
            print(f"SUMMERCART64 tier: OK — {sc64 - len(z64)} bytes free under 64 MiB")
    else:
        # Informational only — 64 MiB is not the project hard cap
        if len(z64) > sc64:
            print(
                f"note: size > 64 MiB — needs large flashcart (e.g. 64drive); "
                f"SC64/ED 64MiB tier would not load this image"
            )
        else:
            print(f"note: size ≤ 64 MiB — also loadable on SummerCart64/ED-class carts")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(z64)
        print(f"wrote:  {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
