#!/bin/bash
# Bidirectional mirror between ~/.grok/skills and this catalog's imported/.
# Default: local is source of truth for existing skills; catalog-only skills
# are installed locally. Then both trees match by skill name.

set -euo pipefail

CATALOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCAL="${HOME}/.grok/skills"
IMPORTED="$CATALOG_DIR/imported"

# Optional category map (default: custom)
category_for() {
  case "$1" in
    dtn-bpv7-expert|ipnsig-solar-system-internet|probabilistic-routing-debugger) echo dtn ;;
    statistical-analyst|check-work|code-review|create-skill|update|fastfetch|help|imagine) echo engineering ;;
    goal-verifier|self-refine-loop|skill-evolver) echo meta ;;
    litreview|research) echo research ;;
    patent-drawings|patent-evidence-package|patent-specification) echo patent ;;
    patent-slm|abliteration) echo models ;;
    hacker|bbp-video-poc|webkit-png-rce|1password-security-design|cvss-v3.1-spec|pwnow|sudo) echo security ;;
    pcb-design|n64-texture-video-mod) echo hardware ;;
    rocket-science) echo science ;;
    gaming-video-tap) echo ops ;;
    *) echo custom ;;
  esac
}

mkdir -p "$LOCAL" "$IMPORTED"

echo "=== Local → catalog ==="
for skill in "$LOCAL"/*; do
  [ -d "$skill" ] || continue
  [ -f "$skill/SKILL.md" ] || continue
  name="$(basename "$skill")"
  if [ -L "$skill" ]; then
    src="$(readlink -f "$skill")"
  else
    src="$skill"
  fi
  catg="$(category_for "$name")"
  dest="$IMPORTED/$catg/$name"
  mkdir -p "$(dirname "$dest")"
  rsync -a --delete --exclude '.git' "$src/" "$dest/"
  echo "  ✓ $name → imported/$catg/$name"
done

echo ""
echo "=== Catalog → local (fill gaps / refresh) ==="
for skill_dir in "$IMPORTED"/*/*; do
  [ -d "$skill_dir" ] || continue
  [ -f "$skill_dir/SKILL.md" ] || continue
  name="$(basename "$skill_dir")"
  target="$LOCAL/$name"
  if [ -L "$target" ]; then
    rm -f "$target"
  fi
  mkdir -p "$target"
  rsync -a --delete --exclude '.git' "$skill_dir/" "$target/"
  echo "  ✓ $name"
done

echo ""
echo "Local:   $(find "$LOCAL" -mindepth 1 -maxdepth 1 -type d | wc -l) dirs"
echo "Catalog: $(find "$IMPORTED" -name SKILL.md | wc -l) SKILL.md"
