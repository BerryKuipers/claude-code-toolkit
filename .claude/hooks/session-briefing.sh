#!/bin/bash
# Session Briefing - Display dev memory summary on session start
# Called after process-pending-memory.sh

CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
MEMORY_DIR="$CLAUDE_PROJECT_DIR/ai_memory"
EVENTS_FILE="$MEMORY_DIR/events.jsonl"

# Exit silently if no events file
[ ! -f "$EVENTS_FILE" ] && exit 0

# Check if jq is available
if ! command -v jq &> /dev/null; then
  # Fallback: simple tail without jq
  echo "📋 Recent Dev Memory (last 5 commits):"
  tail -5 "$EVENTS_FILE" | while read -r line; do
    echo "  • $line" | sed 's/.*"message":"\([^"]*\)".*/\1/'
  done
  exit 0
fi

# Count events
TOTAL_EVENTS=$(wc -l < "$EVENTS_FILE" | tr -d ' ')
[ "$TOTAL_EVENTS" -eq 0 ] && exit 0

# Get current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

# Get repo name
REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" || basename "$CLAUDE_PROJECT_DIR")

# Get recent events (last 7 days or last 10, whichever is more relevant)
RECENT_EVENTS=$(tail -20 "$EVENTS_FILE")

# Count by type
FEATURES=$(echo "$RECENT_EVENTS" | jq -s '[.[] | select(.type == "feature")] | length')
BUGFIXES=$(echo "$RECENT_EVENTS" | jq -s '[.[] | select(.type == "bugfix")] | length')
REFACTORS=$(echo "$RECENT_EVENTS" | jq -s '[.[] | select(.type == "refactor")] | length')

# Generate briefing
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    📋 SESSION BRIEFING                       ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ Project: $REPO_NAME"
echo "║ Branch:  $CURRENT_BRANCH"
echo "║ Events:  $TOTAL_EVENTS total"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ Recent Activity (last 20 commits):"
echo "║   ✨ Features: $FEATURES | 🐛 Fixes: $BUGFIXES | ♻️ Refactors: $REFACTORS"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║ Latest Changes:"

# Show last 5 events with formatting
tail -5 "$EVENTS_FILE" | jq -r '
  "║   " +
  (if .type == "feature" then "✨"
   elif .type == "bugfix" then "🐛"
   elif .type == "refactor" then "♻️"
   elif .type == "docs" then "📚"
   elif .type == "test" then "🧪"
   else "📝" end) +
  " [" + .hash + "] " + (.message | .[0:50]) + (if (.message | length) > 50 then "..." else "" end)
'

echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

exit 0
