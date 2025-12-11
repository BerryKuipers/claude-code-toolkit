#!/bin/bash
# Process pending dev memory updates
# Called on SessionStart and Stop to process commits made outside/during Claude session

CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
MEMORY_DIR="$CLAUDE_PROJECT_DIR/ai_memory"
PENDING_FILE="$MEMORY_DIR/.pending_updates"
EVENTS_FILE="$MEMORY_DIR/events.jsonl"

# Check if there are pending updates
if [ ! -f "$PENDING_FILE" ] || [ ! -s "$PENDING_FILE" ]; then
  exit 0
fi

# Count pending updates
PENDING_COUNT=$(wc -l < "$PENDING_FILE" | tr -d ' ')
if [ "$PENDING_COUNT" -eq 0 ]; then
  exit 0
fi

echo "📝 Processing $PENDING_COUNT pending dev memory update(s)..." >&2

# Process each pending commit
while IFS='|' read -r COMMIT_HASH TIMESTAMP BRANCH REPO FILES_CHANGED; do
  # Skip empty lines
  [ -z "$COMMIT_HASH" ] && continue

  # Get commit message
  COMMIT_MSG=$(git log -1 --pretty=%s "$COMMIT_HASH" 2>/dev/null || echo "Unknown commit")
  COMMIT_MSG_ESCAPED=$(echo "$COMMIT_MSG" | sed 's/"/\\"/g' | tr '\n' ' ')

  # Determine event type from commit message
  EVENT_TYPE="commit"
  if echo "$COMMIT_MSG" | grep -qi "^feat"; then
    EVENT_TYPE="feature"
  elif echo "$COMMIT_MSG" | grep -qi "^fix"; then
    EVENT_TYPE="bugfix"
  elif echo "$COMMIT_MSG" | grep -qi "^refactor"; then
    EVENT_TYPE="refactor"
  elif echo "$COMMIT_MSG" | grep -qi "^docs"; then
    EVENT_TYPE="docs"
  elif echo "$COMMIT_MSG" | grep -qi "^test"; then
    EVENT_TYPE="test"
  fi

  # Get short hash
  SHORT_HASH=$(echo "$COMMIT_HASH" | cut -c1-7)

  # Write event to events.jsonl
  mkdir -p "$MEMORY_DIR"
  echo "{\"timestamp\":\"$TIMESTAMP\",\"type\":\"$EVENT_TYPE\",\"hash\":\"$SHORT_HASH\",\"branch\":\"$BRANCH\",\"repo\":\"$REPO\",\"files_changed\":$FILES_CHANGED,\"message\":\"$COMMIT_MSG_ESCAPED\"}" >> "$EVENTS_FILE"

  echo "  ✓ Recorded: [$SHORT_HASH] $COMMIT_MSG" >&2
done < "$PENDING_FILE"

# Clear pending file after processing
> "$PENDING_FILE"

echo "✅ Dev memory updated" >&2
