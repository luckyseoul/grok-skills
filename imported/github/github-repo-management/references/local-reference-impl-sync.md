# Local Reference Implementation Sync (Non-Git Workspace)

Common pattern when maintaining a local research/DTN/IETF experiment workspace that mixes:
- A copy (or vendor snapshot) of an upstream reference implementation (`impl/`)
- Local-only experiment artifacts (precomputed CSVs, simulator configs with hardcoded paths, reports, custom harnesses, Java routers, etc.)

**Canonical example:** `/home/nick/dtn/cpb` vs `https://github.com/luckyseoul/draft-perry-dtn-cpb` (the `impl/` directory is the source of truth for `cpb.py` + `test_cpb.py` and the Mars config1_sim; local adds Helsinki Config 2 / THE-ONE work).

## 1. Discovery (when you only have "CPB" or a short name)

Local dir has no `.git`, only abbreviated clues.

```bash
curl -s "https://api.github.com/search/repositories?q=draft-perry-dtn-cpb+OR+cpb+contact+probability+block+dtn+in:readme+in:description" \
| python3 -c '
import sys, json
for item in json.load(sys.stdin).get("items", [])[:5]:
    print(item["full_name"], item["html_url"], item.get("description","")[:100])
'
```

(See `references/github-api-cheatsheet.md` for the search and JSON extraction patterns.)

## 2. Comparison & Selective Sync (preserve local work)

```bash
# Temporary clean upstream view
rm -rf /tmp/upstream-cpb
git clone --depth 1 https://github.com/luckyseoul/draft-perry-dtn-cpb.git /tmp/upstream-cpb

# Inspect
ls /tmp/upstream-cpb/impl/
diff -u /home/nick/dtn/cpb/cpb.py /tmp/upstream-cpb/impl/cpb.py | head -30

# Selective copy of reference material only
mkdir -p /home/nick/dtn/cpb/impl
cp /tmp/upstream-cpb/impl/cpb.py /home/nick/dtn/cpb/impl/
cp /tmp/upstream-cpb/impl/test_cpb.py /home/nick/dtn/cpb/impl/
cp /tmp/upstream-cpb/impl/requirements.txt /home/nick/dtn/cpb/impl/
cp /tmp/upstream-cpb/impl/config1_sim.py /home/nick/dtn/cpb/impl/
cp /tmp/upstream-cpb/impl/README.md /home/nick/dtn/cpb/impl/impl_README.md

# Do NOT touch: compute_probs.py, config2.txt, config2_probs.csv, reports/, any custom Java, THE-ONE configs
```

## 3. Post-Sync Polish & Reorganization (this session's extension)

After the raw sync, the workspace is usually messy (mixed files at root, stale pycache, root-owned artifacts, outdated docs).

**Recommended structure for long-term maintainability:**

```
cpb/
├── OVERVIEW.txt                 # plain-English bridge doc (critical for non-SWE users)
├── run.sh                       # one-command launcher (test / demo / sim / probs)
├── demo_cpb.py                  # tiny impressive self-contained demo
├── compute_probs.py             # local experiment tool (now made portable)
├── config2.txt                  # THE-ONE scenario (keep absolute paths)
├── config2_probs.csv            # important data
├── reports/
├── impl/                        # pristine upstream reference snapshot
│   ├── cpb.py
│   ├── test_cpb.py
│   ├── config1_sim.py
│   └── ...
└── .gitignore                   # tailored (ignore reports/, generated CSVs, .venv, __pycache__)
```

**Actions performed in the 2026-05-24 session:**
- `mkdir impl && mv` the reference files into it
- Updated compute_probs.py and config1_sim.py with `Path(__file__).resolve().parent` + env var override for portability
- Created `OVERVIEW.txt` (plain text, no markdown), `demo_cpb.py`, `run.sh` (bash menu for common actions)
- `chown -R nick:nick` (ownership drift is extremely common)
- `rm -rf __pycache__`
- `python3 -m venv` attempt (note: may require `apt install python3-venv` on some hosts — capture the fix if it fails)
- Ran long sim via `terminal(background=true, notify_on_complete=true)` + `process(wait=...)` pattern

## 4. Local Git for the Hybrid Workspace

The upstream reference should stay in sync with GitHub; the experiments deserve their own history.

```bash
cd /home/nick/dtn/cpb
git init
git config user.name "Nick"
git config user.email "nick@localhost"

# Add only the things you own or control
git add .gitignore OVERVIEW.txt run.sh demo_cpb.py compute_probs.py config2.txt
git commit -m "Initial clean workspace..."

# Add the large but important data + the reference snapshot
git add config2_probs.csv impl/
git commit -m "Add probability data and full reference implementation snapshot"

# Future: git add -u; git commit when you improve the Helsinki side
```

Use `.gitignore` that explicitly un-ignores the one important CSV while ignoring generated outputs and reports.

## 5. Accessibility Layer for Non-Technical Users (strong user preference)

The user profile strongly favors the AI taking initiative to make projects "accessible and impressive for non-technical users" and to "ride the wave" rather than asking for choices.

**Always add after a sync:**
- A top-level `OVERVIEW.txt` written in simple language explaining the split (reference vs local experiments)
- A `run.sh` or `demo_*.py` that gives immediate "wow" value with zero setup
- Plain-text files only (no markdown if the user will view in terminal)

