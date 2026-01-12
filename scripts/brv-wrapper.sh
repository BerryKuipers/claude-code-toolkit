#!/usr/bin/env bash
#
# brv-wrapper.sh - Optional ByteRover CLI wrapper for toolkit projects
#
# This script provides a project-agnostic wrapper for ByteRover CLI.
# It handles availability checking and graceful fallback.
#
# Usage:
#   source brv-wrapper.sh      # Load functions
#   brv_available              # Returns 0 if brv is available
#   brv_run query "..."        # Run brv command with fallback
#   brv_or_skip query "..."    # Run if available, skip otherwise
#
# This file is part of claude-code-toolkit and is project-agnostic.
# Projects should NOT modify this file; instead, create project-local
# wrappers that source this script and add project-specific logic.

# Check if brv is available (global or npx)
brv_available() {
  if command -v brv &>/dev/null; then
    return 0
  fi
  if command -v npx &>/dev/null && npx --yes byterover-cli --version &>/dev/null 2>&1; then
    return 0
  fi
  return 1
}

# Get the brv command to use (returns empty if not available)
brv_cmd() {
  if command -v brv &>/dev/null; then
    echo "brv"
  elif command -v npx &>/dev/null; then
    echo "npx --yes byterover-cli"
  else
    echo ""
  fi
}

# Run brv command, returns 1 if not available
brv_run() {
  local cmd
  cmd=$(brv_cmd)
  if [ -z "$cmd" ]; then
    echo "[brv-wrapper] ByteRover CLI not available" >&2
    return 1
  fi
  $cmd "$@"
}

# Run brv if available, silently skip if not
brv_or_skip() {
  local cmd
  cmd=$(brv_cmd)
  if [ -z "$cmd" ]; then
    return 0  # Silent skip
  fi
  $cmd "$@"
}

# Print availability status
brv_status() {
  if brv_available; then
    local cmd
    cmd=$(brv_cmd)
    local version
    version=$($cmd --version 2>/dev/null || echo "unknown")
    echo "[brv] Available: $cmd (v$version)"
    return 0
  else
    echo "[brv] Not available"
    echo "      Install: npm install -g byterover-cli"
    return 1
  fi
}

# Export functions if sourced
export -f brv_available brv_cmd brv_run brv_or_skip brv_status 2>/dev/null || true
