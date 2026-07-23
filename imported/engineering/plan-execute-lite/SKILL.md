---
name: plan-execute-lite
description: >
  Execute a small sequential or lightly parallel implementation plan from a
  design note or checklist: one branch per chunk, tests, then PR. For full
  Graphite DAG orchestration use product /execute-plan when available.
  Triggers: execute this plan, implement the checklist, /plan-execute-lite.
version: 1.0.0
author: luckyseoul
license: MIT
---

# Plan Execute Lite

## Workflow
1. Parse plan into ordered tasks (respect dependencies).
2. For each task: branch or worktree → implement → run targeted tests → commit.
3. After stack: push, open draft PR(s), paste verification evidence.
4. Defer risky shared-state actions until user confirms.

## Not for
- 20-PR Graphite stacks (use product execute-plan)
- Pure review (use draft-cold-review / check-work)
