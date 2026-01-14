# Loop Orchestration Command

**Arguments:** [task description] [--max=N] [--promise=DONE] [--mode=auto|workflow|agent|audit]

**Description:** Autonomous loop orchestrator that expands short tasks into comprehensive workflows, selects appropriate agents, enforces verification gates, and loops automatically until completion or max iterations.

---

## Purpose

Transform short task descriptions into fully autonomous workflows:
```bash
/loop fix the failing tests for authentication
/loop implement feature: user dark mode toggle
/loop refactor the payment module
/loop audit this repository for security issues
```

The loop orchestrator will:
1. Expand short input into a proper plan (with context analysis)
2. Select and run appropriate existing agents/workflows (parallel where safe)
3. Enforce verification gates (build/tests/lint where applicable)
4. **Loop automatically** until workflow is truly done (or max iterations)
5. Print completion marker when finished

---

## Arguments

- `$ARGUMENTS` (required): Short task description
- `--max=N`: Maximum iterations before hard-stop (default: 20)
- `--promise=TOKEN`: Completion marker to detect success (default: DONE)
- `--mode=MODE`: Force specific mode instead of auto-detection
  - `auto`: Auto-detect best mode (default)
  - `workflow`: Full conductor-style workflow
  - `agent`: Single agent delegation
  - `audit`: Audit and fix mode
  - `quick-fix`: Simple fix without full workflow

---

## Workflow

### Step 1: Parse Arguments and Initialize State

```bash
TASK_DESCRIPTION="$ARGUMENTS"
MAX_ITERATIONS=20
COMPLETION_PROMISE="DONE"
MODE="auto"

# Parse flags
for arg in "$@"; do
  case $arg in
    --max=*) MAX_ITERATIONS="${arg#*=}" ;;
    --promise=*) COMPLETION_PROMISE="${arg#*=}" ;;
    --mode=*) MODE="${arg#*=}" ;;
  esac
done

# Validate we have a task
if [ -z "$TASK_DESCRIPTION" ]; then
  echo "Usage: /loop <task description> [--max=N] [--promise=TOKEN] [--mode=MODE]"
  exit 1
fi

STATE_FILE=".claude/state/loop.local.json"
```

### Step 2: Check for Existing Loop State

```bash
# Check if loop is already running for this repo
if [ -f "$STATE_FILE" ]; then
  EXISTING_ENABLED=$(jq -r '.enabled' "$STATE_FILE" 2>/dev/null)

  if [ "$EXISTING_ENABLED" = "true" ]; then
    echo "🔄 Active loop detected!"
    echo "   Task: $(jq -r '.original_arguments' "$STATE_FILE")"
    echo "   Iteration: $(jq -r '.iteration' "$STATE_FILE") / $(jq -r '.max_iterations' "$STATE_FILE")"
    echo ""
    echo "Options:"
    echo "  1. Continue existing loop (default)"
    echo "  2. Stop and start new loop: /loop-stop && /loop $TASK_DESCRIPTION"
    echo ""
    echo "Continuing existing loop..."

    # Continue existing loop
    CONTINUE_EXISTING=true
  fi
fi
```

### Step 3: Classify Intent and Select Mode

If not continuing existing loop, classify the task:

**Intent Classification:**
```markdown
Analyze the task description to determine mode:

TASK: "$TASK_DESCRIPTION"

Classification rules:
1. **workflow-run** (full conductor cycle):
   - Keywords: "implement", "feature", "build", "create", "add"
   - Multi-step tasks requiring architecture + implementation + testing

2. **agent-run** (single specialized agent):
   - Keywords: "refactor", "design", "debug", "review"
   - Tasks matching a single agent's specialty

3. **quick-fix** (minimal intervention):
   - Keywords: "fix", "patch", "update", "change"
   - Small, focused changes

4. **audit** (audit and fix loop):
   - Keywords: "audit", "check", "validate", "scan", "security"
   - Quality/security analysis with optional auto-fix

Detected mode: [DETECTED_MODE]
Confidence: [HIGH/MEDIUM/LOW]
Reasoning: [WHY_THIS_MODE]
```

### Step 4: Select Agents and Workflows

**For workflow-run mode:**
```markdown
Available workflows via conductor:
- full-cycle: Complete issue-to-PR automation
- implementation-only: Architecture + implementation
- quality-gate: Testing + audit + validation

Selected workflow: [WORKFLOW]
Agents to involve:
- architect (architecture validation)
- implementation (code writing)
- audit (quality checks)
- refactor (if quality < 8.0)
- [design if UI-related]
- [database if schema-related]
```

**For agent-run mode:**
```markdown
Available agents:
- architect: Architecture validation, SOLID/VSA compliance
- audit: Code quality, security scanning
- refactor: Code improvement, cleanup
- design: UI/UX review
- code-reviewer: PR review
- implementation: Feature implementation
- database: Schema operations
- dependency-manager: Dependency updates

Best agent for task: [SELECTED_AGENT]
Reason: [WHY_THIS_AGENT]
```

