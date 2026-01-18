#!/bin/bash
# Context Window Monitor Hook (PostToolUse)
#
# Reads context percentage from .ralph/context-state.json
# (Claude writes this file as it works)
#
# Thresholds:
# - 72%: Warn if agents running
# - 75%: General warning
# - 80%: Recommend /clear
# - 90%: Critical

# set -e  # Disabled for Windows compatibility

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
RALPH_DIR="$PROJECT_DIR/.ralph"
CONTEXT_STATE="$RALPH_DIR/context-state.json"
SESSION_STATE="$RALPH_DIR/session-state.json"

# Only active during RALPH loop
if [[ ! -f "$RALPH_DIR/loop-active" ]]; then
    exit 0
fi

# Read context percentage from our state file (Claude writes this)
CONTEXT_PERCENT=0
if [[ -f "$CONTEXT_STATE" ]] && command -v jq &> /dev/null; then
    CONTEXT_PERCENT=$(jq -r '.usedPercent // 0' "$CONTEXT_STATE" 2>/dev/null || echo "0")
    LAST_UPDATE=$(jq -r '.updatedAt // empty' "$CONTEXT_STATE" 2>/dev/null)
fi

# Remove decimal, ensure number
CONTEXT_PERCENT=${CONTEXT_PERCENT%.*}
CONTEXT_PERCENT=${CONTEXT_PERCENT:-0}

# Exit if no data (Claude hasn't written yet)
if [[ "$CONTEXT_PERCENT" == "0" || "$CONTEXT_PERCENT" == "null" ]]; then
    # Remind Claude to update context state
    echo ""
    echo "📊 Context state not found. Claude should update .ralph/context-state.json"
    echo ""
    exit 0
fi

# Check for running agents
RUNNING_AGENTS=0
if [[ -f "$SESSION_STATE" ]] && command -v jq &> /dev/null; then
    RUNNING_AGENTS=$(jq -r '.runningAgents | length // 0' "$SESSION_STATE" 2>/dev/null || echo "0")
fi

# Thresholds
AGENT_WARN_THRESHOLD=72
WARN_THRESHOLD=75
CLEAR_THRESHOLD=80
CRITICAL_THRESHOLD=90

# Check for stuck/long-running agents
STUCK_WARNING=""
if [[ -f "$SESSION_STATE" ]] && command -v jq &> /dev/null; then
    OLDEST_START=$(jq -r '.runningAgents[0].startedAt // empty' "$SESSION_STATE" 2>/dev/null)
    if [[ -n "$OLDEST_START" && "$OLDEST_START" != "null" ]]; then
        START_EPOCH=$(date -d "$OLDEST_START" +%s 2>/dev/null || echo "0")
        NOW_EPOCH=$(date +%s)
        if [[ "$START_EPOCH" -gt 0 ]]; then
            RUNNING_MINS=$(( (NOW_EPOCH - START_EPOCH) / 60 ))
            if [[ "$RUNNING_MINS" -ge 10 ]]; then
                STUCK_WARNING="⏱️ Agent running for ${RUNNING_MINS}min - may be stuck!"
            fi
        fi
    fi
fi

# Logic based on context percentage
if [[ "$CONTEXT_PERCENT" -ge "$CRITICAL_THRESHOLD" ]]; then
    echo ""
    echo "🚨🚨🚨 CRITICAL: CONTEXT AT ${CONTEXT_PERCENT}% 🚨🚨🚨"
    echo "MUST /clear NOW regardless of running agents."
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
