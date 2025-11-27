#!/bin/bash
# UserPromptSubmit Hook: Mandatory Agent Routing
# Injects agent delegation context based on task keywords
# Makes Claude AWARE it should use agents for specific tasks

USER_PROMPT="$1"

# Convert to lowercase for matching
PROMPT_LOWER=$(echo "$USER_PROMPT" | tr '[:upper:]' '[:lower:]')

# ============================================
# TASK DETECTION & AGENT MAPPING
# ============================================

DETECTED_TASKS=""
RECOMMENDED_AGENTS=""

# Use bash built-in regex matching [[ =~ ]] for better performance (avoids forking processes)

# Database operations -> database agent
if [[ "$PROMPT_LOWER" =~ (database|migration|schema|sql|table|column|index|drizzle|prisma|supabase) ]]; then
  DETECTED_TASKS+="- Database operation detected\n"
  RECOMMENDED_AGENTS+="- **database** agent: Safe database operations with schema validation\n"
fi

# Refactoring -> refactor agent
if [[ "$PROMPT_LOWER" =~ (refactor|clean\ up|simplify|extract|consolidate|dry|duplication|technical\ debt) ]]; then
  DETECTED_TASKS+="- Refactoring task detected\n"
  RECOMMENDED_AGENTS+="- **refactor** agent: Safe refactoring with Clean Code principles\n"
fi

# Architecture review -> architect agent
if [[ "$PROMPT_LOWER" =~ (architect|solid|structure|layer|pattern|design\ pattern|vertical\ slice|vsa|separation\ of\ concern|soc) ]]; then
  DETECTED_TASKS+="- Architecture review detected\n"
  RECOMMENDED_AGENTS+="- **architect** agent: SOLID/VSA/Layer validation\n"
fi

# Feature implementation -> implementation agent
if [[ "$PROMPT_LOWER" =~ (implement|create|build|add\ feature|new\ feature|develop) ]]; then
  DETECTED_TASKS+="- Feature implementation detected\n"
  RECOMMENDED_AGENTS+="- **implementation** agent: Structured feature development\n"
fi

# Code review -> code-reviewer agent
if [[ "$PROMPT_LOWER" =~ (review|code\ review|check\ code|validate|audit\ code) ]]; then
  DETECTED_TASKS+="- Code review detected\n"
  RECOMMENDED_AGENTS+="- **code-reviewer** agent: Comprehensive code review\n"
fi

# Security -> security-pentest agent
if [[ "$PROMPT_LOWER" =~ (security|vulnerability|xss|sql\ injection|auth|authentication|authorization|owasp) ]]; then
  DETECTED_TASKS+="- Security task detected\n"
  RECOMMENDED_AGENTS+="- **security-pentest** agent: Security analysis and testing\n"
fi

# UI/Frontend -> design or ui-frontend-agent
if [[ "$PROMPT_LOWER" =~ (ui|frontend|component|react|vue|styling|css|design|ux) ]]; then
  DETECTED_TASKS+="- UI/Frontend task detected\n"
  RECOMMENDED_AGENTS+="- **design** or **ui-frontend-agent**: UI development and testing\n"
fi

# Complex workflow -> orchestrator or conductor
if [[ "$PROMPT_LOWER" =~ (workflow|multiple|coordinate|end-to-end|full\ feature|complete|from\ scratch) ]]; then
  DETECTED_TASKS+="- Complex workflow detected\n"
  RECOMMENDED_AGENTS+="- **orchestrator** or **conductor** agent: Multi-agent coordination\n"
fi

# ============================================
# BUILD CONTEXT MESSAGE
# ============================================

if [ -n "$RECOMMENDED_AGENTS" ]; then
  # Inject mandatory context
  cat << EOF
{
  "action": "continue",
  "additionalContext": "\n\n---\n\n**MANDATORY: Agent Delegation Required**\n\nThis task matches patterns that REQUIRE specialized agents:\n\n$DETECTED_TASKS\n**You MUST use these agents:**\n$RECOMMENDED_AGENTS\n**How to delegate:**\n\`\`\`\nTask({ subagent_type: \"agent-name\", prompt: \"[task description]\" })\n\`\`\`\n\n**Coding Principles to Enforce:**\n- DRY (Don't Repeat Yourself)\n- SOLID (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion)\n- SOC (Separation of Concerns)\n- Typed code (no \`any\`, explicit types)\n- Modular architecture\n- Centralized utilities/constants\n- Clean Code (Uncle Bob's principles)\n\n**If you write code directly without using agents, the quality gate will flag violations.**\n\n---"
}
EOF
else
  # No specific agent detected, but remind about principles
  cat << EOF
{
  "action": "continue",
  "additionalContext": "\n\n**Reminder: Use Specialized Agents When Applicable**\n\nAvailable agents: architect, refactor, implementation, database, code-reviewer, security-pentest, design, orchestrator, conductor\n\n**Always enforce:** DRY, SOLID, SOC, typed code, modular, centralized, Clean Code"
}
EOF
fi

exit 0
