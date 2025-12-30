#!/bin/bash
# Loop Session Start Hook
# Checks for pending loop continuation and injects continuation context
#
# This hook runs on SessionStart to:
# 1. Check if there's an active loop that should continue
# 2. Display loop continuation prompt
# 3. Provide context for the next iteration

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
STATE_FILE="${PROJECT_DIR}/.claude/state/loop.local.json"
CONTINUE_FILE="${PROJECT_DIR}/.claude/state/loop.continue"
LOG_FILE="${PROJECT_DIR}/.claude/state/loop.log"

# Silent exit if no continuation pending
[ ! -f "$CONTINUE_FILE" ] && [ ! -f "$STATE_FILE" ] && exit 0

# Check if jq is available
if ! command -v jq &> /dev/null; then
    exit 0
fi

# Check for continuation file (from previous Stop hook)
if [ -f "$CONTINUE_FILE" ]; then
    CONTINUE_LOOP=$(jq -r '.continue_loop // false' "$CONTINUE_FILE")

    if [ "$CONTINUE_LOOP" = "true" ]; then
        ITERATION=$(jq -r '.iteration // 1' "$CONTINUE_FILE")
        TASK=$(jq -r '.task // ""' "$CONTINUE_FILE")
        PROMISE=$(jq -r '.promise // "DONE"' "$CONTINUE_FILE")
        REMAINING=$(jq -r '.remaining_iterations // 0' "$CONTINUE_FILE")

        echo ""
        echo "======================================"
        echo " LOOP CONTINUATION - ITERATION $ITERATION"
        echo "======================================"
        echo "Task: $TASK"
        echo "Remaining iterations: $REMAINING"
        echo "Completion marker: <promise>$PROMISE</promise>"
        echo ""
        echo "To stop this loop: /loop-stop"
        echo "======================================"
        echo ""

        # Clean up continuation file (it's been consumed)
        rm -f "$CONTINUE_FILE"

        # Log continuation
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - Session started, continuing iteration $ITERATION" >> "$LOG_FILE"

        exit 0
    fi
fi

# Check state file for active loop (fallback)
if [ -f "$STATE_FILE" ]; then
    ENABLED=$(jq -r '.enabled // false' "$STATE_FILE")

    if [ "$ENABLED" = "true" ]; then
        ITERATION=$(jq -r '.iteration // 1' "$STATE_FILE")
        TASK=$(jq -r '.original_arguments // ""' "$STATE_FILE")
        MAX_ITER=$(jq -r '.max_iterations // 20' "$STATE_FILE")
        PROMISE=$(jq -r '.completion_promise // "DONE"' "$STATE_FILE")
        MODE=$(jq -r '.mode // "auto"' "$STATE_FILE")

        echo ""
        echo "======================================"
        echo " ACTIVE LOOP DETECTED"
        echo "======================================"
        echo "Task: $TASK"
        echo "Mode: $MODE"
        echo "Current iteration: $ITERATION / $MAX_ITER"
        echo "Completion marker: <promise>$PROMISE</promise>"
        echo ""
        echo "The loop will continue automatically."
        echo "To stop: /loop-stop"
        echo "======================================"
        echo ""

        # Log detection
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - Session started, active loop detected at iteration $ITERATION" >> "$LOG_FILE"
    fi
fi

exit 0
