#!/bin/bash
# Bootstrap Claude Code Toolkit in a target repository
# Run this ONCE after adding the toolkit as a submodule
#
# Usage (from your project root):
#   .claude-toolkit/scripts/bootstrap.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
TOOLKIT_DIR="$PROJECT_DIR/.claude-toolkit"

echo "🚀 Bootstrapping Claude Code Toolkit..."
echo "   Project: $PROJECT_DIR"

# Verify toolkit exists
if [ ! -d "$TOOLKIT_DIR" ]; then
  echo "❌ Toolkit not found at $TOOLKIT_DIR"
  echo "   First add the toolkit as a submodule:"
  echo "   git submodule add https://github.com/BerryKuipers/claude-code-toolkit .claude-toolkit"
  exit 1
fi

# Create .claude directory if needed
mkdir -p "$PROJECT_DIR/.claude"

# Create/update settings.json with SessionStart hook for sync
SETTINGS_FILE="$PROJECT_DIR/.claude/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
  echo "  ⚠️  .claude/settings.json exists - backing up to settings.json.bak"
  cp "$SETTINGS_FILE" "$SETTINGS_FILE.bak"
fi

cat > "$SETTINGS_FILE" << 'EOF'
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'cd \"$(git rev-parse --show-toplevel)\" && bash .claude-toolkit/scripts/sync-claude-toolkit.sh'"
          },
          {
            "type": "command",
            "command": "bash -c 'cd \"$(git rev-parse --show-toplevel)\" && bash scripts/install-gh-cli.sh'"
          }
        ]
      }
    ]
  }
}
EOF

echo "  ✅ Created .claude/settings.json with sync hook"

# Run initial sync
echo ""
echo "  → Running initial sync..."
"$TOOLKIT_DIR/scripts/sync-claude-toolkit.sh"

echo ""
echo "✅ Bootstrap complete!"
echo ""
echo "Next steps:"
echo "  1. Commit the changes: git add .claude scripts && git commit -m 'feat: Bootstrap Claude Code Toolkit'"
echo "  2. Push to remote"
echo "  3. Start a new Claude Code session - toolkit will auto-sync on SessionStart"
