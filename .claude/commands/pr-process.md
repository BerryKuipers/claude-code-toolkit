# PR Processing Command

Complete end-to-end processing of a Pull Request including review, merge, testing, and validation with critical analysis of AI feedback.

## Instructions

**PR to process:** $ARGUMENTS (if no arguments provided, auto-select best PR)

## 🔄 Smart Resumption Check

```bash
STATE_FILE=".claude/state/pr-process.json"

# Check for existing state
if [ -f "$STATE_FILE" ]; then
  echo "🔄 Previous pr-process session found:"
  echo "🎯 PR: #$(jq -r '.context.prNumber // "N/A"' "$STATE_FILE") - $(jq -r '.context.prTitle // "Unknown"' "$STATE_FILE")"
  echo "🌿 Branch: $(jq -r '.context.branchName // "N/A"' "$STATE_FILE")"
  echo "📍 Progress: $(jq -r '.completedSteps | length' "$STATE_FILE") steps completed, currently at step $(jq -r '.currentStep' "$STATE_FILE")"
  echo "🕒 Started: $(jq -r '.timestamp' "$STATE_FILE")"
  echo ""
  echo "Resume from step $(jq -r '.currentStep' "$STATE_FILE")? [R/F/S]"
  echo "R=Resume, F=Fresh start, S=Show status"

  case "$RESUME_CHOICE" in
    F|f) rm -f "$STATE_FILE"; echo "🆕 Starting fresh";;
    S|s) cat "$STATE_FILE" | jq '.'; exit 0;;
    *) echo "▶️ Resuming from step $(jq -r '.currentStep' "$STATE_FILE")...";
       COMPLETED_STEPS=$(jq -r '.completedSteps | join(" ")' "$STATE_FILE");
       PR_NUMBER=$(jq -r '.context.prNumber' "$STATE_FILE");
       PR_TITLE=$(jq -r '.context.prTitle' "$STATE_FILE");
       BRANCH_NAME=$(jq -r '.context.branchName' "$STATE_FILE");;
  esac
fi

# Helper functions
should_skip_step() { [[ " $COMPLETED_STEPS " =~ " $1 " ]]; }
save_step() {
  mkdir -p ".claude/state"
  cat > "$STATE_FILE" << EOF
{
  "command": "pr-process",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "arguments": "$ARGUMENTS",
  "context": $3,
  "completedSteps": [$(echo "$COMPLETED_STEPS $1" | tr ' ' ',' | sed 's/^,//')],
  "currentStep": $(($1 + 1)),
  "metadata": {"lastActivity": "$2"}
}
EOF
  COMPLETED_STEPS="$COMPLETED_STEPS $1"
  echo "💾 Step $1 completed: $2"
}
```

### Step 1: Determine Target PR

```bash
if should_skip_step 1; then
  echo "⏭️ Step 1 already completed - PR #$PR_NUMBER selected"
else
```
If $ARGUMENTS is provided, use that PR number. Otherwise:
1. Run `gh pr list --state open --json number,title,headRefName,createdAt` to get all open PRs
2. Get current branch with `git branch --show-current`
3. Auto-select PR using priority:
   - Current branch PR (highest priority)
   - Bug fixes (`fix`, `bug` in title) over features
   - Issue-linked PRs (contain `#` in title)
   - Most recent within same priority

### Step 2: Switch to PR Branch and Merge Development
1. Run `git checkout [PR_BRANCH]` to switch to the PR branch
2. Run `git pull origin [PR_BRANCH]` to get latest changes
3. Run `git fetch origin development` to get latest development
4. Run `git merge origin/development` to merge development into PR branch
5. If merge conflicts occur, list the conflicted files and ask for manual resolution

