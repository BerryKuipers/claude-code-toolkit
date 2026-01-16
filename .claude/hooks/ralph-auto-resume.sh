#!/bin/bash
# Ralph Loop Auto-Resume Hook
# Event: SessionStart
#
# Checks for active ralph loop and pending PRD stories.
# If found, outputs continuation prompt for ralph-loop-internal.

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
PRD_FILE="${PROJECT_DIR}/.ralph/prd.json"
LOOP_ACTIVE_FILE="${PROJECT_DIR}/.ralph/loop-active"
PROGRESS_FILE="${PROJECT_DIR}/.ralph/progress.txt"
INSTRUCTIONS_FILE="${PROJECT_DIR}/.ralph/instructions.md"

# Silent exit if ralph loop not active
[ ! -f "$LOOP_ACTIVE_FILE" ] && exit 0

# Silent exit if no PRD
[ ! -f "$PRD_FILE" ] && exit 0

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "WARNING: jq not found, ralph loop cannot parse PRD"
    exit 0
fi

# Count incomplete stories
INCOMPLETE_COUNT=$(jq '[.userStories[] | select(.passes == false)] | length' "$PRD_FILE" 2>/dev/null || echo "0")
TOTAL_COUNT=$(jq '.userStories | length' "$PRD_FILE" 2>/dev/null || echo "0")
COMPLETED_COUNT=$((TOTAL_COUNT - INCOMPLETE_COUNT))

# If all stories complete, disable loop
if [ "$INCOMPLETE_COUNT" -eq 0 ]; then
    rm -f "$LOOP_ACTIVE_FILE"

    echo ""
    echo "======================================"
    echo " RALPH LOOP COMPLETE"
    echo "======================================"
    echo "All $TOTAL_COUNT user stories passed!"
    echo ""
    echo "PRD: $PRD_FILE"
    echo "Progress: $PROGRESS_FILE"
    echo "======================================"
    exit 0
fi

# Get next story info
NEXT_STORY=$(jq -r '[.userStories[] | select(.passes == false)][0]' "$PRD_FILE")
STORY_ID=$(echo "$NEXT_STORY" | jq -r '.id // "unknown"')
STORY_TITLE=$(echo "$NEXT_STORY" | jq -r '.title // "untitled"')
STORY_EXECUTOR=$(echo "$NEXT_STORY" | jq -r '.executor // ""')

# Check for BLOCKED or MANUAL_REQUIRED in last story's notes
LAST_NOTES=$(jq -r '.userStories[-1].notes // ""' "$PRD_FILE")
if echo "$LAST_NOTES" | grep -qiE "BLOCKED|MANUAL_REQUIRED"; then
    rm -f "$LOOP_ACTIVE_FILE"

    echo ""
    echo "======================================"
    echo " RALPH LOOP BLOCKED"
    echo "======================================"
    echo "Manual intervention required."
    echo "Last notes: $LAST_NOTES"
    echo ""
    echo "Review the PRD and resolve the issue."
    echo "Then restart with: /ralph-loop-internal"
    echo "======================================"
    exit 0
fi

# Output continuation prompt
echo ""
echo "======================================"
echo " RALPH LOOP CONTINUATION"
echo "======================================"
echo "Progress: $COMPLETED_COUNT / $TOTAL_COUNT stories complete"
echo ""
echo "Next story: $STORY_ID - $STORY_TITLE"
if [ -n "$STORY_EXECUTOR" ]; then
    echo "Executor hint: $STORY_EXECUTOR"
fi
echo ""
echo "PRD: $PRD_FILE"
if [ -f "$INSTRUCTIONS_FILE" ]; then
    echo "Instructions: $INSTRUCTIONS_FILE (delegation policy active)"
fi
echo ""
echo "To stop: /ralph-loop-internal --stop"
echo "======================================"
echo ""
echo "Resuming ralph loop..."
echo ""

# Output the continuation command for Claude to execute
echo ">>> AUTO-RESUME: Run /ralph-loop --continue to continue the loop"

exit 0
