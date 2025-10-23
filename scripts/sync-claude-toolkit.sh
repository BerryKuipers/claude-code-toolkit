#!/bin/bash
# Sync Claude Code Toolkit to .claude/
# Cross-platform: works on Linux, Mac, and Windows (via Git Bash)
# Runs on SessionStart to keep toolkit in sync

set -e

# Detect project directory (works in SessionStart and manual runs)
if [ -n "$CLAUDE_PROJECT_DIR" ]; then
  PROJECT_DIR="$CLAUDE_PROJECT_DIR"
else
  # Fallback: script directory parent
  PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
fi

TOOLKIT_DIR="$PROJECT_DIR/.claude-toolkit/.claude"
TARGET_DIR="$PROJECT_DIR/.claude"

echo "🔄 Syncing Claude Code Toolkit..."

# Check if toolkit exists
if [ ! -d "$TOOLKIT_DIR" ]; then
  echo "⚠️  Toolkit not found, skipping sync"
  exit 0
fi

# Update submodule (pull latest from toolkit repo)
cd "$CLAUDE_PROJECT_DIR"
if [ -d ".git" ] && [ -f ".gitmodules" ]; then
  echo "  → Updating toolkit submodule..."
  git submodule update --init --remote .claude-toolkit 2>/dev/null || true
fi

# Sync universal files from toolkit
echo "  → Syncing agents..."
rsync -a --delete "$TOOLKIT_DIR/agents/" "$TARGET_DIR/agents/" 2>/dev/null || \
  cp -rf "$TOOLKIT_DIR/agents" "$TARGET_DIR/"

echo "  → Syncing commands..."
rsync -a --delete "$TOOLKIT_DIR/commands/" "$TARGET_DIR/commands/" 2>/dev/null || \
  cp -rf "$TOOLKIT_DIR/commands" "$TARGET_DIR/"

echo "  → Syncing skills..."
rsync -a --delete "$TOOLKIT_DIR/skills/" "$TARGET_DIR/skills/" 2>/dev/null || \
  cp -rf "$TOOLKIT_DIR/skills" "$TARGET_DIR/"

echo "  → Syncing API skills..."
rsync -a --delete "$TOOLKIT_DIR/api-skills-source/" "$TARGET_DIR/api-skills-source/" 2>/dev/null || \
  cp -rf "$TOOLKIT_DIR/api-skills-source" "$TARGET_DIR/"

echo "  → Syncing prompts..."
rsync -a --delete "$TOOLKIT_DIR/prompts/" "$TARGET_DIR/prompts/" 2>/dev/null || \
  cp -rf "$TOOLKIT_DIR/prompts" "$TARGET_DIR/"

# Don't overwrite project-specific files
echo "  → Preserving project-specific files (settings.json, config.yml)"

echo "✅ Toolkit synced successfully!"
