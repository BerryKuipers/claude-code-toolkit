#!/bin/bash
# Sync Claude Code Toolkit to .claude/
# Cross-platform: works on Linux, Mac, and Windows (via Git Bash)
# Runs on SessionStart to keep toolkit in sync

# Error handler - show what failed
trap 'echo "❌ Sync failed at line $LINENO: $BASH_COMMAND"' ERR
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
echo "  → CLAUDE_PROJECT_DIR: ${CLAUDE_PROJECT_DIR:-<not set>}"
echo "  → Git toplevel: $(git rev-parse --show-toplevel 2>/dev/null || echo '<not a git repo>')"
echo "  → Using PROJECT_DIR: $PROJECT_DIR"
echo "  → Toolkit source: $TOOLKIT_DIR"
echo "  → Target .claude: $TARGET_DIR"

# Check if toolkit exists
if [ ! -d "$TOOLKIT_DIR" ]; then
  echo "⚠️  Toolkit not found at: $TOOLKIT_DIR"
  echo "    Does .claude-toolkit submodule exist? Run: git submodule status"
  exit 0
fi
echo "  ✓ Toolkit found"

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

echo "  → Syncing hooks..."
mkdir -p "$TARGET_DIR/hooks"
rsync -a --delete "$TOOLKIT_DIR/hooks/" "$TARGET_DIR/hooks/" 2>/dev/null || \
  cp -rf "$TOOLKIT_DIR/hooks"/* "$TARGET_DIR/hooks/" 2>/dev/null || true
# Make hooks executable
chmod +x "$TARGET_DIR/hooks/"*.sh 2>/dev/null || true

echo "  → Syncing skills..."
rsync -a --delete "$TOOLKIT_DIR/skills/" "$TARGET_DIR/skills/" 2>/dev/null || \
  cp -rf "$TOOLKIT_DIR/skills" "$TARGET_DIR/"

echo "  → Syncing API skills..."
rsync -a --delete "$TOOLKIT_DIR/api-skills-source/" "$TARGET_DIR/api-skills-source/" 2>/dev/null || \
  cp -rf "$TOOLKIT_DIR/api-skills-source" "$TARGET_DIR/"

echo "  → Syncing prompts..."
rsync -a --delete "$TOOLKIT_DIR/prompts/" "$TARGET_DIR/prompts/" 2>/dev/null || \
  cp -rf "$TOOLKIT_DIR/prompts" "$TARGET_DIR/"

echo "  → Syncing rules..."
mkdir -p "$TARGET_DIR/rules"
rsync -a --delete "$TOOLKIT_DIR/rules/" "$TARGET_DIR/rules/" 2>/dev/null || \
  cp -rf "$TOOLKIT_DIR/rules"/* "$TARGET_DIR/rules/" 2>/dev/null || true

# Sync scripts to project scripts directory
SCRIPTS_DEST="$PROJECT_DIR/scripts"
mkdir -p "$SCRIPTS_DEST"

# Copy utility scripts (install-gh-cli.sh, etc.)
UTIL_SCRIPTS_SRC="$PROJECT_DIR/.claude-toolkit/scripts"
echo "  → Syncing utility scripts..."
for script in "$UTIL_SCRIPTS_SRC"/install-*.sh; do
  if [ -f "$script" ]; then
    cp "$script" "$SCRIPTS_DEST/"
    chmod +x "$SCRIPTS_DEST/$(basename "$script")"
  fi
done

# Copy E2E scripts
E2E_SCRIPTS_SRC="$PROJECT_DIR/.claude-toolkit/templates/e2e-scripts"
if [ -d "$E2E_SCRIPTS_SRC" ]; then
  echo "  → Syncing E2E scripts..."
  for script in "$E2E_SCRIPTS_SRC"/*.mjs; do
    if [ -f "$script" ]; then
      cp "$script" "$SCRIPTS_DEST/"
      chmod +x "$SCRIPTS_DEST/$(basename "$script")"
    fi
  done
fi

# ============================================
# Settings.json Hook Configuration
# ============================================
echo "  → Checking settings.json for hook configuration..."

SETTINGS_FILE="$TARGET_DIR/settings.json"
SETTINGS_TEMPLATE="$TOOLKIT_DIR/../templates/settings-with-hooks.json"

# If settings.json doesn't exist, create from template
if [ ! -f "$SETTINGS_FILE" ]; then
  if [ -f "$SETTINGS_TEMPLATE" ]; then
    echo "  → Creating settings.json from template with hooks..."
    cp "$SETTINGS_TEMPLATE" "$SETTINGS_FILE"
  fi
elif [ -f "$SETTINGS_TEMPLATE" ]; then
  # Check if hooks are configured
  if ! grep -q "PreToolUse\|PostToolUse\|UserPromptSubmit" "$SETTINGS_FILE" 2>/dev/null; then
    echo ""
    echo "  ⚠️  HOOKS NOT CONFIGURED in settings.json!"
    echo "     Your code quality enforcement hooks exist but aren't wired up."
    echo ""
    echo "     To enable enforcement, add hooks to your settings.json:"
    echo "     - See template: $SETTINGS_TEMPLATE"
    echo "     - Or run: cp $SETTINGS_TEMPLATE $SETTINGS_FILE"
    echo ""
    echo "     Available hooks in .claude/hooks/:"
    ls -1 "$TARGET_DIR/hooks/"*.sh 2>/dev/null | xargs -I {} basename {} | sed 's/^/       - /'
    echo ""
  fi
fi

# Don't overwrite project-specific files
echo "  → Preserving project-specific files (settings.json, config.yml)"

# ============================================
# Dev Memory Integration
# ============================================
echo "  → Ensuring ai_memory directory exists..."
MEMORY_DIR="$PROJECT_DIR/ai_memory"
mkdir -p "$MEMORY_DIR"

# Create .gitkeep if first time
if [ ! -f "$MEMORY_DIR/.gitkeep" ]; then
  cat > "$MEMORY_DIR/.gitkeep" <<'EOF'
# AI Development Memory

This directory contains automatically generated development memory files:
- events.jsonl - Development events (commits, features, fixes, decisions)
- sessions.jsonl - Coding sessions
- SESSION_BRIEFING.md - Generated session briefings

These files are maintained by the dev-memory-update skill and should be
committed to git to track project history.

For more information, see: .claude-toolkit/docs/dev_memory/
EOF
  echo "  ✅ Created ai_memory directory with .gitkeep"
fi

echo "✅ Toolkit synced successfully!"
