# Grok Skills Catalog

**One command on a new laptop:**

```bash
git clone <your-repo-url> ~/.grok/skills-catalog
cd ~/.grok/skills-catalog
./setup.sh
```

Then restart Grok. Your custom skills (dtn-bpv7-expert, statistical-analyst, goal-verifier,
self-refine-loop, skill-evolver, abliteration, pwnow, sudo, etc.) will be available.

---

## What This Gives You

- Your high-value custom skills installed into `~/.grok/skills/`
- Easy access to the local IETF/RFC reference library (optional during setup)
- A single place to manage and version your Grok environment across machines

## Full Setup (New Machine)

```bash
git clone <your-repo-url> ~/.grok/skills-catalog
cd ~/.grok/skills-catalog
./setup.sh
```

The `setup.sh` will ask if you also want the IETF reference library (~21MB).

## Updating Skills Later

After cloning, just pull and re-run setup:

```bash
cd ~/.grok/skills-catalog
git pull
./setup.sh
```

## Structure

- `imported/` — Skills that get installed on every machine
- `references/` — Notes on other useful skills (not auto-installed)
- `setup.sh` — The only script you need to run on new machines
- `CATALOG.md` — Master list of everything tracked here

## For This Project

If you're working on `draft-perry-dtn-cpb`, also run (after cloning the project):

```bash
cd ~/draft-perry-dtn-cpb
./scripts/grok-bootstrap.sh
```

This adds a few extra project-specific skills on top of the catalog.

---

**This repo is your portable Grok environment.** Clone it on any new machine and you're back in business with almost no handholding.
