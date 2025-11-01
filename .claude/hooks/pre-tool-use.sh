#!/bin/bash
# PreToolUse Hook - Allow gh CLI commands in web sessions
# Validates architectural patterns and enables GitHub CLI operations

TOOL_NAME="$1"
TOOL_ARGS="$2"

# Allow gh CLI commands (needed for web sessions with sandboxing)
if [[ "$TOOL_NAME" == "Bash" ]]; then
  # Allow gh commands (GitHub CLI operations)
  if echo "$TOOL_ARGS" | grep -E "^gh " > /dev/null 2>&1; then
    echo '{"action": "allow"}'
    exit 0
  fi

  # Allow git commands (version control operations)
  if echo "$TOOL_ARGS" | grep -E "^git " > /dev/null 2>&1; then
    echo '{"action": "allow"}'
    exit 0
  fi

  # Block direct execution of commands/agents via Bash
  if echo "$TOOL_ARGS" | grep -E "\.claude/(commands|agents)/[^_].*\.md" > /dev/null 2>&1; then
    cat << 'EOF'
{
  "action": "block",
  "message": "❌ **ARCHITECTURAL VIOLATION**: Commands and agents cannot be run via Bash.\n\n**Correct Usage:**\n\n✅ For slash commands:\n```\n/architect --scope=backend\n/audit --severity=high\n```\n\n✅ For agents (use natural language):\nDelegate to architect agent for reviewing backend architecture\nDelegate to design agent for improving ProfileCard UI\n\n📚 See agent documentation for details."
}
EOF
    exit 0
  fi

  # Block recursion (orchestrator calling itself)
  if echo "$TOOL_ARGS" | grep -E "/orchestrator|orchestrator\.sh" > /dev/null 2>&1; then
    cat << 'EOF'
{
  "action": "block",
  "message": "⚠️ **RECURSION WARNING**: Do not invoke /orchestrator from main conversation.\n\n**Why this happens:**\n- You're already talking to the orchestrator agent\n- Calling /orchestrator tries to invoke orchestrator FROM orchestrator = recursion\n\n**Solution:**\n✅ Just ask naturally and I will route to the right agent\n\n**When /orchestrator IS needed:**\n- Only when OTHER agents need to coordinate multiple agents"
}
EOF
    exit 0
  fi
fi

# Validate Task tool usage
if [[ "$TOOL_NAME" == "Task" ]]; then
  # Check if subagent_type is provided
  if ! echo "$TOOL_ARGS" | grep -E "subagent_type" > /dev/null 2>&1; then
    cat << 'EOF'
{
  "action": "block",
  "message": "⚠️ **MISSING PARAMETER**: Task tool requires 'subagent_type' parameter.\n\n**Correct Usage:**\nDelegate to [agent-name] for [task description]\n\n**Available agents:**\n- architect, design, audit, refactor, orchestrator, conductor, mega-workflow, implementation, database, security-pentest"
}
EOF
    exit 0
  fi
fi

# Allow all other tools (passed validation)
echo '{"action": "allow"}'
exit 0
