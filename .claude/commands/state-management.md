# Smart State Management for Command Resumption

## 🗂️ State Lifecycle Management

### Automatic Cleanup on Success ✅

```bash
# At the end of successful command completion
cleanup_on_success() {
  local command_name="$1"
  local state_file=".claude/state/$command_name.json"

  if [ -f "$state_file" ]; then
    echo "🎉 Command completed successfully!"
    echo "🧹 Cleaning up state file..."
    rm -f "$state_file"
    echo "✅ State cleaned - ready for next session"
  fi
}

# Example usage at end of issue-pickup
echo "🎉 Issue #$ISSUE_NUMBER Implementation Complete!"
# ... success message ...
cleanup_on_success "issue-pickup"
```

### Conditional Cleanup on Failure/Interruption ⚠️

```bash
# On command failure or interruption
cleanup_on_failure() {
  local command_name="$1"
  local preserve_state="${2:-ask}"  # ask, keep, clean
  local state_file=".claude/state/$command_name.json"

  case "$preserve_state" in
    "ask")
      echo ""
      echo "❌ Command did not complete successfully"
      echo "❓ Keep state for future resumption?"
      echo "   [K] Keep state (default) - can resume later"
      echo "   [C] Clean state - start fresh next time"
      echo "   [A] Auto-clean after 24 hours"

      # In practice, read user input or use command line flag
      # Default to keeping state for resumption
      ;;
    "keep")
      echo "💾 State preserved for resumption"
      ;;
    "clean")
      rm -f "$state_file"
      echo "🧹 State cleaned"
      ;;
    "auto")
      # Set auto-cleanup timestamp
      jq '.metadata.autoCleanupAt = (now + 86400)' "$state_file" > tmp.$$ && mv tmp.$$ "$state_file"
      echo "⏰ State will auto-clean in 24 hours"
      ;;
  esac
}
```

### Auto-Cleanup of Stale States 🕐

```bash
# Run this periodically or at command start
cleanup_stale_states() {
  local state_dir=".claude/state"
  local current_time=$(date +%s)

  if [ -d "$state_dir" ]; then
    echo "🧹 Checking for stale command states..."

    for state_file in "$state_dir"/*.json; do
      if [ -f "$state_file" ]; then
        # Check for auto-cleanup timestamp
        local auto_cleanup=$(jq -r '.metadata.autoCleanupAt // 0' "$state_file" 2>/dev/null || echo "0")

        if [ "$auto_cleanup" != "0" ] && [ "$current_time" -gt "$auto_cleanup" ]; then
          local command_name=$(basename "$state_file" .json)
          echo "🗑️  Auto-cleaning stale state: $command_name"
          rm -f "$state_file"
        fi

        # Also clean very old states (7+ days) regardless
        local state_time=$(jq -r '.timestamp' "$state_file" 2>/dev/null || echo "")
        if [ -n "$state_time" ]; then
          local state_age=$(( current_time - $(date -d "$state_time" +%s) ))
          if [ "$state_age" -gt 604800 ]; then  # 7 days
            echo "🗑️  Cleaning very old state: $(basename "$state_file" .json) ($(($state_age / 86400)) days old)"
            rm -f "$state_file"
          fi
        fi
      fi
    done
  fi
}
```

## 🤝 User Confirmation Patterns

### Smart Resume Detection with Clear Options

```bash
# When command starts and state is detected
handle_resume_detection() {
  local command_name="$1"
  local state_file=".claude/state/$command_name.json"

  if [ -f "$state_file" ]; then
    # Load basic info for display
    local issue_num=$(jq -r '.context.issueNumber // "N/A"' "$state_file")
    local last_activity=$(jq -r '.metadata.lastActivity // "Unknown"' "$state_file")
    local completed_steps=$(jq -r '.completedSteps | length' "$state_file")
    local current_step=$(jq -r '.currentStep' "$state_file")
    local timestamp=$(jq -r '.timestamp' "$state_file")

    echo "🔄 PREVIOUS SESSION DETECTED"
    echo "================================"
    echo "📋 Command: $command_name"
    echo "🎯 Context: Issue #$issue_num"
    echo "📍 Progress: $completed_steps steps completed, currently at step $current_step"
    echo "⏱️  Last activity: $last_activity"
    echo "📅 Started: $timestamp"
    echo ""

    # Handle command line arguments first
    case "$1" in
      --resume|-r)     return 0;;  # Auto-resume
      --fresh|-f)      rm -f "$state_file"; return 1;;  # Auto-fresh
      --status|-s)     show_detailed_status "$state_file"; exit 0;;
    esac

    # Interactive prompt if no command line arg
    echo "🤔 What would you like to do?"
    echo "   [R] Resume from step $current_step (recommended)"
    echo "   [F] Start fresh (clears previous state)"
    echo "   [S] Show detailed status"
    echo "   [Q] Quit (preserves state)"
    echo ""
    echo "💡 Tip: Use --resume/-r or --fresh/-f flags to skip this prompt"
    echo ""

    # In practice, read user input
    # For demo purposes, default to resume
    local choice="${RESUME_CHOICE:-R}"

    case "$choice" in
      R|r|"")  echo "▶️  Resuming from step $current_step"; return 0;;
      F|f)     echo "🆕 Starting fresh"; rm -f "$state_file"; return 1;;
      S|s)     show_detailed_status "$state_file"; return 2;;  # Show status and ask again
      Q|q)     echo "👋 Keeping state for later"; exit 0;;
      *)       echo "❓ Invalid choice, defaulting to resume"; return 0;;
    esac
  fi

  return 1  # No state found
}
```

