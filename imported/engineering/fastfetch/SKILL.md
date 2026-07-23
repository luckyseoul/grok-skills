---
name: fastfetch
description: Quickly fetch and display comprehensive system specifications (CPU, GPU, memory, OS, kernel, etc.). Use this skill at the beginning of any new project or when working on an unfamiliar machine to rapidly understand the hardware and software environment.
---

# fastfetch — System Spec Fetcher

This skill exists to speed up "new project ingress" — getting oriented on a fresh machine or environment as fast as possible.

## When to Use

- Starting work on a new machine / container / VM
- Beginning a new project on unfamiliar hardware
- Needing quick hardware details (especially GPU/CUDA, CPU cores, RAM)
- Before running heavy workloads or deciding on acceleration strategies

## How to Use

Invoke this skill (e.g. `/fastfetch`) or naturally request system specs.

**Preferred method:** Run the helper script:

```bash
~/.grok/skills/fastfetch/scripts/fastfetch.sh
```

This script will:
- Use `fastfetch` if installed (with clean, useful flags)
- Gracefully fall back to basic system info if fastfetch is missing
- Detect common acceleration hardware (NVIDIA, Jetson, etc.)

## Manual / Alternative Usage

If the helper isn't available:

```bash
fastfetch --logo none
```

For JSON (machine-readable):

```bash
fastfetch --format json
```

## Installation (if missing)

The helper script will suggest the right command for your distro.

Common one-liners:

**Ubuntu / Debian:**
```bash
sudo apt update && sudo apt install fastfetch
```

**Fedora:**
```bash
sudo dnf install fastfetch
```

**Arch:**
```bash
sudo pacman -S fastfetch
```

Use the `pwnow` or `sudo` skill for privilege escalation when needed.

## Why This Skill Exists

Jumping into a new codebase or environment is slow when you don't know the hardware. This skill gives a fast, consistent, high-signal snapshot so you can immediately make smart decisions (e.g. "this has a V100, we should use CUDA", "only 6 cores, don't over-parallelize", "8GB RAM — be careful with large simulations").

It is especially valuable when working across multiple physical nodes or when dropped into cloud VMs, Jetson devices, or containers.