### Step 3: Critical Analysis of Gemini Comments
1. Run `gh pr view [PR_NUMBER] --json reviews` to get PR reviews
2. Run `gh api repos/[OWNER]/[REPO]/pulls/[PR_NUMBER]/comments` to get review comments
3. Filter for Gemini/AI comments containing "suggestion" or "fix"
4. For each Gemini comment found:
   - **Display the comment content**
   - **Analyze critically:**
     - Does this address the root cause or just symptoms?
     - Are there better alternative solutions?
     - Does it align with TribeVibe's architecture patterns?
     - Could it introduce new issues or side effects?
     - Is the solution complete?
   - **Pause for manual review** before implementing any suggestions
   - **If implementing suggestions:**
     - Commit changes with proper verification (check git status after commit)
     - If commit fails, analyze and address pre-commit hook failures
     - Only push after successful commit verification
5. **IMPORTANT:** Don't blindly apply AI suggestions - require human judgment

### Step 4: Build and Test
1. Run `npm run build` to ensure all packages compile
2. If build fails, analyze errors and fix issues before proceeding
3. Report build status and any issues found

### Step 5: Code Quality Audit
1. Run `npm run audit` to execute the comprehensive audit agent
2. Review audit results and address any critical issues
3. Ensure architecture compliance score is acceptable

### Step 6: Commit and Push Changes
1. Run `git status` to see all changes
2. Run `git add .` to stage changes
3. Create conventional commit with format:
   ```
   fix: process PR #[NUMBER] - [PR_TITLE]

   🤖 Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```
4. **Verify commit success** before pushing:
   - Check git status to confirm commit completed
   - If commit failed due to pre-commit hooks, analyze the failure
   - If audit issues found, address them and retry commit
   - Only proceed to push after successful commit
5. Run `git push origin [PR_BRANCH]` to push changes

### Step 7: Resolve Gemini Conversations
1. Check if `scripts/resolve-pr-conversations.ps1` exists
2. If exists, run `powershell "scripts/resolve-pr-conversations.ps1 -PrNumber [PR_NUMBER]"`
3. This marks Gemini conversations as resolved on GitHub

### Step 8: Runtime Verification
1. Start development server with `npm run dev` in background
2. Wait 30 seconds for startup
3. Check if API starts without errors
4. Report any startup issues

### Step 9: Manual UI Verification Request
Display message: "⏳ Please verify UI works at http://localhost:3004 and confirm when ready to proceed"
Wait for user confirmation before continuing.

### Step 10: Real-Time CI Monitoring
**CRITICAL: Actively monitor CI in real-time using the dedicated `/ci-monitor` command**

```bash
echo "🔄 Starting real-time CI monitoring for PR #${PR_NUMBER}..."

# Get latest workflow run for the branch
LATEST_RUN_ID=$(gh run list --branch="${BRANCH_NAME}" --limit=1 --json=databaseId --jq='.[0].databaseId')

if [[ -z "$LATEST_RUN_ID" || "$LATEST_RUN_ID" == "null" ]]; then
  echo "⚠️ No CI run found for branch ${BRANCH_NAME}"
  echo "📊 Checking PR-level status instead..."
  gh pr checks ${PR_NUMBER}
  exit 0
fi

echo "📊 Monitoring CI Run #${LATEST_RUN_ID} for branch ${BRANCH_NAME}"
echo "🔗 View in GitHub: https://github.com/BerryKuipers/TribeVibe/actions/runs/${LATEST_RUN_ID}"
echo ""

# Use gh run watch for real-time monitoring (blocks until completion)
echo "👁️ Watching CI run in real-time (this will block until completion)..."
gh run watch "${LATEST_RUN_ID}" 2>&1 | tee /tmp/ci-watch-${LATEST_RUN_ID}.log

# Check final status after watch completes
FINAL_STATUS=$(gh run view "${LATEST_RUN_ID}" --json=conclusion --jq='.conclusion')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

case "$FINAL_STATUS" in
  "success")
    echo "✅ CI PASSED - All checks successful!"
    echo "🎉 PR #${PR_NUMBER} is ready for review/merge"
    ;;
  "failure")
    echo "❌ CI FAILED - One or more checks failed"
    echo "📋 Failed checks:"
    gh pr checks ${PR_NUMBER} | grep -E "fail|failure" || echo "  (See GitHub Actions for details)"
    echo ""
    echo "💡 Options:"
    echo "  1. Run /ci-test-fixer to automatically fix test failures"
    echo "  2. Run /ci-monitor --watch --auto-fix for continuous monitoring with auto-fix"
    echo "  3. Check logs: cat /tmp/ci-watch-${LATEST_RUN_ID}.log"
    exit 1
    ;;
  "cancelled")
    echo "⏹️ CI CANCELLED - Workflow was cancelled"
    exit 1
    ;;
  *)
    echo "⚠️ CI STATUS UNKNOWN: ${FINAL_STATUS}"
    gh pr checks ${PR_NUMBER}
    ;;
esac

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

**Alternative: Background monitoring with dedicated agent**
```bash
# For non-blocking workflows, delegate to ci-monitor agent
echo "📊 Starting background CI monitoring with auto-fix..."
SlashCommand("/ci-monitor --watch --branch=${BRANCH_NAME} --auto-fix") &
MONITOR_PID=$!

