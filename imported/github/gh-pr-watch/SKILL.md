---
name: gh-pr-watch
description: >
  Watch one or more GitHub PRs with gh: CI status, review threads, mergeability.
  Fix failures in worktrees; do not force-push without confirmation. Triggers:
  watch PR, babysit PR, PR CI failed, /gh-pr-watch.
version: 1.0.0
author: luckyseoul
license: MIT
---

# GitHub PR Watch

## Prerequisites
- `gh` authenticated, or `GITHUB_TOKEN` for API.

## Commands
```bash
gh pr view <n> --json state,statusCheckRollup,reviews,mergeable
gh pr checks <n>
gh pr diff <n>
gh api repos/{owner}/{repo}/pulls/<n>/comments
```

## Loop
1. List failing checks → open logs → reproduce locally.
2. Fix on a branch/worktree; commit as the user identity; push.
3. Reply to review comments with evidence.
4. Stop when checks green and no unresolved threads (or user stops).

## Hard rules
- No force-push to shared branches without explicit user OK.
- No merge without user OK.
- Prefer PAT/gh over inventing MCP write schemas.
