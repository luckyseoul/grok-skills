#!/bin/bash
# Install / refresh Grok skills from this catalog into ~/.grok/skills.
# Safe: does not delete skills that are not in the catalog.
# Uses real directory copies (not symlinks) so the machine keeps working
# if the catalog clone moves.

set -euo pipefail

CATALOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SKILLS="${HOME}/.grok/skills"
TARGET_IETF="${HOME}/.grok/ietf-rfcs"

echo "=== Grok skills setup ==="
echo "Catalog: $CATALOG_DIR"
echo "Target:  $TARGET_SKILLS"
echo ""

mkdir -p "$TARGET_SKILLS"

installed=0
for skill_dir in "$CATALOG_DIR/imported"/*/*; do
  [ -d "$skill_dir" ] || continue
  [ -f "$skill_dir/SKILL.md" ] || continue
  skill_name="$(basename "$skill_dir")"
  target="$TARGET_SKILLS/$skill_name"

  # Replace symlink leftovers with real trees
  if [ -L "$target" ]; then
    rm -f "$target"
  fi

  mkdir -p "$target"
  rsync -a --delete \
    --exclude '.git' \
    "$skill_dir/" "$target/"
  echo "  ✓ $skill_name"
  installed=$((installed + 1))
done

echo ""
echo "Installed/refreshed $installed skills into $TARGET_SKILLS"

if [ -d "$CATALOG_DIR/ietf-rfcs" ]; then
  echo ""
  if [ -t 0 ]; then
    read -r -p "Also install IETF/RFC library from catalog? [y/N] " reply
  else
    reply=N
  fi
  if [[ "${reply:-}" =~ ^[Yy]$ ]]; then
    mkdir -p "$TARGET_IETF"
    rsync -a --delete "$CATALOG_DIR/ietf-rfcs/" "$TARGET_IETF/"
    echo "  ✓ IETF library → $TARGET_IETF"
  fi
elif [ -d "$TARGET_IETF" ]; then
  echo ""
  echo "IETF library already present at $TARGET_IETF (not in this catalog clone)."
fi

echo ""
echo "Done. Restart Grok (or wait for skill auto-reload) to pick up changes."
echo "Mirror local → GitHub later with: ./tools/mirror-skills.sh"