echo "🔄 CI monitoring running in background (PID: $MONITOR_PID)"
echo "📝 To check status: ps -p $MONITOR_PID"
echo "🛑 To stop monitoring: kill $MONITOR_PID"
echo "🔗 GitHub Actions: https://github.com/BerryKuipers/TribeVibe/actions"
```

### Final Result

```bash
# Clean up state on successful completion
rm -f ".claude/state/pr-process.json"
echo "🧹 PR processing complete - state cleaned"
```

If all steps complete successfully, display:
```
🎉 PR #[NUMBER] is ready for merge!
✅ All steps completed successfully
✅ Code quality verified
✅ Runtime functionality confirmed
✅ CI checks passing
```

## Critical Analysis Framework
**For Gemini comments, always evaluate:**
- **Root Cause**: Does it solve the actual problem?
- **Alternatives**: Are there better approaches?
- **Architecture**: Does it fit TribeVibe patterns?
- **Side Effects**: Could it cause new issues?
- **Completeness**: Is it a complete solution?

**⚠️ Require manual review before implementing any AI suggestions.**

## Handling Pre-commit Hook Failures

When commits fail due to pre-commit hooks (audit, lint, etc.):

1. **Check git status** - confirm no commit was created
2. **Analyze failure output** - identify specific issues (audit score, lint errors, etc.)
3. **Address root causes**:
   - Low audit scores: Review and fix code quality issues
   - Lint errors: Run `npm run lint:fix` or fix manually
   - Build failures: Fix compilation errors
4. **Re-run audit if needed**: `npm run audit` to verify fixes
5. **Retry commit** once issues are resolved
6. **Verify success** before proceeding to push

## Command Evaluation and Self-Improvement

After each PR processing session, the command evaluates its effectiveness and automatically improves:

```bash
# Evaluation metrics tracked:
# - Total processing time from start to merge
# - Number of review iterations required
# - Pre-commit hook failure rate and resolution time
# - Test suite execution success rate
# - AI suggestion quality and implementation rate
# - Merge conflicts encountered and resolution efficiency

# Auto-improvements applied:
# - Enhanced pre-commit hook failure handling
# - Optimized review workflow based on common patterns
# - Better conflict resolution strategies
# - Improved AI suggestion filtering and validation
# - Streamlined testing and validation processes

# The command automatically updates itself with:
# - Lessons learned from each PR processing session
# - Common failure patterns and their preventive measures
# - Best practices for efficient code review
# - Optimization strategies for testing workflows
# - Enhanced resumption capabilities for interrupted sessions

# Performance tracking:
COMMAND_FILE=".claude/commands/pr-process.md"
END_TIME=$(date +%s)
PROCESSING_TIME=$((END_TIME - START_TIME))

# Store lessons learned
cat >> "$COMMAND_FILE.lessons" << EOF
Session: $(date)
Duration: ${PROCESSING_TIME}s
PR: #${PR_NUMBER}
Success Rate: $(if [[ $? -eq 0 ]]; then echo "100%"; else echo "Partial"; fi)
Key Learnings: [Auto-populated based on execution patterns]
EOF
```

This continuous improvement ensures each PR processing session becomes more efficient and effective.