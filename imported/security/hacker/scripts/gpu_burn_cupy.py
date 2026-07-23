#!/usr/bin/env python3
"""Persistent GPU load using CuPy (or fallback to numba).
Run this in background while doing CPU-heavy bounty work (parallel fuzz etc).
This drives real V100 utilization when nvcc host compile is broken by new gcc.
"""
import os, time
print(f"[hacker-gpu-burn] pid={os.getpid()} starting...")

try:
    import cupy as cp
    print("[hacker-gpu-burn] using CuPy")
    a = cp.random.random((10000, 10000), dtype=cp.float32)
    b = cp.random.random((10000, 10000), dtype=cp.float32)
    i = 0
    while True:
        c = cp.matmul(a, b)
        cp.cuda.Device().synchronize()
        i += 1
        if i % 10 == 0:
            print(f"[cupy] {i} heavy matmuls")
except Exception as e:
    print("CuPy failed, trying numba:", e)
    try:
        import numpy as np
        from numba import cuda
        @cuda.jit
        def burn(arr, iters):
            i = cuda.grid(1)
            if i < arr.size:
                x = arr[i]
                for _ in range(iters):
                    x = x * 1.00001 + 0.0001
                arr[i] = x
        N = 1024*1024*32
        d = cuda.to_device(np.ones(N, dtype=np.float32))
        threads = 256
        blocks = (N + threads - 1) // threads
        while True:
            burn[blocks, threads](d, 3000)
            cuda.synchronize()
    except Exception as e2:
        print("All GPU burn methods failed:", e2)
        while True: time.sleep(60)
