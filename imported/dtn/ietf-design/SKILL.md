---
name: ietf-design
description: >
  Author and cold-review an Internet-Draft / protocol design note: problem,
  requirements, wire format, security, experiment plan, open questions.
  Use when the user wants an I-D outline, design for a BPv7 extension, DTN
  protocol feature, or "/ietf-design". Distinct from product /design (app PR plans).
version: 1.0.0
author: luckyseoul
license: MIT
---

# IETF / Protocol Design Skill

## When to use
- New or revised Internet-Draft sections
- BPv7 extension or DTN routing design
- Experiment plan for Experimental-track documents

## Do **not** use
- Application PR DAGs → product `/design` + `/execute-plan` if available
- Pure code review → `/check-work` or `code-review`

## Workflow
1. Restate **problem** and non-goals (one paragraph).
2. Capture **requirements language** (MUST/SHOULD/MAY) candidates.
3. Draft structure: Abstract, Intro, Wire format, Ops, Security, IANA, Experiment, Open questions.
4. Run a **skeptic pass**: contradictions, unshipped claims, dead paths, sim vs draft.
5. Output: markdown design note + checklist of open items for Standards Track vs Experimental.

## Grounding
- Prefer local `~/.grok/ietf-rfcs/` and `dtn-bpv7-expert` for normative claims.
- Prefer `statistical-analyst` for experiment sizing claims.
