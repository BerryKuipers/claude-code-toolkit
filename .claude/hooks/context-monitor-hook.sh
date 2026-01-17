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
AGENT_WARN_THRESHOLD=72  # Warn early if agents running
WARN_THRESHOLD=75
CLEAR_THRESHOLD=80
CRITICAL_THRESHOLD=90
STUCK_TIMEOUT_MINUTES=10  # Warn about processes running longer than this

# Check for stuck/long-running agents
STUCK_WARNING=""
if [[ -f "$SESSION_STATE" ]] && command -v jq &> /dev/null; then
    # Check oldest agent start time
    OLDEST_START=$(jq -r '.runningAgents[0].startedAt // empty' "$SESSION_STATE" 2>/dev/null)
    if [[ -n "$OLDEST_START" && "$OLDEST_START" != "null" ]]; then
        # Calculate minutes running (simplified)
        START_EPOCH=$(date -d "$OLDEST_START" +%s 2>/dev/null || echo "0")
        NOW_EPOCH=$(date +%s)
        if [[ "$START_EPOCH" -gt 0 ]]; then
            RUNNING_MINS=$(( (NOW_EPOCH - START_EPOCH) / 60 ))
            if [[ "$RUNNING_MINS" -ge "$STUCK_TIMEOUT_MINUTES" ]]; then
                STUCK_WARNING="⏱️ Agent running for ${RUNNING_MINS}min (>${STUCK_TIMEOUT_MINUTES}min) - may be stuck!"
            fi
        fi
    fi
fi

# Logic based on context percentage
if [[ "$CONTEXT_PERCENT" -ge "$CRITICAL_THRESHOLD" ]]; then
    echo ""
    echo "🚨🚨🚨 CRITICAL: CONTEXT AT ${CONTEXT_PERCENT}% 🚨🚨🚨"
    echo "Autocompact imminent! MUST /clear NOW regardless of running agents."
    if [[ -n "$STUCK_WARNING" ]]; then
        echo "$STUCK_WARNING"
        echo "KILL stuck processes and /clear NOW!"
    fi
    echo ""
    echo "ACTION REQUIRED: Save state and run /clear IMMEDIATELY"
    echo ""

elif [[ "$CONTEXT_PERCENT" -ge "$CLEAR_THRESHOLD" ]]; then
    if [[ "$RUNNING_AGENTS" -gt 0 ]]; then
        echo ""
        echo "⚠️ CONTEXT AT ${CONTEXT_PERCENT}% - AGENTS RUNNING ($RUNNING_AGENTS)"
        if [[ -n "$STUCK_WARNING" ]]; then
            echo "$STUCK_WARNING"
            echo "Consider killing stuck process and /clear."
        else
            echo "Wait for agents to finish, then /clear immediately."
        fi
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
    if [[ -n "$STUCK_WARNING" ]]; then
        echo "$STUCK_WARNING"
    fi
    echo ""

elif [[ "$CONTEXT_PERCENT" -ge "$AGENT_WARN_THRESHOLD" && "$RUNNING_AGENTS" -gt 0 ]]; then
    echo ""
    echo "📊 Context: ${CONTEXT_PERCENT}% with $RUNNING_AGENTS agent(s) running"
    echo "Prepare to /clear soon after agents complete."
    if [[ -n "$STUCK_WARNING" ]]; then
        echo "$STUCK_WARNING"
    fi
    echo ""
fi

exit 0
