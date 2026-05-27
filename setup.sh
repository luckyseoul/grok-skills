#!/bin/bash
# One-time (or per-machine) setup for your Grok skills environment.
# Run this on a new system after cloning the catalog.

set -e

CATALOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SKILLS="$HOME/.grok/skills"
TARGET_IETF="$HOME/.grok/ietf-rfcs"

echo "=== Setting up Grok skills environment from catalog ==="
echo "Catalog: $CATALOG_DIR"
echo ""

mkdir -p "$TARGET_SKILLS"

echo "Installing high-value skills (symlinked for easy updates)..."
for skill_dir in "$CATALOG_DIR/imported"/*/*; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        target="$TARGET_SKILLS/$skill_name"
        
        # Remove old version if exists
        rm -rf "$target"
        
        # Create symlink
        ln -s "$skill_dir" "$target"
        echo "  ✓ $skill_name (symlinked)"
    fi
done

echo ""
echo "Core skills installed to $TARGET_SKILLS"

# Optional: IETF library
if [ -d "$CATALOG_DIR/ietf-rfcs" ]; then
    echo ""
    read -p "Also symlink the IETF/RFC library (~21MB)? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$TARGET_IETF"
        ln -s "$CATALOG_DIR/ietf-rfcs" "$TARGET_IETF"
        echo "  ✓ IETF library symlinked to $TARGET_IETF"
    fi
fi

echo ""
echo "Done. Restart your Grok session/window for skills to take effect."
echo "You can now use: /dtn-bpv7-expert, statistical-analyst, pwnow, etc."
