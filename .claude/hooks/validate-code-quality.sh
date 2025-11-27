#!/bin/bash
# PreToolUse Hook: Code Quality & Principle Enforcement
# Intercepts Edit/Write operations to enforce DRY, SOLID, SOC, typed, modular, centralized principles
# Blocks violations and suggests using appropriate agents

TOOL_NAME="$1"
TOOL_ARGS="$2"

# Only validate Edit and Write operations
if [[ "$TOOL_NAME" != "Edit" ]] && [[ "$TOOL_NAME" != "Write" ]]; then
  echo '{"action": "allow"}'
  exit 0
fi

# Extract file path from tool arguments
FILE_PATH=$(echo "$TOOL_ARGS" | grep -oE '"file_path"\s*:\s*"[^"]+' | sed 's/"file_path"\s*:\s*"//')
if [ -z "$FILE_PATH" ]; then
  FILE_PATH=$(echo "$TOOL_ARGS" | grep -oE 'file_path[^"]*"[^"]+' | grep -oE '"[^"]+$' | tr -d '"')
fi

# Skip validation for non-code files
case "$FILE_PATH" in
  *.md|*.txt|*.json|*.yml|*.yaml|*.toml|*.lock|*.css|*.scss|*.html)
    echo '{"action": "allow"}'
    exit 0
    ;;
esac

# Extract new content being written
NEW_CONTENT=$(echo "$TOOL_ARGS" | grep -oE '"(new_string|content)"\s*:\s*"[^"]*' | sed 's/"[^"]*"\s*:\s*"//' | head -1)

# ============================================
# PRINCIPLE VIOLATION CHECKS
# ============================================

VIOLATIONS=""

# Check 1: Untyped functions (TypeScript/JavaScript)
if [[ "$FILE_PATH" =~ \.(ts|tsx|js|jsx)$ ]]; then
  # Detect function without type annotations
  if echo "$NEW_CONTENT" | grep -qE "function\s+\w+\s*\([^:)]+\)\s*\{"; then
    VIOLATIONS="$VIOLATIONS\n- **Typed Code Violation**: Function parameters missing type annotations"
  fi

  # Detect 'any' type usage
  if echo "$NEW_CONTENT" | grep -qE ":\s*any\b"; then
    VIOLATIONS="$VIOLATIONS\n- **Typed Code Violation**: Using 'any' type - use specific types, generics, or unions"
  fi
fi

# Check 2: Magic strings/numbers (potential DRY violation)
MAGIC_COUNT=$(echo "$NEW_CONTENT" | grep -oE "['\"][^'\"]{10,}['\"]" | wc -l)
if [ "$MAGIC_COUNT" -gt 3 ]; then
  VIOLATIONS="$VIOLATIONS\n- **DRY Violation**: $MAGIC_COUNT hardcoded strings detected - consider centralizing in constants"
fi

# Check 3: Large function (potential SRP violation)
LINE_COUNT=$(echo "$NEW_CONTENT" | grep -c "")
if [ "$LINE_COUNT" -gt 50 ]; then
  VIOLATIONS="$VIOLATIONS\n- **SOLID/SRP Warning**: Code block is $LINE_COUNT lines - consider breaking into smaller functions"
fi

# Check 4: Direct database access in non-repository files
if [[ ! "$FILE_PATH" =~ [Rr]epository ]] && [[ ! "$FILE_PATH" =~ /db/ ]] && [[ ! "$FILE_PATH" =~ database ]]; then
  if echo "$NEW_CONTENT" | grep -qE "(db\.|\.query\(|\.execute\(|prisma\.|drizzle\.)"; then
    VIOLATIONS="$VIOLATIONS\n- **Layer Violation**: Direct database access outside repository layer - use Repository pattern"
  fi
fi

# Check 5: Missing error handling
if echo "$NEW_CONTENT" | grep -qE "async\s+function|async\s*\(" ; then
  if ! echo "$NEW_CONTENT" | grep -qE "(try\s*\{|\.catch\(|catch\s*\()"; then
    VIOLATIONS="$VIOLATIONS\n- **Robustness Warning**: Async function without error handling"
  fi
fi

# ============================================
# AGENT ROUTING SUGGESTIONS
# ============================================

SUGGESTED_AGENT=""
ROUTING_REASON=""

# Suggest refactor agent for quality issues
if echo "$VIOLATIONS" | grep -qE "(SRP|DRY|SOLID)"; then
  SUGGESTED_AGENT="refactor"
  ROUTING_REASON="Code quality improvements should use the RefactorAgent which enforces Clean Code principles"
fi

# Suggest architect agent for layer violations
if echo "$VIOLATIONS" | grep -q "Layer Violation"; then
  SUGGESTED_AGENT="architect"
  ROUTING_REASON="Architectural violations should be reviewed by ArchitectAgent first"
fi

# Suggest database agent for database operations
if echo "$NEW_CONTENT" | grep -qE "(migration|schema|CREATE TABLE|ALTER TABLE|drizzle|prisma)"; then
  SUGGESTED_AGENT="database"
  ROUTING_REASON="Database operations should use the DatabaseAgent for safe schema changes"
fi

# Suggest implementation agent for large new features
if [[ "$TOOL_NAME" == "Write" ]] && [ "$LINE_COUNT" -gt 100 ]; then
  SUGGESTED_AGENT="implementation"
  ROUTING_REASON="Large feature implementations should use ImplementationAgent for proper structure"
fi

# ============================================
# OUTPUT DECISION
# ============================================

if [ -n "$VIOLATIONS" ] && [ -n "$SUGGESTED_AGENT" ]; then
  # Block and suggest agent
  cat << EOF
{
  "action": "block",
  "message": "**Code Quality Gate** - Principle violations detected:\n$VIOLATIONS\n\n**Recommended Action**: Delegate to **${SUGGESTED_AGENT}** agent.\n\n$ROUTING_REASON\n\n**To use the agent:**\n\`\`\`\nDelegate to ${SUGGESTED_AGENT} agent for: [describe the task]\n\`\`\`\n\nOr use the slash command: \`/${SUGGESTED_AGENT}\`"
}
EOF
  exit 0
elif [ -n "$VIOLATIONS" ]; then
  # Warn but allow (non-critical violations)
  cat << EOF
{
  "action": "allow",
  "message": "**Code Quality Advisory**:\n$VIOLATIONS\n\nConsider using specialized agents:\n- **/refactor** - For code quality improvements\n- **/architect** - For architectural review\n- **database agent** - For database operations"
}
EOF
  exit 0
else
  # All checks passed
  echo '{"action": "allow"}'
  exit 0
fi
