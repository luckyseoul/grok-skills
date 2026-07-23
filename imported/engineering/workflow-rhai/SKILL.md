---
name: workflow-rhai
description: >
  Author a Grok Build Rhai workflow script (meta, agents, parallel, verify),
  smoke with validate_only, save under .grok/workflows or ~/.grok/workflows.
  Triggers: write a workflow, rhai orchestration, /workflow-rhai.
version: 1.0.0
author: luckyseoul
license: MIT
---

# Workflow Rhai (User Guide)

## Shape
```rhai
let meta = #{
    name: "my-workflow",
    description: "one sentence",
};
// then agent() / parallel() / phase() / complete()
```

## Steps
1. Gather intent and fan-out budget.
2. Author script; keep agent prompts self-contained.
3. `workflow` tool with `validate_only: true` and sample args.
4. Save to `.grok/workflows/<name>.rhai` (project) or `~/.grok/workflows/`.
5. Offer a real run.

For the full host API, also load the product create-workflow skill when present.
