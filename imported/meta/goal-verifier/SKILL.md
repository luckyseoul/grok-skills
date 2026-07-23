---
name: goal-verifier
description: >
  Verify that the current session actually achieved the user's stated goal,
  with evidence (paths, commands, outputs) — not vibes. Complements check-work
  (code/diff focus) by focusing on goal restatement, acceptance criteria, and
  pass/fail per criterion. Use when the user says verify goal, confirm success,
  did we finish, is this done, acceptance criteria, goal check, /goal-verifier,
  or asks "did I achieve this".
---

# Goal Verifier

Prove the **user's goal** was met. Prefer hard evidence over narrative.

This skill is **goal-first**. Use **`check-work`** when the ask is “verify the
diff / build / tests.” Use **this skill** when the ask is “are we done with
what I asked for?” Both may run in one session.

## When to use

- User: *verify goal*, *confirm success*, *did we finish*, *is this done*
- Long multi-step work about to be declared complete
- User restates a goal mid-session and wants a status vs that goal
- Before claiming a multi-artifact deliverable is ready (train + smoke + wire)

## When **not** to use

- Pure code review of a PR → `review` / `check-work`
- Continuous background status → `update`
- Vague “looks good?” with no goal → restate goal first, then verify

## Workflow

### 1. Restate the goal (one sentence)

Write a single sentence the user would accept as “done means X.”

If the goal is ambiguous, **stop and ask** one clarifying question. Do not invent
success criteria the user never agreed to.

### 2. Build acceptance criteria

List **explicit** criteria from the user, then **inferred** ones only if they
are necessary for “done” (e.g. “abliterate both models” implies both dirs exist
and smokes answer).

Format:

| # | Criterion | Source (explicit / inferred) |
|---|-----------|------------------------------|
| 1 | … | explicit |

Mark inferred criteria so the user can reject them.

### 3. Check each criterion with evidence

For every criterion, gather **fresh** evidence in this turn:

- Files: `ls` / `read_file` / size / mtime
- Commands: re-run a cheap smoke if the claim depends on runtime
- Processes: only if “running service” was part of the goal
- Negative evidence: missing path, empty file, refusal string in smoke

**Do not** treat “I intended to…” or earlier un-verified assistant claims as
evidence.

Verdict per criterion: **PASS** | **FAIL** | **PARTIAL**

### 4. Overall verdict

- **GOAL MET** — all critical criteria PASS
- **GOAL NOT MET** — any critical FAIL
- **PARTIAL** — criticals pass but optional/inferred incomplete

Never mark GOAL MET if a critical criterion is PARTIAL.

### 5. If not met: smallest next actions

Give a **numbered fix list** (max 5), ordered by dependency. Prefer actions you
can run next over advice dumps.

If user asked only for verification, **do not** start fixing unless they also
asked to finish / fix gaps. Offer: “Want me to close the gaps?”

## Output template (required)

```markdown
## Goal
<one sentence>

## Criteria
| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | … | PASS/FAIL/PARTIAL | path, command, or quote |

## Verdict
GOAL MET | GOAL NOT MET | PARTIAL

## Gaps (if any)
1. …
2. …

## Recommended next steps (if not met)
1. …
```

## Evidence rules (non-negotiable)

| Claim type | Minimum evidence |
|------------|------------------|
| File/dir exists | path + listing or size |
| Model trained / abliterated | adapter or `abliteration.json` + smoke output |
| Command works | re-run or log excerpt from this session after the change |
| Alias/wired runner | script content shows target path + one smoke |
| “No refusal” | quoted generation that answers the technical ask |

False-positive guard: if evidence is only conversation prose, mark **FAIL** or
**PARTIAL**, not PASS.

## Relationship to other skills

| Skill | Use for |
|-------|---------|
| `check-work` | Subagent code/diff/build/test verification |
| `update` | Background task liveness |
| `self-refine-loop` | Improve a draft **after** gaps are known |
| `abliteration` | Local model over-refusal (rare; gated) |

## Anti-patterns

- Declaring success because the plan was good
- Expanding the goal to make more work
- Running expensive full re-trains just to verify (prefer cheap smokes)
- Hiding FAIL criteria under “minor notes”
