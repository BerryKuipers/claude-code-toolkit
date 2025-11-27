#!/bin/bash
# PostToolUse Hook: Quality Gate Validation
# Runs AFTER Edit/Write to validate code quality
# Provides feedback to Claude about quality issues

TOOL_NAME="$1"
TOOL_ARGS="$2"

# Get project root
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Only validate Edit and Write operations on code files
if [[ "$TOOL_NAME" != "Edit" ]] && [[ "$TOOL_NAME" != "Write" ]]; then
  echo '{"action": "continue"}'
  exit 0
fi

# Extract file path (use jq for reliable JSON parsing)
FILE_PATH=$(echo "$TOOL_ARGS" | jq -r '.file_path // ""' 2>/dev/null)
if [ -z "$FILE_PATH" ]; then
  # Fallback to regex if jq fails
  FILE_PATH=$(echo "$TOOL_ARGS" | grep -oE '"file_path"\s*:\s*"[^"]+' | sed 's/"file_path"\s*:\s*"//')
fi

# Skip non-code files
case "$FILE_PATH" in
  *.md|*.txt|*.json|*.yml|*.yaml|*.toml|*.lock|*.css|*.scss|*.html)
    echo '{"action": "continue"}'
    exit 0
    ;;
esac

# Skip if file doesn't exist (failed write)
if [ ! -f "$FILE_PATH" ]; then
  echo '{"action": "continue"}'
  exit 0
fi

ISSUES=""

# ============================================
# TypeScript Type Check (if applicable)
# ============================================
# NOTE: Single-file tsc checks produce false positives without project context.
# We skip the automatic check here and recommend running full project validation.
# Users should run `npm run typecheck` or `npx tsc --noEmit` manually for accurate results.
if [[ "$FILE_PATH" =~ \.(ts|tsx)$ ]]; then
  # Check if tsconfig exists (use ls for glob expansion instead of [ -f ] which doesn't expand)
  if [ -f "$PROJECT_DIR/tsconfig.json" ] || ls "$PROJECT_DIR"/packages/*/tsconfig.json >/dev/null 2>&1; then
    # Add reminder to run full type check (don't auto-run as it's slow and single-file is unreliable)
    ISSUES="$ISSUES\n- **TypeScript**: Run \`npx tsc --noEmit\` to verify types across project"
  fi
fi

# ============================================
# ESLint Check (if applicable)
# ============================================
if [[ "$FILE_PATH" =~ \.(ts|tsx|js|jsx)$ ]]; then
  if [ -f "$PROJECT_DIR/.eslintrc.json" ] || [ -f "$PROJECT_DIR/.eslintrc.js" ] || [ -f "$PROJECT_DIR/eslint.config.js" ]; then
    LINT_ERRORS=$(npx eslint "$FILE_PATH" --format compact 2>&1 | grep -c "error" || true)
    if [ "$LINT_ERRORS" -gt 0 ]; then
      ISSUES="$ISSUES\n- **ESLint Errors**: $LINT_ERRORS lint errors in modified file"
    fi
  fi
fi

# ============================================
# Code Metrics Analysis
# ============================================

# Check file length (SRP warning)
TOTAL_LINES=$(wc -l < "$FILE_PATH" 2>/dev/null || echo "0")
if [ "$TOTAL_LINES" -gt 300 ]; then
  ISSUES="$ISSUES\n- **File Size Warning**: File is $TOTAL_LINES lines - consider splitting into modules"
fi

# Check function count (SRP indicator)
if [[ "$FILE_PATH" =~ \.(ts|tsx|js|jsx)$ ]]; then
  FUNCTION_COUNT=$(grep -cE "(function\s+\w+|=>\s*\{|async\s+function)" "$FILE_PATH" 2>/dev/null || echo "0")
  if [ "$FUNCTION_COUNT" -gt 15 ]; then
    ISSUES="$ISSUES\n- **Module Complexity**: $FUNCTION_COUNT functions in file - consider extracting to separate modules"
  fi
fi

# Check for TODO/FIXME/HACK comments
DEBT_MARKERS=$(grep -cE "(TODO|FIXME|HACK|XXX):" "$FILE_PATH" 2>/dev/null || echo "0")
if [ "$DEBT_MARKERS" -gt 0 ]; then
  ISSUES="$ISSUES\n- **Tech Debt Markers**: $DEBT_MARKERS TODO/FIXME/HACK comments found"
fi

# ============================================
# Log to quality audit trail
# ============================================
mkdir -p "$PROJECT_DIR/.claude/logs"
{
  echo "[$(date -Iseconds)] PostToolUse Quality Check"
  echo "  File: $FILE_PATH"
  echo "  Tool: $TOOL_NAME"
  if [ -n "$ISSUES" ]; then
    echo "  Issues Found:"
    echo -e "$ISSUES"
  else
    echo "  Status: PASSED"
  fi
  echo ""
} >> "$PROJECT_DIR/.claude/logs/quality-gate.log"

# ============================================
# Output Decision
# ============================================

if [ -n "$ISSUES" ]; then
  # Report issues to Claude (context injection)
  cat << EOF
{
  "action": "continue",
  "additionalContext": "\n\n**Quality Gate Report for \`$FILE_PATH\`**:\n$ISSUES\n\n**Recommended Actions**:\n- Use \`/refactor\` command to address code quality issues\n- Use \`/architect\` command for structural review\n- Run \`npm run lint:fix\` to auto-fix lint errors\n- Run \`npx tsc --noEmit\` to check all type errors"
}
EOF
else
  echo '{"action": "continue"}'
fi
exit 0
