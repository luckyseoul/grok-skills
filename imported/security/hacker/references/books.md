# Actionable Notes from Hacking Books (Grounded for the Hacker Skill)

This file contains condensed, immediately-applicable lessons from the books referenced by the hacker skill. Every note should translate into code, harness changes, or report structure the same day.

---

## Hacking: The Art of Exploitation (Jon Erickson)

**Core relevant ideas:**
- TOCTOU (Time Of Check To Time Of Use) races are extremely powerful when a privileged process trusts a path or file that an attacker can influence between check and use.
- Many privilege escalation vectors come from following user-controlled paths or trusting attacker-writable state (symlinks, environment, config files written by untrusted parties).
- Detailed understanding of how the kernel resolves paths (`openat`, `fchmodat`, etc.) and how setuid/privileged binaries interact with the filesystem is required.

**Direct mapping to current work (NVIDIA CDI LPE):**
- The nvidia runtime writes an OCI bundle (`state.json` + `config.json`) and then invokes (or triggers via hook) `nvidia-cdi-hook` as root.
- If we can overwrite the bundle contents (especially `"root": {"path": "/"}` or relative escapes) after the runtime has decided on the path but before the hook performs `fchmodat` or symlink operations, we get the hook to act on host paths with root privileges.
- Lesson: Make the race window as small and reliable as possible. Use `find` immediately after `docker create`, overwrite, then `docker start`. Consider inotify for production harnesses.
- Lesson: Test many path variants (`/`, `/proc/1/root`, `../../../`, `.`, mounted host paths). The book teaches you to think like the kernel path resolver.

**Action items for harness:**
- Add inotifywait watcher that overwrites the moment `state.json` appears.
- Log the exact `fchmodat` return value (0 vs EPERM) and correlate with the variant used.
- Keep pre/post stat records.

---

## Bug Bounty Bootcamp (Vickie Li) & Real-World Bug Hunting (Peter Yaworski)

**Key practices:**
- Scope is king — understand exactly what the program rewards (LPE via container runtime counts for NVIDIA Intigriti).
- A good PoC is minimal, reproducible, and shows clear impact (e.g. "host /etc/shadow now mode 777 from inside container via CDI hook").
- Document the exact reproduction steps, including timing-sensitive races if necessary.
- Collect strong artifacts: logs, strace, before/after state, minimal commands.
- Write the report as if the triager has 30 seconds.

**Action items:**
- Every serious harness run must end with a "minimal repro" section extractable from the logs/hits.
- Hits .jsonl format should be easy to turn into report bullets.
- Use the verification (stat changes) as the core of the impact statement.

---

## Traditional vs Generative AI Pentesting (Yassine Maleh, 2025) + 2026 Agentic Patterns

**Core loop (exactly what this skill implements):**
1. Recon / observation (run the hook, capture errors, strace, logs).
2. LLM generates mutations / variants (OCI specs, paths, timing parameters).
3. Volume execution on real target (80 workers).
4. Feedback: parse real results (errors, partial successes, fchmodat rc).
5. Next generation of smarter variants.
6. Reporting assisted by LLM.

**Practical techniques to copy:**
- Use errors as signal ("failed to determined container root", "Ignoring permission error with chmod").
- Generate variants that specifically target the failure modes observed.
- Parallelism is the multiplier — your 88 threads are the "army", the LLM is the brain.
- Keep the human in the loop for verification and report quality.

**Action items:**
- When the monitor shows repeated errors, immediately ask the LLM (this skill): "Here are the last 20 error lines from the CDI hook. Generate 25 new malicious OCI variants designed to bypass or abuse the root detection logic."
- Maintain a "corpus" of working + interesting variants, not just random.

---

## Quick Reference — Common Mutation Ideas (from books + live work)

- Absolute host root: `"root":{"path":"/"}`
- Proc root escape: `"root":{"path":"/proc/1/root"}`
- Relative: `"root":{"path":"."}` or `"../../.."`
- Mount tricks that give the hook visibility of host fs
- Annotations and extra fields that may affect parsing
- Different ociVersion strings
- Process user set to 0 explicitly

Always test both direct hook invocation (for learning) and real `docker create --gpus --runtime nvidia` (for the actual privileged path).

---

## Recommended Reading Order (for someone picking up the skill)

1. Art of Exploitation — chapters on races and file operations (immediate harness impact).
2. Bug Bounty Bootcamp — chapters on scoping + writing PoCs (report impact).
3. Maleh Generative AI Pentesting — the mutation + feedback loop chapter.
4. Real-World Bug Hunting — study 3-4 LPE-style reports.

Read → immediately modify or relaunch the harness with the new idea → analyze live output with this skill.

## Permanence Note

Update this file whenever you extract a new generalizable technique from a book or a live run. Because this lives in the GitHub repo, the knowledge compounds across sessions and can be shared.
