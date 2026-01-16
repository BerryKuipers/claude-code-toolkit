#!/bin/bash
# Ralph Stop Hook - Persist session state on stop/crash
#
# This hook runs on Stop event to ensure RALPH loop state is saved
# so sessions can resume properly after interruption.
#
# Saves:
# - Current session state to session-state.json
# - Marks session as interrupted for proper resumption

set -e

# Configuration
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
RALPH_DIR="$PROJECT_DIR/.ralph"
SESSION_STATE="$RALPH_DIR/session-state.json"
PROGRESS_FILE="$RALPH_DIR/progress.txt"

# Only run if RALPH loop is active
if [[ ! -f "$RALPH_DIR/loop-active" ]]; then
    exit 0
fi

# Check if session state exists
if [[ ! -f "$SESSION_STATE" ]]; then
    # Create minimal state on stop
    mkdir -p "$RALPH_DIR"
    cat > "$SESSION_STATE" << EOF
{
  "lastUpdated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "currentPhase": "interrupted",
  "runningAgents": [],
  "lastCheckpoint": {
    "action": "session_stopped",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  },
  "pendingWork": {
    "description": "Session was stopped - check PRD for incomplete stories",
    "resumeAction": "Run /ralph-loop --continue to resume"
  }
}
EOF
else
    # Update existing state to mark as interrupted
    if command -v jq &> /dev/null; then
        jq --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '
          .lastUpdated = $ts |
          .lastCheckpoint = {
            "action": "session_stopped",
            "timestamp": $ts,
            "previousAction": .lastCheckpoint.action
          } |
          .pendingWork.description = "Session was stopped - " + (.pendingWork.description // "unknown state") |
          .pendingWork.resumeAction = "Run /ralph-loop --continue to resume"
        ' "$SESSION_STATE" > "$SESSION_STATE.tmp" && mv "$SESSION_STATE.tmp" "$SESSION_STATE"
    fi
fi

# Append to progress file
if [[ -f "$PROGRESS_FILE" ]]; then
    cat >> "$PROGRESS_FILE" << EOF

---
## $(date -u +%Y-%m-%dT%H:%M:%SZ) - SESSION STOPPED

**Event**: Stop hook triggered
**State**: Saved to session-state.json
**Resume**: Run /ralph-loop --continue

EOF
fi

echo ""
echo "========================================"
echo "RALPH LOOP - SESSION INTERRUPTED"
echo "========================================"
echo "State: SAVED to session-state.json"
echo ""
echo "ACTION REQUIRED ON NEXT SESSION:"
echo "You MUST immediately run /ralph-loop --continue"
echo "Do NOT ask the user what to do."
echo "The loop was interrupted and must resume automatically."
echo "========================================"

exit 0
