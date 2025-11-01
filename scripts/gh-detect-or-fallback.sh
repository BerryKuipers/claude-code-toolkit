#!/usr/bin/env bash
set -Eeuo pipefail

# Add gh CLI to PATH if installed locally
export PATH="$HOME/.local/bin:$PATH"

STATE_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/.state/can_gh"

# Check if state file exists
if [ ! -f "$STATE_FILE" ]; then
  # State file doesn't exist yet - check if gh is installed and working
  if command -v gh >/dev/null 2>&1 && gh auth status -h github.com >/dev/null 2>&1; then
    # gh is available and authenticated, but state file wasn't created yet
    echo "✅ gh CLI available and authenticated"
  else
    # gh is not available or not authenticated, but this might be during initial setup
    # Don't show warning - let the installation hooks complete first
    exit 0
  fi
  exit 0
fi

CAN_GH=$(cat "$STATE_FILE")

if [ "$CAN_GH" = "1" ]; then
  echo "✅ gh CLI available and authenticated"
else
  echo "⚠️  gh CLI not available - fallback to curl for GitHub API"
  echo ""
  echo "💡 Example fallback commands:"
  echo "   # List issues"
  echo "   curl -H \"Authorization: token \$GH_TOKEN\" \\"
  echo "     https://api.github.com/repos/\$OWNER/\$REPO/issues?state=open"
  echo ""
  echo "   # Get issue details"
  echo "   curl -H \"Authorization: token \$GH_TOKEN\" \\"
  echo "     https://api.github.com/repos/\$OWNER/\$REPO/issues/123"
fi
