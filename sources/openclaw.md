# Source: OpenClaw Skills Ecosystem

**Main Project**: https://github.com/openclaw/openclaw  
**Awesome Curated List**: https://github.com/VoltAgent/awesome-openclaw-skills (5,400+ filtered skills)  
**Registry / Installer**: ClawHub (clawhub.ai / clawskills.sh)  
**Standard**: SKILL.md (compatible with agentskills.io)  
**Last evaluated**: 2026-05-27 (initial cataloging)

## Characteristics

- Much higher volume than alirezarezvani/claude-skills.
- Very strong in automation, browser control, productivity, communication, GitHub integration, personal assistant patterns.
- Quality varies more — the awesome list does good filtering.
- Many skills are designed for persistent 24/7 agent operation (Telegram/Discord/etc. interfaces).

## Best Entry Points

1. Browse the categorized awesome list first (highly recommended).
2. Individual skills usually link to their ClawHub page which has install commands and VirusTotal scans.

## Recommended Categories for Engineering / Agent Work

- Coding Agents & IDEs
- Git & GitHub
- Browser & Automation (especially useful for research)
- Search & Research
- Security & Passwords
- CLI Utilities
- Productivity & Tasks

## How to Activate (Reference)

Most skills have per-skill instructions. Common patterns:

```bash
# Via ClawHub CLI (if installed)
clawhub install <skill-slug>

# Manual from GitHub (common)
git clone <specific-skill-repo> /tmp/skill
cp -r /tmp/skill/<skill-dir> ~/.grok/skills/<name>

# Or direct from awesome list links
```

When we find a particularly good one during a session, add the exact activation command to CATALOG.md under Reference Only (or promote to Fully Imported if it earns it).

## Current Status

All OpenClaw skills are currently tracked as **Reference Only** via the awesome list.

We will evaluate and import high-leverage ones (especially anything that complements our heavy autonomous experiment / analysis workflows) on a case-by-case basis.
