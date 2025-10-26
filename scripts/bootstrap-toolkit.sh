#!/bin/bash
# Bootstrap Claude Code Toolkit Submodule
# This script initializes the toolkit submodule when it doesn't exist yet.
# Safe to run on every session start - it's idempotent.
#
# Usage: Called from SessionStart hook in repos that use the toolkit
# Place this script in the parent repo's scripts/ directory

set -e

PROJECT_DIR="$(git rev-parse --show-toplevel)"
TOOLKIT_DIR="$PROJECT_DIR/.claude-toolkit"

echo "🔧 Bootstrapping Claude Code Toolkit..."

# Check if toolkit already exists
if [ -d "$TOOLKIT_DIR/.git" ]; then
  echo "  ✅ Toolkit already initialized"

  # Run the sync script from the toolkit
  if [ -f "$TOOLKIT_DIR/scripts/sync-claude-toolkit.sh" ]; then
    bash "$TOOLKIT_DIR/scripts/sync-claude-toolkit.sh"
  fi
  exit 0
fi

# Toolkit doesn't exist - try to initialize it
echo "  ⚠️  Toolkit not found, attempting initialization..."

# Check if .gitmodules defines the toolkit submodule
if [ ! -f "$PROJECT_DIR/.gitmodules" ]; then
  echo "  ❌ No .gitmodules file found"
  echo "     The toolkit submodule is not configured in this repository."
  exit 0
fi

if ! grep -q "\.claude-toolkit" "$PROJECT_DIR/.gitmodules"; then
  echo "  ❌ Toolkit not configured in .gitmodules"
  echo "     The toolkit submodule is not configured in this repository."
  exit 0
fi

# Try to detect local proxy from origin URL
ORIGIN_URL=$(git config --local remote.origin.url 2>/dev/null || echo "")
TOOLKIT_URL=""

if [[ "$ORIGIN_URL" =~ local_proxy@127\.0\.0\.1:([0-9]+) ]]; then
  PROXY_PORT="${BASH_REMATCH[1]}"
  PROXY_BASE="http://local_proxy@127.0.0.1:$PROXY_PORT/git"

  # Extract toolkit owner/repo from .gitmodules
  SUBMODULE_URL=$(git config --file .gitmodules submodule..claude-toolkit.url 2>/dev/null || echo "")

  if [[ "$SUBMODULE_URL" =~ github\.com/([^/]+)/([^/]+)(\.git)? ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    TOOLKIT_URL="$PROXY_BASE/$OWNER/$REPO"

    echo "  → Using local proxy URL: $TOOLKIT_URL"
  fi
fi

# If no local proxy URL, fall back to original submodule URL
if [ -z "$TOOLKIT_URL" ]; then
  TOOLKIT_URL=$(git config --file .gitmodules submodule..claude-toolkit.url)
  echo "  → Using original URL: $TOOLKIT_URL"
fi

# Try to clone the toolkit
echo "  → Cloning toolkit..."
if git clone --depth 1 "$TOOLKIT_URL" "$TOOLKIT_DIR" 2>/dev/null; then
  echo "  ✅ Toolkit cloned successfully"

  # Initialize as proper submodule
  git submodule init .claude-toolkit 2>/dev/null || true
  git submodule absorbgitdirs 2>/dev/null || true

  # Run the sync script
  if [ -f "$TOOLKIT_DIR/scripts/sync-claude-toolkit.sh" ]; then
    bash "$TOOLKIT_DIR/scripts/sync-claude-toolkit.sh"
  fi

  exit 0
else
  echo "  ❌ Failed to clone toolkit"
  echo ""
  echo "  The toolkit could not be initialized automatically."
  echo "  This is likely due to proxy restrictions in Claude Code web sessions."
  echo ""
  echo "  Workaround: Manually clone the toolkit:"
  echo "  cd $PROJECT_DIR"
  echo "  git clone $TOOLKIT_URL .claude-toolkit"
  echo "  bash .claude-toolkit/scripts/sync-claude-toolkit.sh"
  echo ""
  echo "  ℹ️  The session will continue without the toolkit."
  exit 0
fi