### Step 5: Define Verification Gates

```bash
# Detect project type and available tools
VERIFICATION_STEPS='[]'

# Git sanity (always)
VERIFICATION_STEPS=$(echo "$VERIFICATION_STEPS" | jq '. + ["git status --porcelain"]')

# Detect Node.js project
if [ -f "package.json" ]; then
  # Check for test script
  if grep -q '"test"' package.json; then
    # Detect package manager
    if [ -f "pnpm-lock.yaml" ]; then
      VERIFICATION_STEPS=$(echo "$VERIFICATION_STEPS" | jq '. + ["pnpm test"]')
    elif [ -f "yarn.lock" ]; then
      VERIFICATION_STEPS=$(echo "$VERIFICATION_STEPS" | jq '. + ["yarn test"]')
    else
      VERIFICATION_STEPS=$(echo "$VERIFICATION_STEPS" | jq '. + ["npm test"]')
    fi
  fi

  # Check for lint script
  if grep -q '"lint"' package.json; then
    VERIFICATION_STEPS=$(echo "$VERIFICATION_STEPS" | jq '. + ["npm run lint"]')
  fi

  # Check for build script
  if grep -q '"build"' package.json; then
    VERIFICATION_STEPS=$(echo "$VERIFICATION_STEPS" | jq '. + ["npm run build"]')
  fi
fi

# Detect .NET project
if [ -f "*.csproj" ] || [ -f "*.sln" ]; then
  VERIFICATION_STEPS=$(echo "$VERIFICATION_STEPS" | jq '. + ["dotnet test"]')
  VERIFICATION_STEPS=$(echo "$VERIFICATION_STEPS" | jq '. + ["dotnet build"]')
fi

echo "Detected verification steps: $VERIFICATION_STEPS"
```

### Step 6: Create Loop State File

```bash
mkdir -p .claude/state

# Generate session token (cwd hash + timestamp)
SESSION_TOKEN=$(echo "$(pwd)_$(date +%s)_$$" | sha256sum | cut -c1-16)

cat > "$STATE_FILE" << EOF
{
  "enabled": true,
  "mode": "$MODE",
  "completion_promise": "$COMPLETION_PROMISE",
  "max_iterations": $MAX_ITERATIONS,
  "iteration": 1,
  "original_arguments": $(echo "$TASK_DESCRIPTION" | jq -Rs .),
  "selected_agents": [],
  "verification_steps": $VERIFICATION_STEPS,
  "last_result_summary": "",
  "session_token": "$SESSION_TOKEN",
  "cwd": "$(pwd)",
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "✅ Loop initialized"
echo "   Task: $TASK_DESCRIPTION"
echo "   Mode: $MODE"
echo "   Max iterations: $MAX_ITERATIONS"
echo "   Completion marker: <promise>$COMPLETION_PROMISE</promise>"
echo ""
```

### Step 7: Execute First Iteration

Based on the detected mode, delegate to appropriate agent or workflow:

**For workflow-run mode:**
```markdown
I need the conductor agent to execute a complete workflow.

Task: $TASK_DESCRIPTION

This is iteration 1 of a loop orchestration. The loop will continue until:
- You print `<promise>$COMPLETION_PROMISE</promise>` to indicate success
- OR max iterations ($MAX_ITERATIONS) is reached

**CRITICAL Loop Protocol:**
1. At the END of this iteration, you MUST either:
   - Print `<promise>$COMPLETION_PROMISE</promise>` if the task is FULLY complete
   - Print `<loop>CONTINUE</loop>` if more work is needed

2. Before ending, write a summary to the state file:
   - What was accomplished this iteration
   - What remains to be done (if any)
   - Current status of verification gates

3. Run verification gates after substantive changes:
   $VERIFICATION_STEPS

Execute the task now. Work autonomously through all necessary phases.
```

**For agent-run mode:**
```markdown
I need the [SELECTED_AGENT] agent to handle this task.

Task: $TASK_DESCRIPTION

This is iteration 1 of an agent loop. Continue until task is complete.

**Loop Protocol:**
- Print `<promise>$COMPLETION_PROMISE</promise>` when fully complete
- Print `<loop>CONTINUE</loop>` if more iterations needed
- Run verification gates after changes: $VERIFICATION_STEPS

Begin work now.
```

**For audit mode:**
```markdown
I need the audit agent to analyze and optionally fix issues.

Task: $TASK_DESCRIPTION

This is an audit loop. For each issue found:
1. Report the issue with severity
2. If safe to auto-fix: apply the fix
3. If requires human review: note it clearly

Loop until all auto-fixable issues are resolved and report is complete.

**Loop Protocol:**
- Print `<promise>$COMPLETION_PROMISE</promise>` when audit is complete and all safe fixes applied
- Print `<loop>CONTINUE</loop>` if more audit rounds needed

Begin audit now.
```

