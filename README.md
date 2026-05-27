# Grok Skills Catalog

**One-command setup on a new machine/window:**

```bash
git clone <your-catalog-remote> ~/.grok/skills-catalog
cd ~/.grok/skills-catalog
./setup.sh
```

Then restart Grok. Your custom skills (dtn-bpv7-expert, statistical-analyst, pwnow, etc.) will be available.

---

## What This Is

A portable, version-controlled home for:
- High-quality skills you've decided to fully import (in `imported/`)
- References to other useful skills you don't want to bloat your environment with (in `references/`)
- The local IETF/RFC reference library (optional, ~21MB)
- Your own custom skills (dtn-bpv7-expert, etc.)

## On a New System

1. Clone this repo to `~/.grok/skills-catalog`
2. Run `./setup.sh`
3. Restart Grok

The setup script symlinks the good skills into `~/.grok/skills/` so Grok picks them up.

## Structure

```
~/.grok/skills-catalog/
├── setup.sh                 # Run this on new machines
├── imported/                # Skills you actively use (symlinked by setup.sh)
├── references/              # "I might need this someday" notes
├── sources/                 # Where things originally came from
├── tools/
│   └── import-from-catalog  # Helper for bringing in new skills
├── CATALOG.md               # Master list of everything
└── README.md
```

## Adding a New Skill

1. Find a good one (alirezarezvani/claude-skills, OpenClaw, etc.)
2. Copy the skill folder into `imported/<category>/<name>/`
3. Update `CATALOG.md`
4. Run `./setup.sh` again (or manually symlink)

## IETF / RFC Library

If you want the full local copy of RFCs, style guides, xml2rfc docs, cbor2, etc.:

```bash
# During setup.sh it will ask
# Or manually:
ln -s ~/.grok/skills-catalog/ietf-rfcs ~/.grok/ietf-rfcs
```

See `ietf-rfcs/CATALOG.md` and `ietf-rfcs/README.md` for what's in there.

## Philosophy

Keep the bloat low. Only fully import things you use constantly. Everything else lives as a precise reference so you can pull it in 10 seconds when you actually need it.

This way you can open Grok on a fresh machine and not feel completely naked.
