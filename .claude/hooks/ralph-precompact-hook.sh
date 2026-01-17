#!/bin/bash
# Ralph PreCompact Hook - Emergency state save before autocompact
#
# This hook fires BEFORE autocompact to save RALPH state.
# GOAL: Avoid ever reaching this point - /clear before 75% context.
# This is a SAFETY NET if self-monitoring fails.

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
RALPH_DIR="$PROJECT_DIR/.ralph"
SESSION_STATE="$RALPH_DIR/session-state.json"
PROGRESS_FILE="$RALPH_DIR/progress.txt"
LOOP_STATE="$RALPH_DIR/loop-state.json"

# Only run if RALPH loop is active
if [[ ! -f "$RALPH_DIR/loop-active" ]]; then
    exit 0
fi

echo ""
echo "========================================"
echo "⚠️  PRECOMPACT TRIGGERED - SAVING STATE"
echo "========================================"
echo "Autocompact is about to run."
echo "RALPH state being saved as safety net."
echo ""

# Update session state with precompact warning
if [[ -f "$SESSION_STATE" ]]; then
    if command -v jq &> /dev/null; then
        jq --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '
          .lastUpdated = $ts |
          .lastCheckpoint = {
            "action": "precompact_triggered",
            "timestamp": $ts,
            "warning": "Context limit reached - autocompact imminent"
          } |
          .pendingWork.precompactSave = true
        ' "$SESSION_STATE" > "$SESSION_STATE.tmp" && mv "$SESSION_STATE.tmp" "$SESSION_STATE"
    fi
fi

# Append warning to progress file
if [[ -f "$PROGRESS_FILE" ]]; then
    cat >> "$PROGRESS_FILE" << EOF

---
## $(date -u +%Y-%m-%dT%H:%M:%SZ) - ⚠️ PRECOMPACT TRIGGERED

**WARNING**: Context window limit reached. Autocompact about to run.
**State**: Saved to session-state.json
**Action**: Should have run /clear earlier to avoid this.

EOF
fi

# Update loop state
if [[ -f "$LOOP_STATE" ]]; then
    if command -v jq &> /dev/null; then
        jq --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '
          .lastUpdated = $ts |
          .precompactCount = ((.precompactCount // 0) + 1)
        ' "$LOOP_STATE" > "$LOOP_STATE.tmp" && mv "$LOOP_STATE.tmp" "$LOOP_STATE"
    fi
fi

echo "State saved. After compaction, run /ralph-loop --continue"
echo "========================================"

exit 0
