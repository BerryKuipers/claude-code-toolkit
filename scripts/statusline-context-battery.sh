#!/bin/bash
# Context Window Battery Statusline for Claude Code
#
# Shows context window usage as a colored battery bar
# Colors: Green (0-50%), Yellow (50-75%), Red (75-100%)
#
# Usage: Add to ~/.claude/settings.json:
# {
#   "statusLine": {
#     "type": "command",
#     "command": "/path/to/statusline-context-battery.sh"
#   }
# }

# Read JSON from stdin (Claude Code passes context data)
INPUT=$(cat)

# Extract context percentage using jq
if command -v jq &> /dev/null; then
    # Try used_percentage first, then calculate from tokens
    PERCENT=$(echo "$INPUT" | jq -r '.context_window.used_percentage // empty' 2>/dev/null)

    if [[ -z "$PERCENT" || "$PERCENT" == "null" ]]; then
        # Calculate from current_usage if available
        CURRENT=$(echo "$INPUT" | jq -r '.context_window.current_usage // 0' 2>/dev/null)
        # Assume 200k context window (adjust for model)
        MAX_CONTEXT=200000
        if [[ "$CURRENT" -gt 0 ]]; then
            PERCENT=$((CURRENT * 100 / MAX_CONTEXT))
        else
            PERCENT=0
        fi
    fi
else
    # Fallback if jq not available
    PERCENT=0
fi

# Ensure PERCENT is a number
PERCENT=${PERCENT:-0}
PERCENT=${PERCENT%.*}  # Remove decimal

# Clamp to 0-100
if [[ "$PERCENT" -lt 0 ]]; then PERCENT=0; fi
if [[ "$PERCENT" -gt 100 ]]; then PERCENT=100; fi

# Color codes
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
GRAY='\033[0;90m'
RESET='\033[0m'
BOLD='\033[1m'

# Choose color based on percentage
if [[ "$PERCENT" -ge 75 ]]; then
    COLOR=$RED
    ICON="🔴"
elif [[ "$PERCENT" -ge 50 ]]; then
    COLOR=$YELLOW
    ICON="🟡"
else
    COLOR=$GREEN
    ICON="🟢"
fi

# Build battery bar (10 segments)
FILLED=$((PERCENT / 10))
EMPTY=$((10 - FILLED))

BAR=""
for ((i=0; i<FILLED; i++)); do
    BAR="${BAR}█"
done
for ((i=0; i<EMPTY; i++)); do
    BAR="${BAR}░"
done

# Output formatted statusline
# Format: 🧠 [████████░░] 75%
printf "${COLOR}🧠 [${BAR}] ${BOLD}%d%%${RESET}" "$PERCENT"

# Add warning if over 75%
if [[ "$PERCENT" -ge 75 ]]; then
    printf " ${RED}⚠ CLEAR SOON${RESET}"
fi
