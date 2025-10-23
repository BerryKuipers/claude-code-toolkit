#!/bin/bash
# UserPromptSubmit Hook - Pure Orchestrator Delegation
# Routes all tasks to OrchestratorAgent for intelligent agent selection
# Follows SOLID/DRY/SoC principles - no hardcoded keyword logic

USER_PROMPT="$1"

cat << EOF
{
  "action": "continue",
  "additionalContext": "\\n\\n🎯 **Task Routing Available**\\n\\nFor complex tasks requiring agent coordination, use OrchestratorAgent:\\n\\n**Advisory Mode** (non-blocking recommendations):\\n\`Task({ subagent_type: \\"orchestrator\\", prompt: \\"${USER_PROMPT}\\", mode: \\"advisory\\" })\`\\n\\n**Full Orchestration** (blocking delegation):\\n\`/orchestrator task=\\"${USER_PROMPT}\\" mode=full\`\\n\\nOrchestratorAgent will intelligently route to: ArchitectAgent, DesignAgent, AuditAgent, RefactorAgent, or appropriate slash commands."
}
EOF
exit 0