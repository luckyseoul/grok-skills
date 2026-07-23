# Grok Skills Catalog — Master Record
_Mirrored 2026-07-23. Local `~/.grok/skills` and this repo stay in sync via `./tools/mirror-skills.sh`._

## Fully mirrored skills (install with `./setup.sh`)

| Skill | Category | Path |
|-------|----------|------|
| `dtn-bpv7-expert` | dtn | `imported/dtn/dtn-bpv7-expert/` |
| `ipnsig-solar-system-internet` | dtn | `imported/dtn/ipnsig-solar-system-internet/` |
| `probabilistic-routing-debugger` | dtn | `imported/dtn/probabilistic-routing-debugger/` |
| `check-work` | engineering | `imported/engineering/check-work/` |
| `code-review` | engineering | `imported/engineering/code-review/` |
| `create-skill` | engineering | `imported/engineering/create-skill/` |
| `fastfetch` | engineering | `imported/engineering/fastfetch/` |
| `help` | engineering | `imported/engineering/help/` |
| `imagine` | engineering | `imported/engineering/imagine/` |
| `statistical-analyst` | engineering | `imported/engineering/statistical-analyst/` |
| `update` | engineering | `imported/engineering/update/` |
| `n64-texture-video-mod` | hardware | `imported/hardware/n64-texture-video-mod/` |
| `pcb-design` | hardware | `imported/hardware/pcb-design/` |
| `goal-verifier` | meta | `imported/meta/goal-verifier/` |
| `self-refine-loop` | meta | `imported/meta/self-refine-loop/` |
| `skill-evolver` | meta | `imported/meta/skill-evolver/` |
| `abliteration` | models | `imported/models/abliteration/` |
| `patent-slm` | models | `imported/models/patent-slm/` |
| `gaming-video-tap` | ops | `imported/ops/gaming-video-tap/` |
| `patent-drawings` | patent | `imported/patent/patent-drawings/` |
| `patent-evidence-package` | patent | `imported/patent/patent-evidence-package/` |
| `patent-specification` | patent | `imported/patent/patent-specification/` |
| `litreview` | research | `imported/research/litreview/` |
| `research` | research | `imported/research/research/` |
| `rocket-science` | science | `imported/science/rocket-science/` |
| `1password-security-design` | security | `imported/security/1password-security-design/` |
| `bbp-video-poc` | security | `imported/security/bbp-video-poc/` |
| `cvss-v3.1-spec` | security | `imported/security/cvss-v3.1-spec/` |
| `hacker` | security | `imported/security/hacker/` |
| `pwnow` | security | `imported/security/pwnow/` |
| `sudo` | security | `imported/security/sudo/` |
| `webkit-png-rce` | security | `imported/security/webkit-png-rce/` |

**Count:** 32 skills.

## Layout

- `imported/<category>/<skill>/` — full skill trees (SKILL.md + helpers)
- `tools/mirror-skills.sh` — bidirectional sync with `~/.grok/skills`
- `setup.sh` — install catalog → `~/.grok/skills` (safe; does not delete extras)

## Categories

| Category | Role |
|----------|------|
| dtn | BPv7 / IPNSIG / probabilistic routing |
| engineering | Stats, review, tooling, create-skill |
| meta | Goal verify, self-refine, skill-evolver |
| models | Abliteration, patent-slm |
| patent | USPTO drawings / evidence / spec |
| research | Lit review |
| security | Hacker, CVSS, 1Password, pwnow/sudo |
| hardware | PCB, N64 |
| science | Rocket |
| ops | Gaming video tap |

## Not mirrored here

- Grok **bundled** skills (`~/.grok/bundled/skills/`) — shipped with the product
- Hermes skill packs under `~/.hermes/` — separate agent ecosystem

## External sources (reference only)

See `sources/` and historical notes below for third-party packs (Stijnman, alirezarezvani, OpenClaw). Import deliberately; not auto-installed.
