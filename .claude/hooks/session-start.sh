#!/bin/bash
# Session Start Hook - Lightweight session initialization
# Checks GitHub CLI and loads project overlay config

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
PROJECT_NAME=$(basename "$PROJECT_DIR")

export CLAUDE_CODE_TASK_LIST_ID="${PROJECT_NAME}"

echo "Success"
echo "Task list: ${CLAUDE_CODE_TASK_LIST_ID}"

if command -v gh &> /dev/null; then
    GH_VERSION=$(gh --version 2>/dev/null | head -1 || echo "unknown")
    echo "GitHub CLI available: $GH_VERSION"
fi

OVERLAY_SCRIPT="$PROJECT_DIR/.claude/hooks/load-overlay.sh"
TOOLKIT_OVERLAY_SCRIPT="$PROJECT_DIR/.claude-toolkit/.claude/hooks/load-overlay.sh"
if [[ -x "$OVERLAY_SCRIPT" ]]; then
    OVERLAY_INFO=$("$OVERLAY_SCRIPT" 2>/dev/null || true)
    if [[ -n "$OVERLAY_INFO" ]]; then
        echo "Project overlay: $(echo "$OVERLAY_INFO" | grep "^project=" | cut -d= -f2)"
    fi
elif [[ -x "$TOOLKIT_OVERLAY_SCRIPT" ]]; then
    OVERLAY_INFO=$("$TOOLKIT_OVERLAY_SCRIPT" 2>/dev/null || true)
    if [[ -n "$OVERLAY_INFO" ]]; then
        echo "Project overlay: $(echo "$OVERLAY_INFO" | grep "^project=" | cut -d= -f2)"
    fi
fi

exit 0
