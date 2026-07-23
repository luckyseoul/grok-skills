---
name: self-refine-loop
description: >
  On-demand generator→critique→revise loop to improve a draft or artifact until
  quality criteria are met or a hard iteration cap is hit. Strict triggers only —
  not for routine replies. Use when the user says self-refine, refine this,
  critique and revise, reflexion, iterative revision, improve this draft,
  polish until good, or /self-refine-loop.
---

# Self-Refine Loop

Raise quality of a **specific** draft or artifact with a bounded critique loop.

**Not default behavior.** Do not auto-enter this loop on every answer. Only when
the user invokes it or clearly wants iterative polish on a named deliverable.

## When to use

- User: *self-refine*, *refine this*, *critique and revise*, *polish this draft*
- A patent section, design doc, skill file, or report must hit explicit criteria
- After `goal-verifier` finds quality gaps on a writing deliverable

## When **not** to use

- Quick Q&A or single-shot commands
- Pure verification → `goal-verifier` / `check-work`
- Open-ended research without a draft to revise
- Anything that would burn >5 full rewrite cycles without user consent

## Hard limits

| Limit | Default | Notes |
|-------|---------|-------|
| Max iterations | **5** | Stop earlier if score ≥ 8/10 |
| Critique bullets | **≤ 5** | Specific, actionable |
| Scope | **One artifact** | Don’t refine the whole repo |
| Token burn | Prefer targeted patches | Full rewrites only if structure is wrong |

## Inputs (capture before looping)

1. **Artifact** — path or pasted text (the current best version)
2. **Criteria** — user quality bar (tone, length, compliance, completeness)
3. **Constraints** — must not change X; cite sources; USPTO style; etc.
4. **Stop score** — default 8/10 confidence that criteria are met

If criteria are missing, propose 3–6 criteria and confirm once (or proceed with
explicit “assumed criteria” labeled as such).

## Loop

For iteration `i = 1..5`:

### A. Critique (skeptic)

Produce **at most 5** weakness bullets. Each bullet must be:

- Specific (quote or section id)
- Actionable (what to change)
- Mapped to a criterion

No vague “could be clearer.”

### B. Revise

Produce an improved artifact that addresses **every** critique bullet (or
explains why a bullet is rejected with reason).

Prefer:

- In-place section edits for long docs
- Full rewrite only for short drafts (< ~400 lines of intent)

### C. Score

`confidence = 0–10` that **user criteria** are met (not “I like it”).

- If `confidence >= 8` → **stop**, return best version + changelog
- If `i == 5` → **stop**, return best version + remaining gaps
- Else continue with the revised artifact as the new baseline

## Output template

```markdown
## Self-refine report
- Artifact: <path or label>
- Iterations: n / 5
- Final confidence: x/10

## Criteria used
1. …

## Changelog (per iteration)
### Iter 1
- Critique: …
- Changes: …
- Score: n/10

## Final artifact
<full text or path to written file>

## Remaining gaps (if score < 8)
- …
```

## File-backed artifacts

If the artifact is on disk:

1. Read current file before loop
2. Optionally backup: `cp file file.bak.selfrefine.<timestamp>` for high-stakes docs
3. Write the final version to the same path (or a new path if user asked for a draft)
4. Show a short diff summary (what sections moved)

## Pairing

| Before | After |
|--------|--------|
| `goal-verifier` finds writing gaps | Run self-refine on the draft |
| Self-refine claims “done” | Optional `goal-verifier` on criteria |
| Skill file quality | Prefer `skill-evolver` (has rubric + versions) |

## Anti-patterns

- Infinite polish past 5 iterations
- Critiquing tone only while factual errors remain
- Silently expanding scope (“also rewrote unrelated modules”)
- Running the loop unprompted on every assistant message
