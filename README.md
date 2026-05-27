# Grok Skills Catalog

Local curated collection of high-quality external skills (primarily from the open `agentskills.io` / SKILL.md ecosystem).

**Goal**: Get the benefits of thousands of community skills with minimal bloat and minimal friction.

## Core Policy (User Directive)

- **Good / frequently useful skills** → Fully copy them locally into `~/.grok/skills/<name>/`. Treat them as first-class local skills.
- **Minimally used / niche / one-off skills** → Do **not** copy the whole thing. Add a precise reference entry instead (repo + path + one-line activation command).
- Always keep a living record here so we never have to re-research "where did that great X skill live?"

This catalog is the single source of truth for "what external skills do we know about and how do we activate them quickly."

## Directory Layout

```
~/.grok/skills-catalog/
├── README.md                 # This file
├── CATALOG.md                # Master index + activation instructions
├── sources/                  # One file per upstream collection
│   ├── alirezarezvani-claude-skills.md
│   ├── openclaw.md
│   └── hermes.md
├── imported/                 # Full copies of skills we decided are "good"
│   └── <category>/
│       └── <skill-name>/
├── references/               # Detailed reference notes for minimally-used skills
├── tools/                    # Helper scripts
│   └── import-from-catalog
└── .git/
```

## Workflow

### When you find or want a new skill
1. Evaluate quality and usefulness in the current context.
2. Decision:
   - **High value / reusable across chats** → Fully import it (see below).
   - **Niche / used once this session** → Add a clean reference entry only.

### Fully importing a good skill
```bash
# Example
cp -r /path/to/upstream/some-great-skill ~/.grok/skills/some-great-skill
# Also keep a pristine copy here for provenance
cp -r /path/to/upstream/some-great-skill ~/.grok/skills-catalog/imported/engineering/some-great-skill
```

Then update `CATALOG.md` under the "Fully Imported" section.

### Adding a reference-only skill
Add an entry to `CATALOG.md` (and optionally a file in `references/`) with:
- Exact source (git URL + commit or branch if possible)
- Path inside the repo
- One-line activation command
- Why we kept it as reference only

### Using skills from this catalog
- For fully imported ones: just use `/skill-name` or let Grok auto-trigger based on the description.
- For reference-only ones: the catalog tells you the exact clone/copy command. Run it, then use.

## Recommended Upstream Sources (as of 2026)

- **alirezarezvani/claude-skills** — ~329 high-quality, production-oriented skills. Excellent engineering, security, research, and orchestration content. Uses the agentskills.io standard.
- **OpenClaw ecosystem** (via VoltAgent/awesome-openclaw-skills + ClawHub) — Massive volume (5k+ curated). Great for automation, browser, productivity, etc.
- **Hermes Agent skills** (NousResearch/hermes-agent + compatible packs)
- **agentskills.io** official examples and Anthropic's skills repo

## Maintenance

- This repo should be committed and can be cloned/pushed to a real remote if you want it across machines.
- When upstreams release big updates, re-evaluate top skills and re-import improved versions.
- Periodically review `CATALOG.md` for skills that have become "good enough" to fully import.

## Philosophy

We are not trying to own every skill in the universe. We are ruthlessly curating the ones that give us real leverage in our actual work, while keeping perfect traceability for everything else.

"Copy the good ones. Reference the rest. Never lose the thread."
