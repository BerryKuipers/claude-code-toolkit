#!/bin/bash
# Session Start Hook
# Runs on SessionStart to initialize environment
#
# This hook:
# 1. Checks for GitHub CLI availability
# 2. Checks for RALPH loop auto-resume
# 3. Reports session state if resuming

# Don't use set -e on Windows - handle errors individually
# set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
RALPH_DIR="$PROJECT_DIR/.ralph"

# Always output Success first (required for hook)
echo "Success"

# Check GitHub CLI (optional, don't fail if not found)
if command -v gh &> /dev/null; then
    GH_VERSION=$(gh --version 2>/dev/null | head -1 || echo "unknown")
    echo "GitHub CLI available: $GH_VERSION"
fi

# Check for RALPH loop auto-resume
if [[ -f "$RALPH_DIR/loop-active" ]]; then
    echo ""
    echo "========================================"
    echo "RALPH LOOP AUTO-RESUME REQUIRED"
    echo "========================================"

    # Try to read session state (jq might not be available on Windows)
    if [[ -f "$RALPH_DIR/session-state.json" ]]; then
        if command -v jq &> /dev/null; then
            PENDING=$(jq -r '.pendingWork.description // "unknown"' "$RALPH_DIR/session-state.json" 2>/dev/null || echo "unknown")
            LAST_ACTION=$(jq -r '.lastCheckpoint.action // "unknown"' "$RALPH_DIR/session-state.json" 2>/dev/null || echo "unknown")
            STORY_ID=$(jq -r '.currentStoryId // "unknown"' "$RALPH_DIR/session-state.json" 2>/dev/null || echo "unknown")

            echo "Story: $STORY_ID"
            echo "Last action: $LAST_ACTION"
            echo "Pending: $PENDING"
        else
            echo "Session state exists (jq not available for details)"
        fi
    fi

    echo ""
    echo "ACTION REQUIRED:"
    echo "1. Run /clear to reset context"
    echo "2. Run /ralph-loop --continue to resume"
    echo ""
    echo "Do NOT ask the user what to do. The loop was interrupted and must resume."
    echo "========================================"
fi

exit 0
