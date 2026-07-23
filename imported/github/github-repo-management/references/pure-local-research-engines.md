# Pure Local Research Compute Engines (No Upstream)

This is the "no-upstream" variant of the local research workspace pattern.

**Characteristics**:
- Custom research code with no authoritative GitHub reference implementation to sync against.
- Often contains many iterative variants of the core algorithm (different limits, backends, post-processors, "fast"/"complete"/"resume" flavors).
- Heavy use of external large storage for outputs (result CSVs, checkpoints, streams).
- Low-level optimizations (C extensions, CUDA kernels) mixed with high-level Python drivers.
- The user expects these to live as first-class repos under their luckyseoul GitHub account rather than loose directories.

**Canonical example from 2026-05-25 session**: `/home/nick/wieferich_engine`

### Inventory of the codebase (what a future session should recognize)
- Core math: `src/wieferich_core.c` (OpenMP mulmod/modexp + sweep_bases/sweep_primes), `src/wieferich_cuda.cu` (GPU kernel with custom Barrett mulmod), `src/wieferich_module.c` (Python C extension exposing numpy arrays).
- GPU wrapper: `wieferich_cuda.py` (ctypes to libwieferich_cuda.so).
- Drivers: `gpu_wieferich_hunt.py` (streaming GPU sweeps to 1e8 with checkpoint + stream.csv), `reciprocity_hunt.py` (graph walker using seeds + bidirectional base<->prime exploration hunting reciprocal pairs, pickle checkpoints, sympy), multiple `hunt_1e9_*.py` variants (fast/complete/resume/precomputed).
- Post-processing and verification: `post_process*.py`, `verify.py`, `gpu_correct.py`, `homerun.py`, `multiseed.py`, `hunt_base.py`, `merge.py`.
- Build: `setup.py` (builds wieferich_module with -fopenmp -O3 -march=native).
- Artifacts: `results_1e9_complete.csv` (402k lines), `results_1e9.csv`, `results_1e9_fast.csv`, checkpoints, `hunt_1e9.log`.
- Hardcoded data paths in scripts: `/mnt/storage/wieferich_1777`, `/boot/wieferich_fast`.

The project had **no .git** and **zero presence** on GitHub under luckyseoul (confirmed via API search).

### Required prerequisite for these projects: external storage mount
These engines are designed around a large data drive (here 9.1 TiB) for result streams and checkpoints.

**Diagnostic + fix pattern** (device names drift — never rely on sda/sdb):
1. `lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,LABEL,UUID` — identify the real device (was sda2, not the expected sdb2).
2. `blkid /dev/sda2` for UUID.
3. Check `cat /etc/fstab` — usually no entry.
4. Verify `/mnt/storage` dir exists (often pre-created but empty).
5. Test: `sudo mount -o ro /dev/sda2 /mnt/storage`
6. Permanent: add to fstab using **UUID** + `nofail,x-systemd.device-timeout=10` so boot doesn't hang:
   ```
   UUID=cb880055-9646-404f-a5b5-3db6d38fe8eb  /mnt/storage  ext4  defaults,noatime,nofail,x-systemd.device-timeout=10  0  2
   ```
7. `sudo mount -a`

Journalctl often shows the initial detection + occasional UAS/ATA errors (common with USB enclosures).

### Recommended workflow when user says "in my fucking repos" (or equivalent frustration)
1. Use search_files + read_file on the dir to produce a clean inventory of variants + data artifacts (as above).
2. Confirm no git and no GitHub presence (curl to search API + git status).
3. Fix the storage mount first (the scripts will fail without it).
4. Offer full autonomous promotion:
   - `git init` in the dir.
   - Sensible .gitignore (ignore huge results/*.csv, __pycache__, build/, *.so if desired).
   - Plain-text `OVERVIEW.txt` (critical — user is not a SWE): describe the different hunt strategies, what "reciprocal pairs" means, scale of runs performed, how to resume a hunt, where results live.
   - Simple launcher (`run.sh` or Makefile) for common actions (build extension, small test hunt, analyze latest CSV).
   - Commit the source + small artifacts + OVERVIEW.
   - Create repo on GitHub (luckyseoul/wieferich-primes or wieferich-engine) and push.
5. After promotion, the project becomes maintainable across sessions and survives device/storage changes.

### Pitfalls specific to this class
- **Device name drift + missing fstab** is the #1 reason the data paths in the scripts are broken. Always diagnose with lsblk + UUID.
- Dozens of variant scripts represent real research evolution — do not aggressively delete "old" ones without user direction.
- Result CSVs can be enormous; decide per-project what belongs in git vs lives only on the mounted storage.
- CUDA .so and build artifacts are host-specific; .gitignore them or keep only sources.
- User will get angry if the work stays as an anonymous directory when they have a clear "my repos" expectation.

### Cross-reference
See the main `local-reference-impl-sync.md` for the hybrid "upstream reference + local experiments" sibling pattern (e.g. the CPB/DTN case). The two patterns share the same underlying values: full agent initiative, plain-text accessibility artifacts for non-SWE users, local git for the research part, and eventual promotion to luckyseoul GitHub.

This pattern (inventory → storage fix → git promotion + OVERVIEW + launcher) is now the canonical recipe for pure local numeric/compute research engines.