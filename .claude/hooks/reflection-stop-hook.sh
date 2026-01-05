#!/bin/bash
# Reflection Stop Hook - Bash Version
# Called on Stop event to log reflection candidates
#
# This hook:
# 1. Checks if reflection logging is enabled for this repo
# 2. Appends a minimal candidate entry to reflection-candidates.jsonl
# 3. Prints a short notification
#
# CRITICAL: This hook NEVER modifies skills/rules or commits. It only logs.

set -e

# Configuration
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CONFIG_FILE="$PROJECT_DIR/.claude/config.yml"
STATE_DIR="$PROJECT_DIR/.claude/state"
CANDIDATES_FILE="$STATE_DIR/reflection-candidates.jsonl"

# Check if reflection is enabled in config.yml
if [ ! -f "$CONFIG_FILE" ]; then
    exit 0
fi

# Check for reflection.enabled: true
if ! grep -A1 '^reflection:' "$CONFIG_FILE" 2>/dev/null | grep -q 'enabled:\s*true'; then
    exit 0
fi

# Ensure state directory exists
mkdir -p "$STATE_DIR"

# Generate session token from cwd + timestamp
SESSION_TOKEN=$(echo "${PROJECT_DIR}-$(date +%Y%m%d)" | sha256sum | cut -c1-16)

# Get current date and generate ID
TODAY=$(date +%Y%m%d)
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Count existing candidates for today to generate sequential ID
EXISTING_COUNT=0
if [ -f "$CANDIDATES_FILE" ]; then
    EXISTING_COUNT=$(grep -c "refl-$TODAY" "$CANDIDATES_FILE" 2>/dev/null || echo 0)
fi
SEQ_NUM=$(printf "%03d" $((EXISTING_COUNT + 1)))
CANDIDATE_ID="refl-$TODAY-$SEQ_NUM"

# Get git info for context
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
COMMIT_HASH=$(git log -1 --pretty=format:"%h" 2>/dev/null || echo "")
COMMIT_MSG=$(git log -1 --pretty=format:"%s" 2>/dev/null || echo "")

# Escape JSON strings
escape_json() {
    echo "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g' | tr -d '\n'
}

ESCAPED_BRANCH=$(escape_json "$BRANCH")
ESCAPED_COMMIT_MSG=$(escape_json "$COMMIT_MSG")

# Create minimal candidate entry (single line JSON)
JSON_LINE=$(cat <<EOF
{"id":"$CANDIDATE_ID","timestamp":"$TIMESTAMP","session_token":"$SESSION_TOKEN","type":"session_end","confidence":"LOW","source":"stop_hook","description":"Session ended on branch: $ESCAPED_BRANCH","evidence":[],"proposed_rule":"","status":"pending","context":{"branch":"$ESCAPED_BRANCH","recent_commit":"$COMMIT_HASH","commit_message":"$ESCAPED_COMMIT_MSG"}}
EOF
)

# Append to candidates file
echo "$JSON_LINE" >> "$CANDIDATES_FILE"

# Print notification
echo ""
echo "-------------------------------------------"
echo " Reflection candidate logged: $CANDIDATE_ID"
echo " Branch: $BRANCH"
echo " Run /reflect to analyze patterns"
echo "-------------------------------------------"

exit 0
