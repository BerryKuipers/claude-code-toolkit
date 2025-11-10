#!/bin/bash
# Sync Claude Code Toolkit to .claude/
# Cross-platform: works on Linux, Mac, and Windows (via Git Bash)
# Runs on SessionStart to keep toolkit in sync

set -e

# Detect project directory (works in SessionStart and manual runs)
if [ -n "$CLAUDE_PROJECT_DIR" ]; then
  PROJECT_DIR="$CLAUDE_PROJECT_DIR"
else
  # Fallback: script directory parent (script is at .claude-toolkit/scripts/)
  PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
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
# Note: SessionStart hook runs this first, but we include fallback for robustness
cd "$PROJECT_DIR"
if [ -d ".git" ] && [ -f ".gitmodules" ]; then
  echo "  → Updating toolkit submodule..."

  # Try to detect local proxy configuration from origin URL
  ORIGIN_URL=$(git config --local remote.origin.url 2>/dev/null || echo "")
  if [[ "$ORIGIN_URL" =~ local_proxy@127\.0\.0\.1:([0-9]+) ]]; then
    PROXY_PORT="${BASH_REMATCH[1]}"
    PROXY_BASE="http://local_proxy@127.0.0.1:$PROXY_PORT/git"

    # Try to reconfigure submodule to use local proxy
    SUBMODULE_URL=$(git config --file .gitmodules submodule..claude-toolkit.url 2>/dev/null || echo "")
    if [[ "$SUBMODULE_URL" =~ github\.com/([^/]+)/([^/]+)(\.git)? ]]; then
      OWNER="${BASH_REMATCH[1]}"
      REPO="${BASH_REMATCH[2]}"
      LOCAL_URL="$PROXY_BASE/$OWNER/$REPO"

      echo "  → Attempting to use local proxy: $LOCAL_URL"
      git config submodule..claude-toolkit.url "$LOCAL_URL" 2>/dev/null || true
    fi
  fi

  # Try to update submodule
  if git submodule update --init --remote .claude-toolkit 2>&1 | grep -q -E "403|502|fatal|unable to access|not authorized"; then
    echo "  ⚠️  Submodule update blocked - using existing toolkit version"
  elif git submodule update --init --remote .claude-toolkit 2>/dev/null; then
    echo "  ✅ Toolkit submodule updated"
  else
    echo "  ⚠️  Submodule update failed - using existing toolkit version"
  fi
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
