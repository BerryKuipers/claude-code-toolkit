# Smart Resumption System for Claude Code Commands

## 📋 **Copy-Paste Integration Template**

Add this to the beginning of ANY command:

```markdown
## 🔄 Smart Resumption Check

**BEFORE STARTING ANY WORK:**

1. **Check for existing state:**
   ```bash
   STATE_FILE=".claude/state/[COMMAND_NAME].json"
   if [ -f "$STATE_FILE" ]; then
     echo "📋 Found previous [COMMAND_NAME] session:"
     echo "🎯 Context: $(jq -r '.context.issueNumber // .context.targetFile // .context.prNumber // "N/A"' "$STATE_FILE")"
     echo "📍 Progress: $(jq -r '.completedSteps | length' "$STATE_FILE") steps completed"
     echo "🕒 Started: $(jq -r '.timestamp' "$STATE_FILE")"
   fi
   ```

2. **Handle user choice:**
   ```
   🔄 Previous session found. What would you like to do?
   [R] Resume from step $(jq -r '.currentStep' "$STATE_FILE")
   [F] Start fresh (clears previous state)
   [S] Show detailed status
   ```

3. **State management functions:**
   ```bash
   # Save step completion
   save_step() {
     local step="$1"
     local activity="$2"
     local context="$3"

     mkdir -p ".claude/state"
     cat > ".claude/state/[COMMAND_NAME].json" << EOF
   {
     "command": "[COMMAND_NAME]",
     "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
     "arguments": "$ARGUMENTS",
     "context": $context,
     "completedSteps": [$(echo "$COMPLETED_STEPS" | tr ' ' ',')],
     "currentStep": $(($step + 1)),
     "metadata": {"lastActivity": "$activity"}
   }
   EOF
     COMPLETED_STEPS="$COMPLETED_STEPS $step"
   }

   # Check if step should be skipped
   should_skip_step() {
     local step="$1"
     [[ " $COMPLETED_STEPS " =~ " $step " ]]
   }

   # Clean up on success
   cleanup_on_success() {
     rm -f ".claude/state/[COMMAND_NAME].json"
     echo "🧹 State cleaned - ready for next session"
   }
   ```

4. **Load previous state if resuming:**
   ```bash
   if [ -f "$STATE_FILE" ] && [[ "$RESUME_CHOICE" == "R" ]]; then
     COMPLETED_STEPS=$(jq -r '.completedSteps | join(" ")' "$STATE_FILE")
     CURRENT_STEP=$(jq -r '.currentStep' "$STATE_FILE")
     # Load context variables...
   fi
   ```
```

## 🎯 **Step Integration Pattern**

For each major step in your command, wrap it like this:

```markdown
### Step X: [Step Name]

```bash
if should_skip_step X; then
  echo "⏭️  Skipping Step X (already completed)"
else
  echo "▶️  Executing Step X: [Step Name]"

  # ORIGINAL STEP LOGIC HERE

  # Save completion
  save_step X "Step X completed: [description]" '{"stepData": "value"}'
fi
```

# Continue with original step content...
```

## 🔗 **Real Integration Examples**

### Enhanced Issue Pickup Command

```markdown
# Issue Pickup Command with Smart Resumption

[Copy the resumption template above, replace [COMMAND_NAME] with "issue-pickup"]

## Instructions

**Issue to pick up:** $ARGUMENTS

### Step 1: Smart Issue Selection and Analysis

```bash
if should_skip_step 1; then
  echo "⏭️  Issue already selected: #$(jq -r '.context.issueNumber' "$STATE_FILE")"
  ISSUE_NUMBER=$(jq -r '.context.issueNumber' "$STATE_FILE")
  ISSUE_TITLE=$(jq -r '.context.issueTitle' "$STATE_FILE")
else
  echo "▶️  Selecting and analyzing issue..."
```

If $ARGUMENTS is provided, use that issue number. Otherwise:

1. **Fetch and analyze all open issues:**
   ```bash
   gh issue list --state open --limit 100 --json number,title,labels,assignees,createdAt,body
   ```

[Original Step 1 logic...]

```bash
  # Save step completion
  save_step 1 "Issue selected and analyzed" '{
    "issueNumber": '$ISSUE_NUMBER',
    "issueTitle": "'$ISSUE_TITLE'",
    "priority": "'$PRIORITY'",
    "reasoning": "'$SELECTION_REASONING'"
  }'
fi
```

### Step 2: AI Analysis Integration and Validation

```bash
if should_skip_step 2; then
  echo "⏭️  AI analysis already completed"
else
  echo "▶️  Running AI analysis..."
```

[Original Step 2 logic...]

```bash
  save_step 2 "AI analysis completed and validated" '{
    "aiAnalysisComplete": true,
    "analysisInsights": "'$AI_INSIGHTS'"
  }'
fi
```

[Continue for all 15 steps...]

### Final Success Message

```bash
cleanup_on_success

echo "🎉 Issue #$ISSUE_NUMBER Implementation Complete!"
# ... rest of success message
```
```

### Enhanced Refactor Command

```markdown
# Clean Code Refactor Command with Smart Resumption

[Copy the resumption template, replace [COMMAND_NAME] with "refactor"]

**Arguments:**
- `target` *(optional)*: file/class/function path (auto-detected if not provided)

### Step 0: Pre-Refactor System Validation

```bash
if should_skip_step 0; then
  echo "⏭️  System validation already passed"
  TARGET_FILE=$(jq -r '.context.targetFile' "$STATE_FILE")
else
  echo "▶️  Validating system before refactoring..."
```

```bash
# CRITICAL: Validate TypeScript paths and build state BEFORE starting
echo "🔍 Pre-refactor system validation..."
```

[Original Step 0 logic...]

```bash
  save_step 0 "System validation completed" '{
    "targetFile": "'$TARGET_FILE'",
    "strategy": "'$STRATEGY'",
    "validationPassed": true
  }'
fi
```

[Continue for all 16 steps...]

### Final Success

```bash
cleanup_on_success
echo "🎉 Refactor completed successfully!"
```
```

## 📋 **Quick Migration Checklist**

For each command:

1. **Add resumption header** (copy template, replace [COMMAND_NAME])
2. **Wrap each major step** with `if should_skip_step X; then ... else ... fi`
3. **Add save_step calls** after each step completion
4. **Add cleanup_on_success** at the end
5. **Test with interruption and resume**

## 🎮 **Command Line Usage**

```bash
# Smart detection (prompts if state found)
/issue-pickup

# Command line options for non-interactive use
/issue-pickup # then choose R/F/S when prompted

# Quick status check
/issue-pickup
# If state exists, choose [S] for status

# Force fresh start
/issue-pickup
# If state exists, choose [F] for fresh
```

## 💡 **Benefits**

1. **Never lose progress** - Pick up exactly where you left off
2. **Context preservation** - Issue numbers, file paths, branches remembered
3. **Cross-session support** - Resume after restarting Claude Code
4. **Smart defaults** - Commands auto-populate with previous context
5. **Clean integration** - 3 lines to add, works with existing logic
6. **User control** - Always asks permission before resuming

## 🔧 **Maintenance**

- State files auto-clean on successful completion
- Old states (7+ days) can be manually cleaned from `.claude/state/`
- `.claude/state/` and `.claude/learning/` are in `.gitignore`
- No shell scripts needed - pure markdown instructions for Claude

**Result: Any complex command becomes resumable with just 3 additions!** 🚀