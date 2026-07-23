# Installed from top-grok-skills-compiled (curated)

Source menu: `~/top-grok-skills-compiled.md`  
Install date: 2026-07-23  
Bar: house quality ≥ ~70% vs peers (`check-work`, `patent-slm`, `update`).

## Installed (4)

| Skill | Path | Why kept |
|-------|------|----------|
| `goal-verifier` | `~/.grok/skills/goal-verifier/` | Goal/evidence acceptance; pairs with `check-work` |
| `self-refine-loop` | `~/.grok/skills/self-refine-loop/` | Bounded critique loop; strict triggers |
| `skill-evolver` | `~/.grok/skills/skill-evolver/` | Rubric + versioned backups for skill rewrites |
| `abliteration` | `~/.grok/skills/abliteration/` | Rare local over-refusal fix; ethical gate |

## Explicitly not installed (from the top-10 list)

| Skill | Reason |
|-------|--------|
| multi-agent-orchestrator | Phantom deps; Grok workflows/subagents already cover this |
| self-healing-error-recovery | Auto-retry thrash risk on shared GPU |
| agentic-uncertainty-quantifier | Low signal as standalone skill |
| skill-creation-enabler | Duplicates `create-skill` |
| privacy-redactor / hitl-approver | Low ROI without outbound automation wiring |
| deep-search-enabler | Overlaps `litreview` + native web tools |

## Slash / triggers

- `/goal-verifier` — did we finish the goal?
- `/self-refine-loop` — polish this draft (max 5 iters)
- `/skill-evolver` — upgrade an existing SKILL.md
- `/abliteration` — local model refusal orthogonalization (gated)