**For quick-fix mode:**
```markdown
Quick fix needed:

Task: $TASK_DESCRIPTION

Apply the minimal fix required. Run verification after:
$VERIFICATION_STEPS

If fix works and tests pass, print `<promise>$COMPLETION_PROMISE</promise>`.
If more work needed, print `<loop>CONTINUE</loop>`.

Begin fix now.
```

---

## Iteration Protocol

**Every iteration MUST end with:**

1. **Update state file** with progress summary:
```bash
jq --arg summary "Iteration N summary..." \
   --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
   '.last_result_summary = $summary | .updated_at = $ts' \
   "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
```

2. **Print completion status:**
   - `<promise>DONE</promise>` - Task fully complete, loop should stop
   - `<loop>CONTINUE</loop>` - More work needed, loop should continue

3. **The Stop hook will:**
   - Read the state file
   - Check for completion marker in output
   - Either disable the loop or trigger next iteration

---

## Verification Gates

Before printing completion, ALL verification gates must pass:

```bash
echo "Running verification gates..."

for step in $(echo "$VERIFICATION_STEPS" | jq -r '.[]'); do
  echo "  -> $step"
  if ! eval "$step" 2>&1; then
    echo "  ❌ FAILED: $step"
    echo ""
    echo "Verification failed. Continuing loop to fix..."
    echo "<loop>CONTINUE</loop>"
    exit 0
  fi
  echo "  ✅ PASSED"
done

echo ""
echo "All verification gates passed!"
```

---

## Usage Examples

### Fix Failing Tests
```bash
/loop fix the failing tests for the auth module
# Mode: quick-fix -> agent-run (debugger)
# Loops until: all tests pass
```

### Implement Feature
```bash
/loop implement user preference for dark mode
# Mode: workflow-run (conductor full-cycle)
# Loops until: PR created with passing CI
```

### Refactor Module
```bash
/loop refactor the payment service for better separation of concerns
# Mode: agent-run (refactor agent)
# Loops until: audit score >= 8.0
```

### Security Audit
```bash
/loop audit this codebase for security vulnerabilities
# Mode: audit
# Loops until: all issues found and reported/fixed
```

### Custom Iteration Limit
```bash
/loop implement dark mode --max=10
# Limits to 10 iterations max
```

### Custom Completion Marker
```bash
/loop fix tests --promise=ALL_TESTS_PASS
# Uses custom marker for completion detection
```

---

## Stop the Loop

To manually stop an active loop:
```bash
/loop-stop
```

Or set enabled=false in state file:
```bash
jq '.enabled = false' .claude/state/loop.local.json > tmp && mv tmp .claude/state/loop.local.json
```

---

## Expected Outcomes

### Success
- Task completed within max iterations
- All verification gates pass
- `<promise>DONE</promise>` printed
- Loop state disabled/cleaned

### Max Iterations Reached
- Loop stops after max_iterations
- Summary of what was accomplished
- What remains incomplete
- Manual intervention may be needed

### Manual Stop
- `/loop-stop` executed
- Loop disabled immediately
- Current iteration may complete but no new iteration starts

---

## Related Commands & Agents

**Commands:**
- `/loop-stop` - Disable active loop
- `/conductor` - Full workflow orchestration
- `/audit` - Code quality audit
- `/refactor` - Code improvement

**Agents:**
- conductor - Complete workflow management
- orchestrator - Task routing
- architect - Architecture validation
- audit - Quality checking
- refactor - Code improvement
- implementation - Feature implementation
- debugger - Test/bug fixing
- design - UI/UX review

---

## Not the Same as /ralph-loop

This `/loop` command uses an **internal protocol** with `<promise>DONE</promise>` completion markers.

For **Ralph TUI-driven loops** with PRD JSON files, use `/ralph-loop` instead:
- `/ralph-loop` - External ralph-tui with PRD JSON from GitHub issues
- Different protocol, different state files, different use case

| Feature | `/loop` (this command) | `/ralph-loop` |
|---------|------------------------|---------------|
| Protocol | Internal `<promise>` markers | External ralph-tui |
| State | `.claude/state/loop.local.json` | `.ralph/prd.json` |
| Input | Ad-hoc task description | GitHub issue |
| Use Case | Quick task automation | Structured PRD development |

---

## Technical Notes

**State File Location:** `.claude/state/loop.local.json`
- Repo-local (not synced across repos)
- Includes session token to prevent cross-session bleed
- Includes cwd hash to prevent cross-repo contamination

**Stop Hook:** `.claude/hooks/loop-controller.sh` / `.ps1`
- Registered in Stop hook event
- Checks state file for enabled loop
- Detects completion markers in recent output
- Increments iteration or disables loop

**Session Scoping:**
- Session token generated from: cwd + timestamp + PID
- Prevents loops from accidentally continuing across different sessions/repos

---

**Generated**: 2025-12-30 (Loop Orchestration System)
