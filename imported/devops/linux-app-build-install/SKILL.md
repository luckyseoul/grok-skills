---
name: linux-app-build-install
description: Reusable patterns and helpers for installing, removing, and building applications from apt, source (cmake/make/configure), handling dependencies, verification, and cleanup on Debian/Ubuntu-based Linux systems.
version: 1.0
created: 2026-05-31
---

# Linux App Build & Install Skill

## When to use this skill
- You need to build something from source (LIGGGHTS, custom tools, research software).
- Installing/removing packages with proper dependency management.
- Creating repeatable build scripts for complex applications.
- Troubleshooting "header not found", linker errors, or "invalid pair style" after partial builds.
- Setting up reproducible environments for simulation codes (DEM, CFD, etc.).

## Core Principles
- Always prefer the distribution's packaging system when possible.
- For source builds: use a dedicated `build-APP` directory.
- Capture full logs.
- Verify the final binary works with a smoke test.
- Document the exact commands used (for future reproduction).
- Clean up failed partial builds aggressively.
- Use `peratomtypepair` / modern syntax when dealing with updated scientific codes (common source of "Invalid model" errors).

## 1. Apt-based Install / Remove

```bash
# Update first
sudo apt-get update -qq

# Install with build deps
sudo apt-get install -y build-essential g++ gfortran \
    libopenmpi-dev openmpi-bin cmake git \
    libfftw3-dev libjpeg-dev libpng-dev \
    libvtk9-dev libboost-mpi-dev   # example for scientific codes

# Remove cleanly
sudo apt-get remove --purge -y PACKAGE
sudo apt-get autoremove -y
```

## 2. Source Build Patterns (Recommended Structure)

Always do this:

```bash
mkdir -p ~/build-APP && cd ~/build-APP
git clone --depth 1 URL APP
cd APP

# For cmake projects (preferred)
mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local -DOPTION=ON
make -j $(nproc)
sudo make install

# For classic make (LAMMPS-style / LIGGGHTS)
cd src
make clean-all
make yes-granular yes-molecule   # enable needed packages
make -j $(nproc) mpi
sudo cp lmp_* /usr/local/bin/APP
```

### Handling Common Failures
- **Missing headers (vtkSmartPointer.h, etc.)** → Install the `-dev` package for the exact major version the build expects (`libvtk9-dev` vs `libvtk6-dev`).
- **"Invalid pair style / model" after build** → The binary was built without the required package (granular, cohesion, etc.). Rebuild with `make yes-XXX`.
- **peratomtypepair errors** → Modern granular codes require full N×N matrices for 2+ atom types. See example below.
- **Linker "cannot find -lvtkCommonCore-6.2"** → VTK version mismatch between compile flags and installed libs. Strip VTK from Makefile or install matching dev package.

## 3. Verification Template

After any build:

```bash
which APP || echo "Not in PATH"
APP --version 2>&1 | head -3
# Smoke test with minimal input
APP < /path/to/minimal.in 2>&1 | tail -10
```

## 4. Example: Full LIGGGHTS 3.8 Build (what we just did)

See the real script we created:
`/home/nick/rcfx/sims/liggghts/build_liggghts.sh`

Key lesson: The Ubuntu repack source + its cmake patches + `libvtk9-dev` + `libboost-mpi-dev` gave us the exact 3.8.0 binary with sjkr cohesion support.

## 5. Rung Campaign Specific Helpers (for RCFX)

When setting up new Rung inputs for LIGGGHTS 3.8+:

```bash
# Correct modern syntax (2 atom types)
fix m3 all property/global coefficientRestitution peratomtypepair 2 val11 val12 val21 val22
pair_style gran model hertz tangential history cohesion sjkr
```

Always create a `rungX_0.14_sjkr.in` (or equivalent) + updated `launch_rungX.sh`.

### Parallel Data Generation for Production Runs (RCFX Rung Campaign Lesson)
**Critical workflow correction** (user feedback): After spending the effort to build a parallel DEM solver (LIGGGHTS 3.8 MPI + full models), do **not** fall back to slow single-threaded Python RSA generators for initial particle data. This defeats the entire reason for the build.

**Correct pattern**:
- Use the newly built parallel binary itself for packing via `fix insert/pack` + relaxation under `mpirun`.
- This was the direct response to the signal: "why is this running single threaded? the whole point of making 3.8 was so that it wouldnt take 4 years each rung".

See the full case study and the exact robust launch command for this hardware:

`references/parallel_dem_data_packing.md`

Includes the specific MPI flags that resolved "Unable to find reachable pairing between local and remote interfaces" on soulkiller:
```
mpirun --mca btl_tcp_if_include lo,enp5s0 --mca btl ^openib,ofi --mca pml ob1 ...
```

Always apply this mindset: once the parallel tool exists, make the data prep step use it too.

## 6. Cleanup & Maintenance

```bash
# After failed build
rm -rf ~/build-APP/APP/build ~/build-APP/APP/Obj_*

# Full removal of custom install
sudo rm -f /usr/local/bin/APP
sudo rm -rf /usr/local/lib/libAPP*
```

## 7. Skill Usage in Future Sessions

When the user says "build X" or "install proper Y", load this skill first, then follow the patterns above. Reference this file when creating new build scripts.

This skill was created after successfully building the full LIGGGHTS 3.8.0 for the RCFX Rung campaign (May 2026).

## 8. Execution Discipline (User Communication Preference — Critical)

**Trigger**: User expresses frustration with explanations, setup overhead, scripts, or timelines ("just run the damn sims", "you're the expert", "I've been stuck on this for months", "stop talking and execute").

**Required behavior**:
- Immediately drop into low-prose execution mode.
- Minimize additional explanation, new scripts, or options lists.
- Use tools directly to launch/monitor the actual run (mpirun, background jobs, process polling).
- Report only essential status: what was launched, current state, and the single next minimal action required from the user (if any).
- Do not propose "another script" or "here's how you can do it" unless the user explicitly asks for the command.

**Pitfall to avoid**: Continuing to hand the user more setup scripts or detailed rationales after they have signaled they want the simulations driven to completion. This pattern caused repeated frustration in the May 2026 Rung campaign sessions.

See `references/execution_mode_communication.md` for exact phrasing patterns that worked vs. patterns that triggered frustration.


---

**Provenance:** MIT copy from Hermes Agent skills (`/home/nick/.hermes/skills/devops/linux-app-build-install`). Retain MIT license notice.
