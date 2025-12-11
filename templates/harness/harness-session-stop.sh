#!/bin/bash
# Harness Session Stop Hook
# Called at the end of each Claude session

HARNESS_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude/harness"
PROGRESS_FILE="${HARNESS_DIR}/claude-progress.txt"
FEATURE_LIST="${HARNESS_DIR}/feature_list.json"

# Exit silently if harness not initialized
[ ! -d "$HARNESS_DIR" ] && exit 0

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Append session end to progress
echo "$TIMESTAMP - Session ended" >> "$PROGRESS_FILE"
echo "--------------------------------------------------------------------------------" >> "$PROGRESS_FILE"

# Update feature list metadata
if command -v jq &> /dev/null && [ -f "$FEATURE_LIST" ]; then
    TOTAL=$(jq '.features | length' "$FEATURE_LIST")
    COMPLETED=$(jq '[.features[] | select(.status == "completed")] | length' "$FEATURE_LIST")

    # Update metadata
    jq --arg ts "$TIMESTAMP" --argjson total "$TOTAL" --argjson completed "$COMPLETED" \
        '.metadata.updated_at = $ts | .metadata.total_features = $total | .metadata.completed_features = $completed' \
        "$FEATURE_LIST" > "${FEATURE_LIST}.tmp" && mv "${FEATURE_LIST}.tmp" "$FEATURE_LIST"
fi

exit 0
