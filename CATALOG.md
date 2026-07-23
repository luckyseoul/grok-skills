# Grok Skills Catalog — Master Record

This is the single living document for all external skills we know about.

Format for entries:

- **Fully Imported**: Copied into `~/.grok/skills/` and `imported/`. Ready to use immediately.
- **Reference Only**: Precise activation instructions. Clone/copy only when needed this session.

---

## Fully Imported Skills

(These live in `~/.grok/skills/` and have copies under `imported/`)

### statistical-analyst
- **Source**: alirezarezvani/claude-skills (engineering category)
- **Imported**: 2026-05-27
- **Tuned**: Yes — heavily adapted description + context for DTN/BPv7 simulation results (delivery ratios, latency, rate-aware metrics, pre-warm effects, adversarial topology, 5x/10x batteries).
- **Why promoted**: Directly supports rigorous statistical analysis of the current experiment campaign for draft-perry-dtn-cpb.

### dtn-bpv7-expert
- **Created locally**: 2026-05-27 as part of RFC library + DTN expertise initiative
- **Purpose**: World-class expert that *always* grounds answers in the local `~/.grok/ietf-rfcs/` library for citation accuracy. Deep knowledge of BPv7 (9171), BPSec (9172), rate-aware/CPB extensions, errata, and the current draft work.
- **Companion**: Works extremely well with `statistical-analyst` when turning simulation numbers into defensible IETF claims.

### litreview (partial)
- **Source**: alirezarezvani/claude-skills
- **Status**: Support files present; full workflow depends on external Consensus MCP + docx tooling. Kept for future use on literature grounding of the draft.

### goal-verifier (`imported/meta/`)
- **Created locally**: 2026-07-23
- **Purpose**: Goal restatement + acceptance criteria + evidence-based PASS/FAIL (pairs with `check-work` for code focus).
- **Triggers**: verify goal, confirm success, did we finish, /goal-verifier

### self-refine-loop (`imported/meta/`)
- **Created locally**: 2026-07-23
- **Purpose**: On-demand generator→critique→revise loop (max 5 iters, score ≥8 stop). Strict triggers only.
- **Triggers**: self-refine, critique and revise, polish this draft, /self-refine-loop

### skill-evolver (`imported/meta/`)
- **Created locally**: 2026-07-23
- **Purpose**: Upgrade existing skills to house quality with versioned backups + 10-dimension rubric (`references/evolution-guide.md`).
- **Triggers**: evolve skill, upgrade SKILL.md, /skill-evolver

### abliteration (`imported/models/`)
- **Created locally**: 2026-07-23
- **Purpose**: Rare, ethically gated local-model refusal-direction orthogonalization for over-refusal on legitimate technical/patent/lab work. Soulkiller paths in `references/local-paths.md`.
- **Triggers**: abliterate, over-refusal, /abliteration
- **Not for**: everyday chat, API jailbreaks, operational crime assistance

Install notes for the July 2026 meta pack: `imported/meta/README-top-skills-install.md`

---

## Reference-Only Skills (High Potential)

### alirezarezvani/claude-skills (https://github.com/alirezarezvani/claude-skills)

One of the highest signal collections (~329 skills + tools as of late May 2026).

**Notable high-value skills to consider importing when relevant:**

- Engineering / Architecture skills
- Security auditor + review skills
- Research & synthesis skills
- Self-improving agent / meta skills
- Orchestration / multi-agent patterns
- C-level / strategic advisory personas (surprisingly useful for prioritization)

**Activation for any specific skill**:
```bash
git clone https://github.com/alirezarezvani/claude-skills.git /tmp/claude-skills
cp -r /tmp/claude-skills/skills/<category>/<skill-name> ~/.grok/skills/<skill-name>
# Then optionally tune the `description` frontmatter for better Grok auto-triggering
```

See `sources/alirezarezvani-claude-skills.md` for more detailed mapping.

### OpenClaw Skills (via awesome list + ClawHub)

Curated list: https://github.com/VoltAgent/awesome-openclaw-skills

Registry: clawhub.ai / clawskills.sh

**Categories worth watching**:
- Coding Agents & IDEs (very large section)
- Browser & Automation
- Git & GitHub
- Search & Research
- Security & Passwords
- Productivity & Tasks

**Activation**:
Use the awesome list to find the specific skill page on ClawHub, then follow the per-skill install instructions (many support direct git or `clawhub install`).

For manual:
```bash
# Most skills live under community contributions or specific GitHub repos linked from the awesome list
```

See `sources/openclaw.md` for current best entry points.

### Hermes Agent Skills

Main repo: https://github.com/NousResearch/hermes-agent

Compatible pack: alirezarezvani/claude-skills (has Hermes sync scripts)

Hermes has particularly strong support for **self-generated and self-improving skills**.

**Activation pattern** similar to above.

---

## Other Notable Sources

- Anthropic's official skills: https://github.com/anthropics/skills
- agentskills.io specification + examples: https://agentskills.io
- Composio skills pack (excellent for tool integrations): https://github.com/ComposioHQ/skills

---

## New Local Infrastructure (2026-05-27)

### IETF/RFC Library
- **Location**: `~/.grok/ietf-rfcs/`
- **Purpose**: Authoritative offline copies of RFCs + drafts to eliminate citation drift and hallucinated references.
- **Current holdings**:
  - Core DTN/BPv7 family: RFC 9171, 9172, 9174, 8949 (CBOR), 5050 (full txt + xml)
  - Style & GitHub process: RFC 7322, 8874, 8875 + living guides (authors.ietf.org, RFC Editor style)
  - **XML coding guide** (most important for writing the draft): RFC 7991 (the xml2rfc v3 vocabulary) + 7992–7996 + full `external/xml2rfc/` clone from ietf-tools
  - External references: full `external/cbor2/` clone (deterministic encoding docs)
- **Tools**: `tools/fetch-rfc` and `tools/fetch-draft`
- **Expert layer**: `dtn-bpv7-expert` skill (see Fully Imported above) — now also routes XML authoring, CBOR determinism, and GitHub process questions to the right local files
- **Catalog**: `CATALOG.md` inside the library tracks retrieval dates and errata status.

This directly addresses the problem of web searches mixing versions and breaking proper IETF citations.

---

## Usage Notes

- When we decide a reference skill is now "good", move it from this section to Fully Imported and actually copy the files.
- Always record **why** we imported or referenced something (context from the chat where it became useful).
- For skills we adapt (especially tuning the `description` field for Grok), keep the original in `imported/<original-name>/` and the adapted version in `~/.grok/skills/`.

See `references/example-security-auditor.md` for the exact format we use for reference-only entries.

Last updated: 2026-05-27 (initial catalog setup)

## Fully Imported (Project-Specific)

### probabilistic-routing-debugger
- **Location**: imported/dtn/probabilistic-routing-debugger/
- **Added**: 2026-05-27
- **Purpose**: Helps troubleshoot why probabilistic protocols (PROPHET, Spray) produce results that are too similar to cpb/cpb-risk or each other in rate-aware adversarial simulations. Focuses on contact-plan dominance, probability calculation issues, spray counter behavior, and interaction with confidence/rate costing.
- **Context**: Created during analysis of the soulkiller 5heavy 5x runs where cpb / cpb-risk / spray showed nearly identical delivery and latency numbers.
