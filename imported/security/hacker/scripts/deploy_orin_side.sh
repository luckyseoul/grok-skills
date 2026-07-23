#!/bin/bash
# Small side mission deploy to real Orin (Jetson)
# Run this on the main host after you have the Orin password.
# It will scp the int8+variant script and launch persistent background load + generator.
set -e
read -s -p "Orin nick@192.168.1.162 password: " P; echo
sshpass -p "$P" scp -o StrictHostKeyChecking=no ~/.grok/skills/hacker/scripts/orin_int8_side.py nick@192.168.1.162:/tmp/
sshpass -p "$P" ssh -o StrictHostKeyChecking=no nick@192.168.1.162 '
  nohup python3 /tmp/orin_int8_side.py > /tmp/orin_side.log 2>&1 &
  echo "Orin INT8 side mission launched (int8 matmul + variant emitter)"
  sleep 3
  ps aux | grep -E "[o]rin_int8_side|python3 /tmp/orin"
  head -3 /tmp/orin_side.log
'
echo "To pull variants back later: sshpass -p '...' scp nick@192.168.1.162:/tmp/orin_variants.jsonl ./"
unset P
