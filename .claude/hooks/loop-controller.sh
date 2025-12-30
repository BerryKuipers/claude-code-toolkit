#!/bin/bash
# Loop Controller Hook
# Called on Stop event to manage loop state and safety limits
#
# This hook:
# 1. Checks if an active loop exists for this repo
# 2. Enforces max_iterations safety limit
# 3. Detects completion markers and disables loop when done
# 4. Persists state for cross-session resumption
#
# Environment variables available from Claude Code:
# - CLAUDE_PROJECT_DIR: Project root directory
# - CLAUDE_SESSION_OUTPUT: Recent assistant output (if available)

set -e

# Configuration
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
STATE_FILE="${PROJECT_DIR}/.claude/state/loop.local.json"
LOG_FILE="${PROJECT_DIR}/.claude/state/loop.log"

# Silent exit if no state file exists
[ ! -f "$STATE_FILE" ] && exit 0

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "loop-controller: jq not found, skipping" >> "$LOG_FILE"
    exit 0
fi

# Read state
ENABLED=$(jq -r '.enabled // false' "$STATE_FILE")
[ "$ENABLED" != "true" ] && exit 0

# Load loop configuration
MAX_ITERATIONS=$(jq -r '.max_iterations // 20' "$STATE_FILE")
CURRENT_ITERATION=$(jq -r '.iteration // 1' "$STATE_FILE")
COMPLETION_PROMISE=$(jq -r '.completion_promise // "DONE"' "$STATE_FILE")
SESSION_TOKEN=$(jq -r '.session_token // ""' "$STATE_FILE")
STATE_CWD=$(jq -r '.cwd // ""' "$STATE_FILE")
TASK=$(jq -r '.original_arguments // ""' "$STATE_FILE")

# Session scoping: verify we're in the same repo
CURRENT_CWD="$(pwd)"
if [ -n "$STATE_CWD" ] && [ "$STATE_CWD" != "$CURRENT_CWD" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - Loop state from different directory ($STATE_CWD), ignoring" >> "$LOG_FILE"
    exit 0
fi

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Function to disable loop
disable_loop() {
    local reason="$1"
    jq --arg reason "$reason" \
       --arg ts "$TIMESTAMP" \
       '.enabled = false | .disabled_reason = $reason | .disabled_at = $ts' \
       "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
    echo "$TIMESTAMP - Loop disabled: $reason" >> "$LOG_FILE"
}

# Function to increment iteration
increment_iteration() {
    local new_iteration=$((CURRENT_ITERATION + 1))
    jq --argjson iter "$new_iteration" \
       --arg ts "$TIMESTAMP" \
       '.iteration = $iter | .updated_at = $ts' \
       "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
    echo "$TIMESTAMP - Iteration incremented to $new_iteration" >> "$LOG_FILE"
}

# Check 1: Max iterations safety limit
if [ "$CURRENT_ITERATION" -ge "$MAX_ITERATIONS" ]; then
    disable_loop "Max iterations ($MAX_ITERATIONS) reached"

    echo ""
    echo "======================================"
    echo " LOOP HARD STOP - MAX ITERATIONS"
    echo "======================================"
    echo "Task: $TASK"
    echo "Iterations completed: $CURRENT_ITERATION"
    echo "Status: Incomplete - manual intervention may be needed"
    echo ""
    echo "To resume: /loop $TASK"
    echo "To check status: cat $STATE_FILE | jq"
    echo "======================================"
    exit 0
fi

# Check 2: Look for completion marker in recent output
# Note: CLAUDE_SESSION_OUTPUT may not be available in all contexts
# If available, check for the promise marker
DONE_DETECTED=false

# Method 1: Check environment variable (if Claude Code provides it)
if [ -n "${CLAUDE_SESSION_OUTPUT:-}" ]; then
    if echo "$CLAUDE_SESSION_OUTPUT" | grep -q "<promise>$COMPLETION_PROMISE</promise>"; then
        DONE_DETECTED=true
        echo "$TIMESTAMP - Completion marker found in session output" >> "$LOG_FILE"
    fi
fi

# Method 2: Check if assistant explicitly set done flag in state
DONE_FLAG=$(jq -r '.done // false' "$STATE_FILE")
if [ "$DONE_FLAG" = "true" ]; then
    DONE_DETECTED=true
    echo "$TIMESTAMP - Done flag set in state file" >> "$LOG_FILE"
fi

if [ "$DONE_DETECTED" = "true" ]; then
    disable_loop "Task completed (promise marker detected)"

    echo ""
    echo "======================================"
    echo " LOOP COMPLETE"
    echo "======================================"
    echo "Task: $TASK"
    echo "Iterations: $CURRENT_ITERATION"
    echo "Status: SUCCESS"
    echo "======================================"
    exit 0
fi

# Check 3: No completion detected - prepare for next iteration
# Increment iteration counter for next session
increment_iteration

echo ""
echo "======================================"
echo " LOOP ITERATION $CURRENT_ITERATION COMPLETE"
echo "======================================"
echo "Task: $TASK"
echo "Next iteration: $((CURRENT_ITERATION + 1)) / $MAX_ITERATIONS"
echo ""
echo "Loop will continue on next session start."
echo "To stop: /loop-stop"
echo "======================================"

# Write continuation prompt for SessionStart hook to pick up
CONTINUATION_FILE="${PROJECT_DIR}/.claude/state/loop.continue"
cat > "$CONTINUATION_FILE" << EOF
{
  "continue_loop": true,
  "iteration": $((CURRENT_ITERATION + 1)),
  "task": $(echo "$TASK" | jq -Rs .),
  "promise": "$COMPLETION_PROMISE",
  "remaining_iterations": $((MAX_ITERATIONS - CURRENT_ITERATION))
}
EOF

exit 0
