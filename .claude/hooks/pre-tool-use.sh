#!/bin/bash
# PreToolUse Hook - Architectural Enforcement
# Validates tool usage follows TribeVibe architectural patterns

TOOL_NAME="$1"
TOOL_ARGS="$2"

# Block direct Bash invocation of commands/agents
if [[ "$TOOL_NAME" == "Bash" ]]; then
  # Check if trying to run .md files from .claude/commands or .claude/agents
  if echo "$TOOL_ARGS" | grep -E "\.claude/(commands|agents)/[^_].*\.md" > /dev/null 2>&1; then
    cat << 'EOF'
{
  "action": "block",
  "message": "❌ **ARCHITECTURAL VIOLATION**: Commands and agents cannot be run via Bash.\n\n**Correct Usage:**\n\n✅ For slash commands:\n```typescript\nSlashCommand(\"/architect\", \"--scope=backend\")\nSlashCommand(\"/audit\", \"--severity=high\")\n```\n\n✅ For agents:\n```typescript\nTask({\n  subagent_type: \"design\",\n  description: \"UI improvement\",\n  prompt: \"Improve ProfileCard design...\"\n})\n```\n\n📚 See CLAUDE.md 'Tool Usage Guidelines' section for details."
}
EOF
    exit 0
  fi

  # Check if trying to invoke orchestrator via Bash (causes recursion)
  if echo "$TOOL_ARGS" | grep -E "/orchestrator|orchestrator\.sh" > /dev/null 2>&1; then
    cat << 'EOF'
{
  "action": "block",
  "message": "⚠️ **RECURSION WARNING**: Do not invoke /orchestrator from main conversation.\n\n**Why this happens:**\n- You're already talking to the orchestrator (Claude Code main agent)\n- Calling /orchestrator tries to invoke orchestrator FROM orchestrator = recursion\n\n**Solution:**\n✅ Just ask naturally: \"improve ProfileCard design\"\n✅ I will automatically route to the right agent\n\n**When /orchestrator IS needed:**\n- Only when OTHER agents need to coordinate multiple agents\n- Example: AuditAgent uses /orchestrator to coordinate ArchitectAgent + DesignAgent\n\n📚 See CLAUDE.md for details on orchestrator usage."
}
EOF
    exit 0
  fi
fi

# Validate Task tool usage for agents
if [[ "$TOOL_NAME" == "Task" ]]; then
  # Check if subagent_type is provided
  if ! echo "$TOOL_ARGS" | grep -E "subagent_type" > /dev/null 2>&1; then
    cat << 'EOF'
{
  "action": "block",
  "message": "⚠️ **MISSING PARAMETER**: Task tool requires 'subagent_type' parameter.\n\n**Correct Usage:**\n```typescript\nTask({\n  subagent_type: \"architect\",  // Required: agent name\n  description: \"Review backend\",\n  prompt: \"Analyze services/api for VSA compliance...\"\n})\n```\n\n**Available agents:**\n- architect (ArchitectAgent)\n- design (DesignAgent)\n- audit (AuditAgent)\n- refactor (RefactorAgent)\n- orchestrator (OrchestratorAgent)\n- system-validator (SystemValidatorAgent)"
}
EOF
    exit 0
  fi
fi

# Allow the tool (passed all validation checks)
echo '{"action": "allow"}'
exit 0