### Non-Intrusive Status Checking

```bash
# Quick status without full resumption prompt
show_quick_status() {
  local command_name="$1"
  local state_file=".claude/state/$command_name.json"

  if [ -f "$state_file" ]; then
    echo "📊 Current $command_name status:"
    jq -r '"  🎯 Context: " + (.context.issueNumber // "N/A") + " - " + (.context.issueTitle // "N/A")' "$state_file"
    jq -r '"  📍 Step: " + (.currentStep | tostring) + " - " + (.metadata.lastActivity // "Unknown")' "$state_file"
    jq -r '"  ⏱️  Time: " + (.timestamp // "Unknown")' "$state_file"
  else
    echo "📊 No active $command_name session"
  fi
}
```

## 🚀 Enhanced Command Line Interface

### Smart Command Line Options

```bash
# Add these to all resumable commands
parse_resumption_args() {
  local command_name="$1"
  shift  # Remove command name from args

  case "$1" in
    --resume|-r)
      RESUMPTION_MODE="auto-resume"
      RESUMPTION_ARGS="$2"  # Optional: specific step number
      ;;
    --fresh|-f)
      RESUMPTION_MODE="fresh"
      ;;
    --status|-s)
      show_quick_status "$command_name"
      exit 0
      ;;
    --detailed-status|-ds)
      show_detailed_status ".claude/state/$command_name.json"
      exit 0
      ;;
    --clean-state|-cs)
      rm -f ".claude/state/$command_name.json"
      echo "🧹 State cleaned for $command_name"
      exit 0
      ;;
    --help|-h)
      show_resumption_help "$command_name"
      exit 0
      ;;
    --validate|-v)
      validate_resumption_context "$command_name"
      exit $?
      ;;
    *)
      # No resumption flag - let normal detection handle it
      RESUMPTION_MODE="detect"
      ;;
  esac
}
```

### Usage Examples

```bash
# Different ways to use resumable commands

# 1. Smart detection (prompts if state found)
/issue-pickup

# 2. Auto-resume (skips prompt)
/issue-pickup --resume
/issue-pickup -r

# 3. Force fresh start
/issue-pickup --fresh
/issue-pickup -f

# 4. Check status without resuming
/issue-pickup --status
/issue-pickup -s

# 5. Detailed status view
/issue-pickup --detailed-status
/issue-pickup -ds

# 6. Clean old state
/issue-pickup --clean-state
/issue-pickup -cs

# 7. Validate context before resuming
/issue-pickup --validate
/issue-pickup -v

# 8. Resume from specific step (advanced)
/issue-pickup --resume 8

# 9. Show help
/issue-pickup --help
/issue-pickup -h
```

## 🔧 Maintenance and Monitoring

### State Directory Health Check

```bash
# Add to your regular maintenance
check_state_health() {
  local state_dir=".claude/state"

  if [ -d "$state_dir" ]; then
    local total_states=$(find "$state_dir" -name "*.json" | wc -l)
    local old_states=$(find "$state_dir" -name "*.json" -mtime +3 | wc -l)
    local very_old_states=$(find "$state_dir" -name "*.json" -mtime +7 | wc -l)

    echo "📊 Command State Health Report:"
    echo "   Total active states: $total_states"
    echo "   States >3 days old: $old_states"
    echo "   States >7 days old: $very_old_states (will auto-clean)"

    if [ "$very_old_states" -gt 0 ]; then
      echo "🧹 Cleaning very old states..."
      cleanup_stale_states
    fi
  else
    echo "📊 No command states directory found (clean slate)"
  fi
}
```

### Monitoring Commands

```bash
# New utility commands you can create

# Show all active command states
/claude-status

# Clean all old states
/claude-cleanup

# Show state directory health
/claude-health
```

## 📋 Integration Checklist

When adding resumption to a command:

- [ ] ✅ Add state directory to .gitignore
- [ ] ✅ Implement save_command_state() function
- [ ] ✅ Implement load_command_state() function
- [ ] ✅ Add resumption detection at command start
- [ ] ✅ Add state saves after each major step
- [ ] ✅ Add cleanup_on_success() at command end
- [ ] ✅ Add cleanup_on_failure() for error handling
- [ ] ✅ Add command line options (--resume, --fresh, --status)
- [ ] ✅ Add user confirmation prompts with clear options
- [ ] ✅ Add context validation for resume safety
- [ ] ✅ Add stale state auto-cleanup
- [ ] ✅ Test interruption and resumption scenarios

## 🎯 Benefits Summary

**For Users:**
- Never lose progress on complex commands
- Clear, non-intrusive resumption prompts
- Flexible control via command line flags
- Smart defaults that "just work"

**For System:**
- Automatic cleanup prevents state bloat
- .gitignore prevents commit pollution
- Graceful error handling and recovery
- Extensible pattern for all commands

This system balances **convenience** with **control**, giving users the power to resume seamlessly while maintaining system cleanliness.