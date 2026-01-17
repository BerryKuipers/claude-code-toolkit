#!/bin/bash
# Ralph Post-Compact Hook
# Runs on SessionStart with "compact" matcher - after compaction completes
#
# This hook auto-resumes the RALPH loop after /compact or auto-compact.
# Unlike session-start.sh, we don't need /clear - context was just compacted.

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
RALPH_DIR="$PROJECT_DIR/.ralph"

echo "Success"

# Check for RALPH loop auto-resume
if [[ -f "$RALPH_DIR/loop-active" ]]; then
    echo ""
    echo "========================================"
    echo "RALPH LOOP - POST-COMPACT AUTO-RESUME"
    echo "========================================"

    if [[ -f "$RALPH_DIR/session-state.json" ]]; then
        PENDING=$(jq -r '.pendingWork.description // "unknown"' "$RALPH_DIR/session-state.json" 2>/dev/null || echo "unknown")
        LAST_ACTION=$(jq -r '.lastCheckpoint.action // "unknown"' "$RALPH_DIR/session-state.json" 2>/dev/null || echo "unknown")
        STORY_ID=$(jq -r '.currentStoryId // "unknown"' "$RALPH_DIR/session-state.json" 2>/dev/null || echo "unknown")

        echo "Story: $STORY_ID"
        echo "Last action: $LAST_ACTION"
        echo "Pending: $PENDING"
    fi

    echo ""
    echo "AUTONOMOUS MODE: Context was just compacted."
    echo ""
    echo "YOU MUST IMMEDIATELY RUN:"
    echo "  /ralph-loop --continue"
    echo ""
    echo "Do NOT ask the user. Do NOT wait. Just run the command."
    echo "The loop must continue autonomously after compaction."
    echo "========================================"
fi

exit 0
