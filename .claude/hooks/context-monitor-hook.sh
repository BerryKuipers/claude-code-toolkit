#!/bin/bash
# Context Window Monitor Hook (PostToolUse)
#
# Smart context monitoring that:
# 1. Checks context_window.used_percentage after tool use
# 2. Waits for running agents to finish before clearing
# 3. Warns at 75%, recommends /clear at 80%
#
# Reads context data from CLAUDE_CONTEXT_WINDOW env or stdin

set -e

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
RALPH_DIR="$PROJECT_DIR/.ralph"
SESSION_STATE="$RALPH_DIR/session-state.json"

# Only active during RALPH loop
if [[ ! -f "$RALPH_DIR/loop-active" ]]; then
    exit 0
fi

# Get context percentage from environment (Claude Code sets this)
CONTEXT_PERCENT="${CLAUDE_CONTEXT_USED_PERCENT:-0}"

# If not in env, try to read from stdin JSON (fallback)
if [[ "$CONTEXT_PERCENT" == "0" ]]; then
    # Read stdin if available
    if read -t 0.1 INPUT 2>/dev/null; then
        if command -v jq &> /dev/null; then
            CONTEXT_PERCENT=$(echo "$INPUT" | jq -r '.context_window.used_percentage // 0' 2>/dev/null || echo "0")
        fi
    fi
fi

# Remove decimal, ensure number
CONTEXT_PERCENT=${CONTEXT_PERCENT%.*}
CONTEXT_PERCENT=${CONTEXT_PERCENT:-0}

# Exit if we can't determine context (don't block on missing data)
if [[ "$CONTEXT_PERCENT" == "0" || "$CONTEXT_PERCENT" == "null" ]]; then
    exit 0
fi

# Check for running agents
RUNNING_AGENTS=0
if [[ -f "$SESSION_STATE" ]] && command -v jq &> /dev/null; then
    RUNNING_AGENTS=$(jq -r '.runningAgents | length // 0' "$SESSION_STATE" 2>/dev/null || echo "0")
fi

# Thresholds
WARN_THRESHOLD=75
CLEAR_THRESHOLD=80
CRITICAL_THRESHOLD=90

# Logic based on context percentage
if [[ "$CONTEXT_PERCENT" -ge "$CRITICAL_THRESHOLD" ]]; then
    echo ""
    echo "🚨🚨🚨 CRITICAL: CONTEXT AT ${CONTEXT_PERCENT}% 🚨🚨🚨"
    echo "Autocompact imminent! MUST /clear NOW regardless of running agents."
    echo ""
    echo "ACTION REQUIRED: Save state and run /clear IMMEDIATELY"
    echo ""

elif [[ "$CONTEXT_PERCENT" -ge "$CLEAR_THRESHOLD" ]]; then
    if [[ "$RUNNING_AGENTS" -gt 0 ]]; then
        echo ""
        echo "⚠️ CONTEXT AT ${CONTEXT_PERCENT}% - AGENTS RUNNING ($RUNNING_AGENTS)"
        echo "Wait for agents to finish, then /clear immediately."
        echo "DO NOT start new work until cleared."
        echo ""
    else
        echo ""
        echo "========================================"
        echo "⚠️ CONTEXT AT ${CONTEXT_PERCENT}% - CLEAR NOW"
        echo "========================================"
        echo "No agents running. Safe to /clear."
        echo ""
        echo "ACTION REQUIRED:"
        echo "1. Save state to session-state.json"
        echo "2. Update progress.txt"
        echo "3. Run /clear"
        echo "========================================"
        echo ""
    fi

elif [[ "$CONTEXT_PERCENT" -ge "$WARN_THRESHOLD" ]]; then
    echo ""
    echo "📊 Context: ${CONTEXT_PERCENT}% (approaching clear threshold at ${CLEAR_THRESHOLD}%)"
    echo ""
fi

exit 0
