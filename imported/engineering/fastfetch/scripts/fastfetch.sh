#!/bin/bash
#
# fastfetch.sh - Smart wrapper for fast system spec fetching.
# Used by the fastfetch skill to speed up new project/machine ingress.

set -euo pipefail

# Check if fastfetch is available
if command -v fastfetch &> /dev/null; then
    echo "=== fastfetch ==="
    fastfetch --logo none --structure Title:Separator:OS:Kernel:Uptime:Packages:Shell:CPU:GPU:Memory:Disk:LocalIP
    echo ""
    echo "Tip: For JSON output use: fastfetch --format json"

    # === Jetson enhancement (runs even when fastfetch is present) ===
    is_jetson() {
        [[ -f /proc/device-tree/model ]] && grep -qi "nvidia.*jetson" /proc/device-tree/model 2>/dev/null
    }

    if is_jetson; then
        echo ""
        echo "=== Jetson Hardware (real SoC) ==="
        echo "Model: $(cat /proc/device-tree/model 2>/dev/null | tr -d '\0')"

        if command -v tegrastats &> /dev/null; then
            stats=$(timeout 3 tegrastats --interval 200 --count 2 2>/dev/null | tail -1)
            if [[ -n "$stats" ]]; then
                gpu_line=$(echo "$stats" | grep -o 'GPU@[0-9]*%[^ ]*' || true)
                ram_line=$(echo "$stats" | grep -o 'RAM [0-9]*/[0-9]*MB' || true)
                echo "GPU Status: ${gpu_line:-N/A}"
                echo "RAM Usage:  ${ram_line:-N/A}"
            fi
        fi

        if command -v nvpmodel &> /dev/null; then
            power_mode=$(nvpmodel -q 2>/dev/null | tail -1 || echo "unknown")
            echo "Power Mode: $power_mode"
        fi
    fi

    exit 0
fi

echo "fastfetch is not installed."

# Try to detect package manager and suggest install
if command -v apt &> /dev/null; then
    echo "Detected apt (Debian/Ubuntu-based)."
    echo "Recommended: sudo apt update && sudo apt install fastfetch"
elif command -v dnf &> /dev/null; then
    echo "Detected dnf (Fedora/RHEL-based)."
    echo "Recommended: sudo dnf install fastfetch"
elif command -v pacman &> /dev/null; then
    echo "Detected pacman (Arch-based)."
    echo "Recommended: sudo pacman -S fastfetch"
else
    echo "Could not auto-detect package manager."
    echo "Please install fastfetch manually from https://github.com/fastfetch-cli/fastfetch"
fi

echo ""
echo "=== Fallback system information ==="
echo "Hostname: $(hostname)"
echo "OS: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d= -f2- | tr -d '\"' || uname -o)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "CPU: $(lscpu 2>/dev/null | grep 'Model name' | head -1 | cut -d: -f2- | xargs || echo 'unknown')"
echo "Cores: $(nproc 2>/dev/null || echo 'unknown')"
echo "Memory: $(free -h 2>/dev/null | awk '/^Mem:/ {print $2}' || echo 'unknown')"
echo "Uptime: $(uptime -p 2>/dev/null || uptime)"

# Check for GPU
if command -v nvidia-smi &> /dev/null; then
    echo ""
    echo "=== NVIDIA GPU ==="
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
fi

# === Jetson / Orin specific enhancement ===
is_jetson() {
    [[ -f /proc/device-tree/model ]] && grep -qi "nvidia.*jetson" /proc/device-tree/model 2>/dev/null
}

if is_jetson; then
    echo ""
    echo "=== Jetson Hardware (real SoC) ==="
    echo "Model: $(cat /proc/device-tree/model 2>/dev/null | tr -d '\0')"

    if command -v tegrastats &> /dev/null; then
        # Get one quick sample (tegrastats needs a moment)
        stats=$(timeout 3 tegrastats --interval 200 --count 2 2>/dev/null | tail -1)
        if [[ -n "$stats" ]]; then
            gpu_line=$(echo "$stats" | grep -o 'GPU@[0-9]*%[^ ]*' || true)
            ram_line=$(echo "$stats" | grep -o 'RAM [0-9]*/[0-9]*MB' || true)
            echo "GPU Status: ${gpu_line:-N/A}"
            echo "RAM Usage:  ${ram_line:-N/A}"
        fi
    fi

    if command -v nvpmodel &> /dev/null; then
        power_mode=$(nvpmodel -q 2>/dev/null | tail -1 || echo "unknown")
        echo "Power Mode: $power_mode"
    fi
fi
