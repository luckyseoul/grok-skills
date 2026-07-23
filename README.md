# Grok Skills Catalog

Portable mirror of your **user** Grok skills (`~/.grok/skills`).

## New machine

```bash
git clone https://github.com/luckyseoul/grok-skills.git ~/Projects/grok/grok-skills
cd ~/Projects/grok/grok-skills
./setup.sh
```

Restart Grok (or wait for skill auto-reload).

## Keep local and GitHub in sync

After editing skills under `~/.grok/skills` (or after pulling this repo):

```bash
cd ~/Projects/grok/grok-skills
./tools/mirror-skills.sh
git add -A && git status
git commit -m "mirror: refresh skills"
git push
```

## Layout

| Path | Purpose |
|------|---------|
| `imported/<category>/<skill>/` | Full skill trees |
| `setup.sh` | Install catalog → `~/.grok/skills` (safe) |
| `tools/mirror-skills.sh` | Bidirectional local ↔ catalog |
| `CATALOG.md` | Inventory |

## Notes

- **Bundled** product skills live in `~/.grok/bundled/skills/` and are **not** mirrored here.
- `setup.sh` never deletes skills that are only on the machine and not in this catalog.
- DTN work: `dtn-bpv7-expert`, `probabilistic-routing-debugger`, `statistical-analyst`, `ipnsig-solar-system-internet`.
