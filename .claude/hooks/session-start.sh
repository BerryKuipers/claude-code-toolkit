#!/bin/bash
# Session Start Hook
# Runs on SessionStart to initialize environment
#
# This hook:
# 1. Checks for GitHub CLI availability
# 2. Checks for RALPH loop auto-resume
# 3. Reports session state if resuming

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
RALPH_DIR="$PROJECT_DIR/.ralph"

echo "Success"

# Check GitHub CLI
if command -v gh &> /dev/null; then
    GH_VERSION=$(gh --version 2>/dev/null | head -1 || echo "unknown")
    echo "GitHub CLI available: $GH_VERSION"
else
    echo "GitHub CLI not installed - some features may be limited"
fi

# Check for RALPH loop auto-resume
if [[ -f "$RALPH_DIR/loop-active" ]]; then
    echo ""
    echo "RALPH LOOP DETECTED"
    echo "==================="

    if [[ -f "$RALPH_DIR/session-state.json" ]]; then
        PENDING=$(jq -r '.pendingWork.description // "unknown"' "$RALPH_DIR/session-state.json" 2>/dev/null || echo "unknown")
        LAST_ACTION=$(jq -r '.lastCheckpoint.action // "unknown"' "$RALPH_DIR/session-state.json" 2>/dev/null || echo "unknown")

        echo "Last action: $LAST_ACTION"
        echo "Pending: $PENDING"
        echo ""
        echo "Resume with: /ralph-loop --continue"
    else
        echo "Loop active but no session state found"
        echo "Resume with: /ralph-loop --continue"
    fi
fi

exit 0
