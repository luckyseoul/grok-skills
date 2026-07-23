#!/usr/bin/env python3
"""Lightweight DFM preflight: print checklist and optional report scan.

Usage:
  python3 dfm_preflight.py
  python3 dfm_preflight.py DESIGN_NOTES.md
  python3 dfm_preflight.py --erc erc.rpt --drc drc.rpt
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CHECKLIST = Path(__file__).resolve().parent.parent / "references" / "dfm-checklist.md"


def scan_report(path: Path, kind: str) -> list[str]:
    if not path.is_file():
        return [f"{kind}: file not found: {path}"]
    text = path.read_text(errors="replace")
    issues = []
    # Heuristics across KiCad report formats
    for pat, label in [
        (r"(?i)error", "error-like lines"),
        (r"(?i)violation", "violation lines"),
        (r"(?i)unconnected", "unconnected"),
    ]:
        hits = re.findall(pat, text)
        if hits:
            issues.append(f"{kind}: found {len(hits)} matches for /{pat}/ — open {path}")
    if not issues:
        issues.append(f"{kind}: no obvious error keywords (still read the full report)")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("notes", nargs="?", help="Optional DESIGN_NOTES.md to mention")
    ap.add_argument("--erc", type=Path, help="ERC report path")
    ap.add_argument("--drc", type=Path, help="DRC report path")
    args = ap.parse_args()

    print("=== PCB DFM preflight ===\n")
    if CHECKLIST.is_file():
        print(f"Full checklist: {CHECKLIST}\n")
        # Print section headers only for quick scan
        for line in CHECKLIST.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                print(line)
            elif line.startswith("- [ ]"):
                print(line)
    else:
        print("WARNING: dfm-checklist.md missing")

    print("\n=== Report scan ===")
    findings: list[str] = []
    if args.erc:
        findings.extend(scan_report(args.erc, "ERC"))
    if args.drc:
        findings.extend(scan_report(args.drc, "DRC"))
    if not args.erc and not args.drc:
        print("No --erc/--drc given. Run kicad-cli erc/drc then re-run.")
    for f in findings:
        print(f"  • {f}")

    if args.notes:
        p = Path(args.notes)
        print(f"\n=== Notes file: {p} ===")
        if p.is_file():
            text = p.read_text(errors="replace")
            for key in ("Open risks", "Fab", "stackup", "ERC", "DRC"):
                if key.lower() in text.lower():
                    print(f"  contains section/keyword: {key}")
        else:
            print("  missing")

    print("\nPreflight complete. Resolve Blockers before Gerbers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
