# Shared Workspace Auto-Cleanup System

## 🧹 Automatic Workspace Management

Prevents workspace accumulation by intelligently cleaning up collaborative workspaces when tasks complete.

## 🔄 Cleanup Implementation

### In Orchestrator - Session Completion
```bash
### Workspace Cleanup on Session End (NEW)

CLEANUP_COLLABORATIVE_WORKSPACE() {
  local SESSION_ID="$1"
  local WORKSPACE_PATH="/tmp/orchestrator-$SESSION_ID"

  if [[ -d "$WORKSPACE_PATH" ]]; then
    echo "🧹 Cleaning up collaborative workspace: $SESSION_ID"

    # Archive important results before cleanup
    ARCHIVE_DIR=".claude/orchestrator-sessions/$(date +%Y%m)"
    mkdir -p "$ARCHIVE_DIR"

    # Save final results and context
    if [[ -f "$WORKSPACE_PATH/final-report.json" ]]; then
      cp "$WORKSPACE_PATH/final-report.json" "$ARCHIVE_DIR/session-$SESSION_ID-results.json"
    fi

    # Save collaboration outcomes
    if [[ -d "$WORKSPACE_PATH/collaborative" ]]; then
      tar -czf "$ARCHIVE_DIR/session-$SESSION_ID-collaboration.tar.gz" -C "$WORKSPACE_PATH" collaborative/
    fi

    # Remove temporary workspace
    rm -rf "$WORKSPACE_PATH"
    echo "✅ Workspace cleaned up, results archived to $ARCHIVE_DIR"
  fi
}

# Call cleanup at end of orchestrator session
trap 'CLEANUP_COLLABORATIVE_WORKSPACE "$SESSION_ID"' EXIT
```

### Scheduled Cleanup for Orphaned Workspaces
```bash
### Periodic Cleanup of Stale Workspaces (Background)

CLEANUP_STALE_WORKSPACES() {
  local MAX_AGE_HOURS="${1:-24}"  # Default 24 hours

  echo "🕒 Checking for stale workspaces older than $MAX_AGE_HOURS hours..."

  # Find workspaces older than specified age
  STALE_WORKSPACES=$(find /tmp -name "orchestrator-*" -type d -mtime "+$(echo "$MAX_AGE_HOURS/24" | bc)" 2>/dev/null)

  if [[ -n "$STALE_WORKSPACES" ]]; then
    echo "📋 Found stale workspaces:"
    echo "$STALE_WORKSPACES" | sed 's/^/  → /'

    echo "$STALE_WORKSPACES" | while read -r workspace; do
      if [[ -d "$workspace" ]]; then
        SESSION_ID=$(basename "$workspace" | sed 's/orchestrator-//')

        # Archive before cleanup
        ARCHIVE_DIR=".claude/orchestrator-sessions/$(date +%Y%m)/stale"
        mkdir -p "$ARCHIVE_DIR"

        # Quick archive of the entire workspace
        tar -czf "$ARCHIVE_DIR/stale-session-$SESSION_ID-$(date +%H%M).tar.gz" -C "$(dirname "$workspace")" "$(basename "$workspace")"

        # Remove stale workspace
        rm -rf "$workspace"
        echo "🗑️  Cleaned up stale workspace: $SESSION_ID"
      fi
    done
  else
    echo "✅ No stale workspaces found"
  fi
}

# Run cleanup automatically (can be called by cron or system scheduler)
# CLEANUP_STALE_WORKSPACES 12  # Clean workspaces older than 12 hours
```

## 📦 Archive Management
```bash
### Archive Management to Prevent Disk Bloat

MANAGE_ARCHIVED_SESSIONS() {
  local ARCHIVE_BASE=".claude/orchestrator-sessions"
  local MAX_ARCHIVE_AGE_DAYS="${1:-30}"  # Keep archives for 30 days

  echo "📦 Managing archived sessions (keeping last $MAX_ARCHIVE_AGE_DAYS days)"

  # Clean old archives
  find "$ARCHIVE_BASE" -name "*.json" -o -name "*.tar.gz" -mtime "+$MAX_ARCHIVE_AGE_DAYS" -delete 2>/dev/null

  # Clean empty directories
  find "$ARCHIVE_BASE" -type d -empty -delete 2>/dev/null

  # Show current archive usage
  if [[ -d "$ARCHIVE_BASE" ]]; then
    ARCHIVE_SIZE=$(du -sh "$ARCHIVE_BASE" 2>/dev/null | cut -f1)
    ARCHIVE_COUNT=$(find "$ARCHIVE_BASE" -type f | wc -l)
    echo "📊 Archive status: $ARCHIVE_SIZE used, $ARCHIVE_COUNT files"
  fi
}
```