# Grok Skills Catalog — Master Record

This is the single living document for all external skills we know about.

Format for entries:

- **Fully Imported**: Copied into `~/.grok/skills/` and `imported/`. Ready to use immediately.
- **Reference Only**: Precise activation instructions. Clone/copy only when needed this session.

---

## Fully Imported Skills

(These live in `~/.grok/skills/` and have copies under `imported/`)

_None yet — we are just setting up the system._

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

## Usage Notes

- When we decide a reference skill is now "good", move it from this section to Fully Imported and actually copy the files.
- Always record **why** we imported or referenced something (context from the chat where it became useful).
- For skills we adapt (especially tuning the `description` field for Grok), keep the original in `imported/<original-name>/` and the adapted version in `~/.grok/skills/`.

See `references/example-security-auditor.md` for the exact format we use for reference-only entries.

Last updated: 2026-05-27 (initial catalog setup)
