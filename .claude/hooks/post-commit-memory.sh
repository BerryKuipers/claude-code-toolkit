#!/bin/bash
# Post-commit hook for dev memory updates
# Automatically creates development event records after each commit

# set -e  # Disabled for Windows compatibility

# Check if dev memory is enabled
CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
CONFIG_FILE="$CLAUDE_PROJECT_DIR/.claude/config.yml"

# Default to enabled if config doesn't exist or doesn't specify
ENABLED=true
if [ -f "$CONFIG_FILE" ]; then
  # Check if devMemory.enabled is explicitly set to false. This is more robust
  # than `grep -A 1` as it looks within the entire (simple) YAML block.
  if sed -n '/^devMemory:/,/^[^[:space:]]/p' "$CONFIG_FILE" | grep -q '^\s*enabled:\s*false\b'; then
    ENABLED=false
  fi
fi

if [ "$ENABLED" = false ]; then
  exit 0
fi

# Extract commit information
REPO=$(basename "$(git rev-parse --show-toplevel)")
BRANCH=$(git branch --show-current)
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_SHORT_HASH=$(git rev-parse --short HEAD)
COMMIT_MESSAGE=$(git log -1 --pretty=%B HEAD)
COMMIT_TIMESTAMP=$(git log -1 --format=%aI HEAD)
FILES_CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD | wc -l | tr -d ' ')

# Log update (non-blocking)
echo "→ Updating dev memory for commit $COMMIT_SHORT_HASH..." >&2

# NOTE: The actual dev-memory-update logic would be invoked by Claude Code
# via the skill system. This hook just triggers the notification.
#
# In practice, this hook would call a script that uses Claude Code API
# or invokes the skill through the proper channels.
#
# For now, we create a marker file that Claude can detect and process

MEMORY_DIR="$CLAUDE_PROJECT_DIR/ai_memory"
mkdir -p "$MEMORY_DIR"

# Create a pending update marker (Claude will process this)
PENDING_FILE="$MEMORY_DIR/.pending_updates"
cat >> "$PENDING_FILE" <<EOF
$COMMIT_HASH|$COMMIT_TIMESTAMP|$BRANCH|$REPO|$FILES_CHANGED
EOF

# If this is a manual run (not during a Claude session), log to user
if [ -z "$CLAUDE_SESSION" ]; then
  echo "  ℹ️  Dev memory update pending for commit $COMMIT_SHORT_HASH" >&2
  echo "  ℹ️  Will be processed in next Claude Code session" >&2
fi

exit 0
