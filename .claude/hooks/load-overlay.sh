#!/usr/bin/env bash
# Load project overlay configuration
# Called from session-start or wrapper commands

set -e

# Detect project name
if [ -n "$CLAUDE_PROJECT" ]; then
  PROJECT_NAME="$CLAUDE_PROJECT"
elif git remote get-url origin &>/dev/null; then
  PROJECT_NAME=$(basename "$(git remote get-url origin)" .git | tr '[:upper:]' '[:lower:]')
else
  PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]')
fi

# Check for overlay
OVERLAY_PATH=".claude/overlays/${PROJECT_NAME}/config.yml"
TOOLKIT_OVERLAY=".claude-toolkit/.claude/overlays/${PROJECT_NAME}/config.yml"

if [ -f "$OVERLAY_PATH" ]; then
  CONFIG_FILE="$OVERLAY_PATH"
elif [ -f "$TOOLKIT_OVERLAY" ]; then
  CONFIG_FILE="$TOOLKIT_OVERLAY"
else
  # No overlay - use defaults
  echo "overlay_status=none"
  echo "project=$PROJECT_NAME"
  exit 0
fi

# Output overlay info (parseable format)
echo "overlay_status=loaded"
echo "project=$PROJECT_NAME"
echo "config_file=$CONFIG_FILE"

# Extract key values if yq is available
if command -v yq &>/dev/null; then
  PREFIX=$(yq -r '.prefix // "bk"' "$CONFIG_FILE" 2>/dev/null)
  ALLOWED=$(yq -r '.allowed_agents | join(",")' "$CONFIG_FILE" 2>/dev/null)
  MCPS=$(yq -r '.enabled_mcp_servers | join(",")' "$CONFIG_FILE" 2>/dev/null)
  COVERAGE=$(yq -r '.thresholds.test_coverage_min // 60' "$CONFIG_FILE" 2>/dev/null)

  echo "prefix=$PREFIX"
  echo "allowed_agents=$ALLOWED"
  echo "enabled_mcp=$MCPS"
  echo "coverage_min=$COVERAGE"
fi
