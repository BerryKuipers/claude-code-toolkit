#!/bin/bash
# PostToolUse Hook - Delegation Transparency Logging
# Logs agent and command invocations for audit trail

TOOL_NAME="$1"
TOOL_ARGS="$2"
TIMESTAMP=$(date -Iseconds 2>/dev/null || date +%Y-%m-%dT%H:%M:%S)

# Ensure log directory exists
mkdir -p .claude/logs

# Log Task tool usage (agent invocations)
if [[ "$TOOL_NAME" == "Task" ]]; then
  # Extract agent type from arguments
  AGENT_TYPE=$(echo "$TOOL_ARGS" | grep -oE "subagent_type[\"']?\s*[:=]\s*[\"']?([a-z-]+)" | sed -E "s/.*[\"':= ]([a-z-]+).*/\1/" | head -1)

  if [[ -n "$AGENT_TYPE" ]]; then
    {
      echo "✅ Agent invoked: $AGENT_TYPE"
      echo "   Timestamp: $TIMESTAMP"
      echo "   Tool: Task"
      echo ""
    } >> .claude/logs/agent-invocations.log
  fi
fi

# Log SlashCommand usage (command invocations)
if [[ "$TOOL_NAME" == "SlashCommand" ]]; then
  # Extract command from arguments (first argument after SlashCommand)
  COMMAND=$(echo "$TOOL_ARGS" | grep -oE "^/[a-z:-]+" | head -1)

  if [[ -n "$COMMAND" ]]; then
    {
      echo "✅ Command invoked: $COMMAND"
      echo "   Timestamp: $TIMESTAMP"
      echo "   Tool: SlashCommand"
      echo ""
    } >> .claude/logs/command-invocations.log
  fi
fi

# Log delegation attempts (for transparency tracking)
if [[ "$TOOL_NAME" == "Task" ]] || [[ "$TOOL_NAME" == "SlashCommand" ]]; then
  {
    echo "[$TIMESTAMP] DELEGATION"
    echo "  Tool: $TOOL_NAME"
    echo "  Args: $TOOL_ARGS"
    echo ""
  } >> .claude/logs/delegation-transparency.log
fi

# Always allow (post-tool hooks are for logging only, not blocking)
echo '{"action": "continue"}'
exit 0