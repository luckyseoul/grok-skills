# Source: alirezarezvani/claude-skills

**Repo**: https://github.com/alirezarezvani/claude-skills  
**Size**: ~329 skills + 30+ agents + 70+ commands + ~400 stdlib-only Python CLI tools  
**Standard**: agentskills.io `SKILL.md` format  
**Last evaluated**: 2026-05-27 (initial cataloging)

## Why This Source Is High Value

- Extremely high signal-to-noise compared to most community collections.
- Strong focus on professional engineering, security, research, and orchestration.
- Includes ready-to-use Python tools (not just prompts).
- Explicitly designed for portability across agents (Claude Code, Hermes, OpenClaw, Cursor, Aider, etc.).
- Actively maintained.

## Recommended Categories for Our Work

- `engineering/` — architecture, code review, refactoring, testing, performance
- `security/` — auditor, threat modeling, review patterns
- `research/` — deep research, synthesis, literature-style analysis
- `orchestration/` — multi-skill / multi-agent coordination
- `meta/` — self-improvement, skill generation, agent reflection
- `productivity/` — task breakdown, prioritization, long-running work tracking

## How to Activate a Specific Skill (Reference)

```bash
# 1. Clone (or update)
git clone https://github.com/alirezarezvani/claude-skills.git /tmp/claude-skills

# 2. Copy the specific skill you want
cp -r /tmp/claude-skills/skills/engineering/<skill-name> ~/.grok/skills/<skill-name>

# 3. (Recommended) Review and tune the description field in SKILL.md
#    for better automatic triggering by Grok

# 4. (Optional but smart) Also save a pristine copy here
cp -r /tmp/claude-skills/skills/engineering/<skill-name> \
   ~/.grok/skills-catalog/imported/engineering/<skill-name>
```

## Current Status in Our Catalog

All skills from this repo are currently **Reference Only**.

We will promote individual skills to Fully Imported only when they prove high value in real work.

## Notes

- Many skills include additional `scripts/`, `references/`, and `tools/` directories — copy the whole skill folder.
- The repo also contains conversion scripts if we ever want to mass-adapt a batch.
- Strong overlap with Hermes Agent (there are sync scripts in the repo).
