#!/bin/bash
# Harness Session Start Hook
# Called at the beginning of each Claude session

HARNESS_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/harness"
PROGRESS_FILE="${HARNESS_DIR}/claude-progress.txt"
FEATURE_LIST="${HARNESS_DIR}/feature_list.json"

# Exit silently if harness not initialized
[ ! -d "$HARNESS_DIR" ] && exit 0

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Append session start to progress
echo "" >> "$PROGRESS_FILE"
echo "--------------------------------------------------------------------------------" >> "$PROGRESS_FILE"
echo "$TIMESTAMP - New session started" >> "$PROGRESS_FILE"

# Read feature stats if jq available
if command -v jq &> /dev/null && [ -f "$FEATURE_LIST" ]; then
    TOTAL=$(jq '.metadata.total_features // (.features | length)' "$FEATURE_LIST")
    COMPLETED=$(jq '[.features[] | select(.status == "completed")] | length' "$FEATURE_LIST")
    IN_PROGRESS=$(jq '.features[] | select(.status == "in_progress") | .name' "$FEATURE_LIST" 2>/dev/null | head -1)

    echo "$TIMESTAMP - Feature status: $COMPLETED/$TOTAL completed" >> "$PROGRESS_FILE"

    if [ -n "$IN_PROGRESS" ] && [ "$IN_PROGRESS" != "null" ]; then
        echo "$TIMESTAMP - Resuming: $IN_PROGRESS" >> "$PROGRESS_FILE"
    fi

    # Update metadata
    jq --arg ts "$TIMESTAMP" '.metadata.updated_at = $ts' "$FEATURE_LIST" > "${FEATURE_LIST}.tmp" && mv "${FEATURE_LIST}.tmp" "$FEATURE_LIST"
fi

exit 0
