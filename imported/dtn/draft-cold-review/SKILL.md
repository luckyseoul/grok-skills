---
name: draft-cold-review
description: >
  Cold-read an Internet-Draft or protocol paper as a first-time independent
  reviewer: abstract honesty, experiment vs claims, Implementation Status,
  dead paths, metric semantics, security. Triggers: cold review draft,
  I-D review, review the Internet-Draft, /draft-cold-review.
version: 1.0.0
author: luckyseoul
license: MIT
---

# Draft Cold Review

## Method
1. Fresh clone or current tip; note commit.
2. Read Abstract, § experiment, Implementation Status, open questions.
3. Grep for: adversarial, placeholder, dead paths, unshipped policies, Hypothesis, LOC lies.
4. Run shipped tests if a companion repo exists.
5. Verdict: Ship-ready / Needs fixes / Broken.

## Output format
### Verdict
### Critical / Major / Minor
### Clean
### Residual risk

Pair with `check-work` for code diffs and `goal-verifier` for goal completion.
