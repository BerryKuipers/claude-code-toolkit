# Smart Command Resumption System

## State Directory Structure
```
.claude/
├── commands/           # Existing command definitions
└── state/             # NEW: Command state files
    ├── issue-pickup.json
    ├── refactor.json
    ├── pr-process.json
    └── [command-name].json
```

## State File Format
```json
{
  "command": "issue-pickup",
  "timestamp": "2025-09-22T14:30:00Z",
  "arguments": "#123",
  "context": {
    "issueNumber": 123,
    "issueTitle": "Implement user preferences API",
    "branchName": "feature/user-preferences-api",
    "selectedFiles": ["src/services/UserService.ts"]
  },
  "completedSteps": [1, 2, 3, 4],
  "currentStep": 5,
  "stepData": {
    "step3": {
      "analysisResults": "...",
      "implementationPlan": "..."
    }
  },
  "metadata": {
    "estimatedTimeRemaining": "15 minutes",
    "lastActivity": "Completed API endpoint implementation"
  }
}
```

## Command Enhancement Pattern

### 1. Resumption Header (Add to each command)
```markdown
## 🔄 Smart Resumption Check

**BEFORE STARTING ANY WORK:**

1. **Check for existing state:**
   ```bash
   STATE_FILE=".claude/state/[COMMAND_NAME].json"
   if [ -f "$STATE_FILE" ]; then
     echo "📋 Found previous [COMMAND] session:"
     cat "$STATE_FILE" | jq -r '.context, .metadata'
   fi
   ```

2. **If state exists and is recent (< 24 hours):**
   ```
   🔄 Previous [COMMAND] session found:
   📍 Issue: #123 - Implement user preferences API
   🌿 Branch: feature/user-preferences-api
   ✅ Completed: Steps 1-4 (Issue analysis, branch setup, API design, implementation)
   🎯 Next: Step 5 - Testing and validation
   ⏱️  Estimated time remaining: 15 minutes

   Would you like to:
   [R] Resume from Step 5
   [F] Start fresh (clears previous state)
   [V] View full previous context
   ```

3. **User choice handling:**
   - **Resume**: Skip to currentStep, load context variables
   - **Fresh**: Delete state file, start from Step 1
   - **View**: Show full state file contents, then ask again

4. **State updates during execution:**
   ```bash
   # After each major step completion:
   jq '.completedSteps += [STEP_NUMBER] | .currentStep = NEXT_STEP | .timestamp = now' \
      "$STATE_FILE" > tmp.$$ && mv tmp.$$ "$STATE_FILE"
   ```
```

### 2. State Management Functions
```bash
# Helper functions to add to each command

save_command_state() {
  local command_name="$1"
  local step="$2"
  local context="$3"

  mkdir -p ".claude/state"

  cat > ".claude/state/$command_name.json" << EOF
{
  "command": "$command_name",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "arguments": "$ARGUMENTS",
  "context": $context,
  "completedSteps": [$(echo "$COMPLETED_STEPS" | tr ' ' ',')],
  "currentStep": $step,
  "metadata": {
    "lastActivity": "$LAST_ACTIVITY"
  }
}
EOF
}

load_command_state() {
  local command_name="$1"
  local state_file=".claude/state/$command_name.json"

  if [ -f "$state_file" ]; then
    # Check if state is recent (less than 24 hours old)
    local state_age=$(( $(date +%s) - $(date -d "$(jq -r .timestamp "$state_file")" +%s) ))
    if [ $state_age -lt 86400 ]; then
      return 0  # State is valid
    fi
  fi
  return 1  # No valid state
}

clear_command_state() {
  local command_name="$1"
  rm -f ".claude/state/$command_name.json"
}
```

## Implementation Examples

### Enhanced Issue Pickup Command
```markdown
# Issue Pickup Command with Smart Resumption

## 🔄 Smart Resumption Check
[Include resumption header from template above]

### Resumable Step 1: Smart Issue Selection
- **State saved:** Selected issue number, title, priority analysis
- **Resume logic:** If step completed, skip to Step 2 with saved issue context

### Resumable Step 2: Branch Creation and Setup
- **State saved:** Branch name, checkout status
- **Resume logic:** Check if branch exists, verify current branch

### Resumable Step 3: Implementation Planning
- **State saved:** File analysis, implementation plan, architectural decisions
- **Resume logic:** Load previous analysis, continue with implementation

[Continue for each step...]
```

### Enhanced Refactor Command
```markdown
# Clean Code Refactor Command with Smart Resumption

### Resumable Step 1: Target Detection
- **State saved:** Target file/function, refactor strategy
- **Resume logic:** Skip file analysis if target already determined

### Resumable Step 2: Pre-refactor Validation
- **State saved:** Build status, test status, baseline metrics
- **Resume logic:** Quick re-validation or skip if recently passed

[Continue for each step...]
```

## Benefits

1. **Seamless Continuation:** Start exactly where you left off
2. **Context Preservation:** Never lose track of issue numbers, branches, files
3. **Smart Defaults:** Commands auto-populate with previous values
4. **Time Savings:** Skip completed steps, focus on remaining work
5. **Error Recovery:** Resume after fixing blocking issues
6. **Cross-session Support:** Works across different Claude Code sessions

## Usage Examples

```bash
# Starting fresh
/issue-pickup

# Auto-resumes if previous state exists
/issue-pickup

# Force fresh start
/issue-pickup --fresh

# View previous state without resuming
/issue-pickup --status
```