Example `run.sh` menu:
- test → official conformance
- demo → 20-line visual encoder demo
- sim → long-running Mars reproduction (background + notify pattern)
- probs → refresh local CSV

## 6. Verification (non-negotiable)

After every sync + polish:
```bash
cd /local/cpb
python3 impl/test_cpb.py          # must say "All tests passed"
python3 impl/config1_sim.py       # optional but powerful — expect ~28s walltime and the exact draft numbers (0.9962 vs 0.9997+)
python3 demo_cpb.py               # quick smoke
./run.sh test
```

The test suite is the living specification (float16 table, Listings 2/7, BTSD, strict mode, DoS limit, byte stability).

## 7. Key Pitfalls & Durable Rules

- **Preserve local-only files at all costs.** Never let a sync delete compute_probs.py, config2.*, reports/, or custom Java routers. These are the actual research.
- **Hardcoded paths are sacred** until the whole workspace is deliberately moved. THE-ONE Java configs and experiment scripts frequently embed absolute paths.
- **Ownership and cache cleanup** after every bulk operation (chown, rm -rf __pycache__).
- **Reorganization is valuable** — moving reference code into `impl/` after the first sync makes future updates trivial and the workspace feel professional.
- **Long-running verification** (full sims) → always use background + notify_on_complete + process(wait) so the session does not block.
- **Git for the hybrid dir** turns a fragile copy-paste workspace into something that can survive months of incremental local improvement while still allowing clean upstream refreshes.
- **Accessibility artifacts** (OVERVIEW + run.sh + demo) are first-class deliverables, not optional polish, when the user is not a software engineer.

## When to Apply / Re-apply This Pattern

- Before any important experiment campaign that depends on the encoder/decoder fidelity.
- Whenever you notice the local cpb.py is smaller or the test suite is missing cases.
- After upstream draft-perry-dtn-cpb (or any similar IETF/reference-impl repo) advances.
- Periodically as a "spring cleaning" pass to keep the working directory impressive and maintainable.

This pattern (including the 2026-05-24 reorganization, launcher scripts, local git, and accessibility focus) is now the canonical recipe for this class of "reference + local research" workspace.

Related files:
- references/github-api-cheatsheet.md (discovery and curl+python JSON tricks)
- The main github-repo-management SKILL.md (high-level gh vs git+curl table + this pattern)

## Session Notes (2026-05-24)

- User explicitly endorsed full autonomous polish ("go ahead, you do all that").
- Strong alignment with user preference for initiative + making things accessible/impressive.
- All core reference files ended byte-identical to GitHub.
- Workspace left in clean, git-tracked, runnable state with simple entry points.

## 8. Jetson / Embedded Hardware Deployment Layer (2026-05-24 extension)

After the workspace is clean, git-tracked, and accessible, the natural next deliverable for real-world use (especially with user on Jetson + ION-DTN) is a **hardware-targeted CLI wrapper** that:

- Imports the pristine reference `impl/cpb.py`
- Hard-codes the user's personal IPN node (268485121 in this case) as `MY_IPN_NODE`
- Provides a simple `encode` / `decode` / `info` CLI with sensible defaults for that node
- Supports both raw CPB and BTSD-wrapped output (the latter is what you actually insert into a BPv7 extension block on ION)
- Is easy to scp to the Jetson (copy `jetson/` + `impl/`, `pip install cbor2`)

**Pattern used:**

```bash
mkdir -p jetson/
# Write jetson_cpb.py containing the full CLI + the node constant
# Patch any strict field handling (source PCE must be bytes → str(node).encode('ascii'))
chmod +x jetson/jetson_cpb.py

# Integrate into the accessibility layer
# Update run.sh with a "jetson" subcommand that forwards args
# Append a "Jetson Deployment" section to OVERVIEW.txt (plain text)

# Commit the deployment artifact
git add jetson/ run.sh OVERVIEW.txt
git commit -m "Add Jetson-ready CPB CLI tool for node 268485121"
```

**Key code decisions captured:**
- Source PCE (field 3) must be bytes in the reference encoder → always convert user node number to `str(MY_IPN_NODE).encode("ascii")`
- Default to CGR confidence metric (1) and reasonable validity (3600s)
- "now" timestamp helper using DTN epoch (seconds since 2000-01-01)
- BTSD flag for direct use in bundle construction
- Self-documenting header that tells the non-SWE user exactly how to copy to Jetson + ION

**Why this belongs in the pattern:**
The sync + reorganization + launchers make the reference usable on the developer's machine. The Jetson wrapper makes it usable on the actual embedded DTN node the user is building/running experiments on. It turns the abstract reference into concrete, node-specific tooling with zero friction.

**Pitfall:** Do not hard-code the node in the reference `impl/` — only in the deployment wrapper. The reference must stay generic and byte-exact with GitHub.

This completes the full lifecycle for this class of work:
1. Discover & selectively sync upstream reference
2. Reorganize + polish + accessibility layer (OVERVIEW + run.sh + demo)
3. Local git for the hybrid workspace
4. Hardware deployment wrapper (Jetson CLI with user's IPN node)

Future sessions maintaining similar "reference impl + local research + embedded target" projects should repeat all four steps.
