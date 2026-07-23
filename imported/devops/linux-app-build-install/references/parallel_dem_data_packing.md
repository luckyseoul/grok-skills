# Parallel Data Generation for DEM Codes (RCFX Rung Campaign)

## Core Lesson
After investing in building a parallel DEM solver (LIGGGHTS 3.8 with MPI + full granular + sjkr cohesion), **do not fall back to slow single-threaded Python generators** for initial particle configurations. This defeats the purpose of the build.

Use the newly built parallel binary itself for packing via `fix insert/pack` + `mpirun`. This was the key correction in the RCFX Rung work.

## MPI Networking Workaround (soulkiller machine)
The first parallel pack attempts failed with:

```
Unable to find reachable pairing between local and remote interfaces
[soulkiller][[51768,1],4][.../btl_tcp_proc.c:266:mca_btl_tcp_proc_create_interface_graph]
MPI_ABORT was invoked on rank 0
```

**Working robust launch (discovered and validated):**

```bash
export OMPI_MCA_btl_tcp_if_include=lo,enp5s0
mpirun --mca btl_tcp_if_include lo,enp5s0 \
       --mca btl ^openib,ofi \
       --mca pml ob1 \
       -np 12 /usr/local/bin/liggghts < packer.in
```

Interfaces on the machine at the time: lo, enp5s0 (main), tailscale0.

This pattern should be the default when launching the built binary on this hardware.

## Recommended Pattern for Future Builds
1. Build the parallel tool (using this skill).
2. Immediately create a small "packer" input that uses the tool's own insertion/relaxation capabilities.
3. Launch the packer with the hardware-specific robust mpirun flags.
4. Use the resulting restart/data as the starting point for production physics runs.

This turns the build effort into end-to-end speed for real-scale simulations (e.g. RCFX Rung 2/4 at 75k–200k+ particles).

## Related Files in the Session
- `sims/liggghts/rung2/run_packer_direct.sh` — the concrete robust wrapper created.
- `sims/liggghts/rung2/generate_packed_data.py` — Python driver that emits the packer input.
- Updated Rung inputs now default to the packed data files.

This technique was the direct response to the user's question: "why is this running single threaded? the whole point of making 3.8 was so that it wouldnt take 4 years each rung".