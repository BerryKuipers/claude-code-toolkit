# Ralph Loop Command

**Arguments:** [issue-number|--auto] [--continue] [--stop] [--prd-only] [--dry-run] [--iterations=N (default: 20)] [--force] [--no-policy]

**Description:** PRD-driven autonomous loop using Max subscription. Uses `/clear` + SessionStart hook for fresh context per iteration.

---

## Purpose

Execute PRD user stories autonomously:

```bash
/ralph-loop                     # Start loop from existing PRD
/ralph-loop 123                 # Fetch issue #123, generate PRD, start loop
/ralph-loop --continue          # Resume after /clear (called by hook)
/ralph-loop --stop              # Disable auto-resume, stop loop
/ralph-loop --prd-only          # Use existing PRD without GitHub fetch
/ralph-loop --dry-run           # Generate PRD only, don't start loop
```

---

## How It Works

```
┌─────────────────────────────────────────────────────┐
│              Ralph Loop Flow (Internal)             │
├─────────────────────────────────────────────────────┤
│ 1. Read .ralph/prd.json                             │
│ 2. Read .ralph/instructions.md (delegation policy)  │
│ 3. Find first story where passes === false          │
│ 4. Delegate to /architect, /conductor, /audit, etc. │
│ 5. Verify completion (TypeScript, tests)            │
│ 6. Update prd.json (passes=true, notes)            │
│ 7. Git commit the changes                           │
│ 8. Run /clear to reset context                      │
│ 9. SessionStart hook → /ralph-loop --continue       │
└─────────────────────────────────────────────────────┘
```

**Key files:**
- `.ralph/loop-active` - Flag to enable auto-resume
- `.ralph/prd.json` - PRD with user stories
- `.ralph/instructions.md` - Delegation policy

---

## Prerequisites

This command requires:
1. **GitHub CLI** (`gh`) - For issue fetching (unless using --prd-only)
2. **Project-specific `.ralph/` directory** - With instructions.md (optional, provides agent policy)

---

## Workflow

### Step 1: Parse Arguments

```bash
ISSUE_NUMBER=""
DRY_RUN="false"
MAX_ITERATIONS="20"
FORCE_OVERWRITE="false"
NO_POLICY="false"
CONTINUE_MODE="false"
STOP_MODE="false"
PRD_ONLY="false"

# Parse arguments
for arg in "$@"; do
  case $arg in
    --continue) CONTINUE_MODE="true" ;;
    --stop) STOP_MODE="true" ;;
    --prd-only) PRD_ONLY="true" ;;
    --dry-run) DRY_RUN="true" ;;
    --iterations=*) MAX_ITERATIONS="${arg#*=}" ;;
    --auto) ISSUE_NUMBER="auto" ;;
    --force) FORCE_OVERWRITE="true" ;;
    --no-policy) NO_POLICY="true" ;;
    [0-9]*) ISSUE_NUMBER="$arg" ;;
  esac
done

# Project paths
PROJECT_ROOT="$(pwd)"
RALPH_DIR="${PROJECT_ROOT}/.ralph"
PRD_FILE="${RALPH_DIR}/prd.json"
PROGRESS_FILE="${RALPH_DIR}/progress.txt"
INSTRUCTIONS_FILE="${RALPH_DIR}/instructions.md"

echo "Ralph Loop - PRD-driven autonomous development"
echo "=============================================="
echo "Project: $PROJECT_ROOT"

# Handle --stop mode immediately
if [[ "$STOP_MODE" == "true" ]]; then
  rm -f "$RALPH_DIR/loop-active"
  echo "Ralph loop stopped. Auto-resume disabled."
  exit 0
fi
```

### Step 2: Handle --continue Mode (Resume from Hook)

```bash
if [[ "$CONTINUE_MODE" == "true" ]]; then
  if [[ ! -f "$PRD_FILE" ]]; then
    echo "ERROR: No PRD found at $PRD_FILE"
    exit 1
  fi

  # Skip to execution
  PRD_ONLY="true"
fi
```

### Step 3: Handle --prd-only Mode (Use Existing PRD)

```bash
if [[ "$PRD_ONLY" == "true" ]]; then
  if [[ ! -f "$PRD_FILE" ]]; then
    echo "ERROR: No PRD found at $PRD_FILE"
    echo "Generate one first: /ralph-loop [issue-number]"
    exit 1
  fi

  echo "Using existing PRD: $PRD_FILE"
  # Skip GitHub fetch, go to execution
fi
```

### Step 4: Fetch GitHub Issue (if not --prd-only)

```bash
if [[ "$PRD_ONLY" != "true" && -n "$ISSUE_NUMBER" ]]; then
  echo ""
  echo "Fetching GitHub issue #$ISSUE_NUMBER..."

  if ! command -v gh &> /dev/null; then
    echo "ERROR: GitHub CLI (gh) not installed"
    exit 1
  fi

  ISSUE_DATA=$(gh issue view "$ISSUE_NUMBER" --json number,title,body,labels 2>/dev/null)
  if [[ -z "$ISSUE_DATA" ]]; then
    echo "ERROR: Issue #$ISSUE_NUMBER not found"
    exit 1
  fi

  ISSUE_TITLE=$(echo "$ISSUE_DATA" | jq -r '.title')
  ISSUE_BODY=$(echo "$ISSUE_DATA" | jq -r '.body')
  echo "Issue: #$ISSUE_NUMBER - $ISSUE_TITLE"

  # Generate PRD from issue (simplified - creates single story)
  mkdir -p "$RALPH_DIR"

  PROJECT_NAME=$(jq -r '.name // empty' package.json 2>/dev/null || basename "$PROJECT_ROOT")

  cat > "$PRD_FILE" << EOF
{
  "name": "$PROJECT_NAME",
  "description": "Implementation for GitHub Issue #$ISSUE_NUMBER: $ISSUE_TITLE",
  "branchName": "feature/issue-$ISSUE_NUMBER",
  "userStories": [
    {
      "id": "US-001",
      "title": "$ISSUE_TITLE",
      "description": "$(echo "$ISSUE_BODY" | jq -Rs .)",
      "acceptanceCriteria": ["Implementation complete", "Tests pass", "Code reviewed"],
      "priority": 1,
      "passes": false,
      "notes": "",
      "executor": "/conductor"
    }
  ],
  "metadata": {
    "sourceIssue": $ISSUE_NUMBER,
    "sourceTitle": "$ISSUE_TITLE",
    "generatedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "generatedBy": "ralph-loop"
  }
}
EOF

  echo "PRD generated: $PRD_FILE"
fi
```

### Step 5: Pre-flight Check - Instructions Policy

```bash
echo ""
echo "PRE-FLIGHT CHECK: Agent delegation policy..."

if [[ -f "$INSTRUCTIONS_FILE" ]]; then
  echo "Found: $INSTRUCTIONS_FILE"
  echo "Ralph will enforce project-specific agent delegation policies"

  # Validate instructions file has required content
  if grep -q "MUST delegate" "$INSTRUCTIONS_FILE" 2>/dev/null || \
     grep -q "NOT ALLOWED TO IMPLEMENT" "$INSTRUCTIONS_FILE" 2>/dev/null; then
    echo "Policy validated: Agent delegation enforcement present"
  else
    echo "WARNING: instructions.md may not enforce agent delegation"
    echo "Consider adding explicit delegation requirements"
  fi

else
  echo "No project-specific instructions found: $INSTRUCTIONS_FILE"
  echo ""

  if [[ "$NO_POLICY" == "true" ]]; then
    echo "WARNING: Running without delegation policy (--no-policy flag set)"
    echo "Ralph may implement directly instead of delegating to agents"
  else
    echo "BLOCKED: Running without delegation policy is not recommended."
    echo ""
    echo "Ralph works best when it delegates to existing Claude Code agents."
    echo "Without instructions.md, Ralph may implement tasks directly,"
    echo "bypassing your architectural rules and agent workflows."
    echo ""
    echo "Options:"
    echo "  1. Create instructions.md (recommended):"
    echo "     mkdir -p $RALPH_DIR"
    echo "     # Add delegation policy - see documentation"
    echo ""
    echo "  2. Run anyway (not recommended):"
    echo "     /ralph-loop $ISSUE_NUMBER --no-policy"
    echo ""

    # Create a minimal instructions.md template
    echo "Creating minimal instructions template..."
    mkdir -p "$RALPH_DIR"
    cat > "$INSTRUCTIONS_FILE" << 'POLICY'
# Ralph Loop Instructions

## 🚨 CRITICAL: You Are a Coordinator, NOT an Implementer

**You MUST delegate ALL work to specialist agents. You NEVER implement directly.**

### Your Role
- ✅ Analyze PRD stories
- ✅ Decide which agent handles each story
- ✅ Delegate using natural language
- ✅ Track progress
- ✅ Verify completion

### NOT Your Role
- ❌ Writing code
- ❌ Running tests (npm run test)
- ❌ Running builds (npm run build)
- ❌ Analyzing architecture yourself
- ❌ Debugging issues yourself

## Delegation Mapping

| Task Type | Delegate To |
|-----------|-------------|
| Architecture/Design | architect agent |
| Code Implementation | implementation agent |
| Database/Migrations | database agent |
| Code Quality | audit agent |
| Testing | /test-all or implementation agent |
| Refactoring | refactor agent |
| UI/UX | design agent |

## Execution Protocol

For each PRD user story:

1. **Identify the task type** (architecture, implementation, testing, etc.)
2. **Delegate to the appropriate agent** using natural language:
   ```
   I need the [agent] agent to [task description].

   Context: [relevant details]
   ```
3. **Wait for agent response**
4. **Verify completion** based on agent's report
5. **Update passes flag** only when verified complete
6. **Move to next story**

## Self-Check

Before any action, ask:
- Am I about to write code? → DELEGATE to implementation agent
- Am I about to run npm/npx? → DELEGATE to appropriate agent
- Am I about to read code for analysis? → DELEGATE to architect agent

**If you catch yourself doing work instead of delegating, STOP and delegate.**

## 🚫 Quality Gate: No Hiding Issues

**Follow rule: `.claude/rules/05-quality-integrity.mdc`**

- NEVER hide problems with fallbacks or workarounds
- FAIL LOUDLY when something is broken
- Mark as BLOCKED if it can't be done properly
- Quality over velocity - blocked is better than broken

**If an implementation can't be done properly, STOP and report it as BLOCKED.**

## 🔄 AUTONOMOUS LOOP - NEVER ASK TO CONTINUE

**This is an AUTONOMOUS loop. NEVER stop to ask permission between stories.**

### Forbidden Behaviors
- ❌ "Would you like me to continue?"
- ❌ "Should I proceed to the next story?"
- ❌ "What would you like me to work on next?"
- ❌ Stopping after completing a story to wait for input
- ❌ Presenting options for which story to do next

### Required Behavior
- ✅ Complete story → Update state files → Immediately start next story
- ✅ Continue until ALL stories pass or BLOCKED
- ✅ Only stop for: BLOCKED story, max iterations, or /ralph-loop --stop

### Loop Flow
```
Story complete?
  ↓
Update prd.json (passes=true)
Update progress.txt
Update session-state.json
  ↓
More stories with passes=false?
  YES → Start next story IMMEDIATELY (no asking)
  NO  → Loop complete, report summary
```

**The whole point of RALPH loop is autonomous execution. Asking to continue defeats the purpose.**

## 🚦 EXIT_SIGNAL Protocol (Dual-Gate Exit)

**The loop only exits when BOTH conditions are met:**
1. All stories have `passes: true` in prd.json
2. You explicitly set `EXIT_SIGNAL: true` in loop-state.json

### When to Set EXIT_SIGNAL

**Only set EXIT_SIGNAL when ALL of these are verified:**
- ✅ Every story in prd.json has `passes: true`
- ✅ All verification gates passed (tests, build, lint)
- ✅ No pending work in session-state.json
- ✅ Git commit successful for final changes

### How to Set EXIT_SIGNAL

```bash
jq '.exitSignal = true | .exitReason = "All stories complete and verified"' \
  .ralph/loop-state.json > .ralph/loop-state.json.tmp \
  && mv .ralph/loop-state.json.tmp .ralph/loop-state.json
```

### Why Dual-Gate?

Prevents premature exits when:
- Stories marked complete but verification still running
- Agent reports "done" but side effects pending
- False positives from completion detection

**If all stories pass but EXIT_SIGNAL is not set, the loop continues to verify.**

## ⚡ Circuit Breaker

**The loop automatically stops after 3 consecutive iterations with no progress.**

### What Counts as Progress?
- Story moved from `passes: false` to `passes: true`
- Meaningful code changes committed

### If Circuit Breaker Trips

1. Check current story requirements in prd.json
2. Review error logs in progress.txt
3. Check session-state.json for stuck agents
4. Fix the issue manually
5. Reset and continue:
   ```bash
   jq '.noProgressCount = 0 | .circuitBreakerTripped = false' \
     .ralph/loop-state.json > .ralph/loop-state.json.tmp \
     && mv .ralph/loop-state.json.tmp .ralph/loop-state.json
   touch .ralph/loop-active
   /ralph-loop --continue
   ```

## 📊 Context Window Management (CRITICAL)

**NEVER let autocompact trigger. Always `/clear` before 75% context usage.**

### Why?
- Autocompact destroys work context by summarizing
- RALPH loop uses `/clear` to reset cleanly between iterations
- State files preserve what matters - context doesn't need to

### Rule
- Stay within first 75% of context window
- If context feels long → save state → `/clear` → continue
- Each story should fit in one context window
- When in doubt, `/clear` early

### If Story Too Large
1. Break into sub-tasks in session-state.json
2. Complete what fits in current context
3. `/clear` and continue with remaining sub-tasks
4. Only mark `passes: true` when ALL sub-tasks done
POLICY
    echo "Created minimal policy: $INSTRUCTIONS_FILE"
    echo "Review and customize before running Ralph."
    echo ""
    echo "Run again to continue: /ralph-loop $ISSUE_NUMBER"
    exit 0
  fi
fi
```

### Step 6: Execute Loop

```bash
echo ""
echo "=============================================="
echo "RALPH LOOP EXECUTION"
echo "=============================================="

# Create loop-active flag
touch "$RALPH_DIR/loop-active"

# Initialize or update loop-state.json
LOOP_STATE_FILE="$RALPH_DIR/loop-state.json"
if [[ ! -f "$LOOP_STATE_FILE" ]]; then
  cat > "$LOOP_STATE_FILE" << EOF
{
  "iteration": 0,
  "lastCompletedCount": 0,
  "noProgressCount": 0,
  "exitSignal": false,
  "exitReason": null,
  "circuitBreakerTripped": false,
  "startedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "lastUpdated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
  echo "Initialized loop-state.json"
fi

# Check circuit breaker before continuing
CB_TRIPPED=$(jq -r '.circuitBreakerTripped // false' "$LOOP_STATE_FILE" 2>/dev/null || echo "false")
if [[ "$CB_TRIPPED" == "true" ]]; then
  echo ""
  echo "========================================"
  echo "CIRCUIT BREAKER ACTIVE"
  echo "========================================"
  echo "Loop was stopped due to no progress."
  echo "Fix the issue, then reset:"
  echo "  jq '.noProgressCount = 0 | .circuitBreakerTripped = false' .ralph/loop-state.json > tmp && mv tmp .ralph/loop-state.json"
  echo "========================================"
  exit 1
fi

# Read PRD and find next incomplete story
INCOMPLETE=$(jq -r '[.userStories[] | select(.passes == false)][0] // empty' "$PRD_FILE" 2>/dev/null)

if [[ -z "$INCOMPLETE" ]]; then
  # All stories have passes=true - check EXIT_SIGNAL dual-gate
  EXIT_SIGNAL=$(jq -r '.exitSignal // false' "$LOOP_STATE_FILE" 2>/dev/null || echo "false")

  if [[ "$EXIT_SIGNAL" == "true" ]]; then
    # DUAL-GATE MET: All pass + EXIT_SIGNAL
    rm -f "$RALPH_DIR/loop-active"
    echo ""
    echo "========================================"
    echo "RALPH LOOP COMPLETE (DUAL-GATE EXIT)"
    echo "========================================"
    echo "✅ All stories: passes=true"
    echo "✅ EXIT_SIGNAL: true"
    echo ""
    echo "PRD: $PRD_FILE"
    echo "========================================"
    exit 0
  else
    # All stories pass but EXIT_SIGNAL not set
    echo ""
    echo "========================================"
    echo "ALL STORIES PASS - AWAITING EXIT_SIGNAL"
    echo "========================================"
    echo "All stories have passes=true, but EXIT_SIGNAL not set."
    echo ""
    echo "Before setting EXIT_SIGNAL, verify:"
    echo "  1. All tests pass"
    echo "  2. Build succeeds"
    echo "  3. No pending work in session-state.json"
    echo "  4. Final changes committed"
    echo ""
    echo "If verified, set EXIT_SIGNAL:"
    echo "  jq '.exitSignal = true | .exitReason = \"Verified complete\"' .ralph/loop-state.json > tmp && mv tmp .ralph/loop-state.json"
    echo ""
    echo "Then run: /ralph-loop --continue"
    echo "========================================"
    exit 0
  fi
fi

STORY_ID=$(echo "$INCOMPLETE" | jq -r '.id')
STORY_TITLE=$(echo "$INCOMPLETE" | jq -r '.title')
STORY_DESC=$(echo "$INCOMPLETE" | jq -r '.description')
STORY_EXECUTOR=$(echo "$INCOMPLETE" | jq -r '.executor // "/conductor"')
STORY_AC=$(echo "$INCOMPLETE" | jq -r '.acceptanceCriteria | join(", ")')

# Count progress
TOTAL=$(jq '.userStories | length' "$PRD_FILE")
DONE=$(jq '[.userStories[] | select(.passes == true)] | length' "$PRD_FILE")

echo ""
echo "Progress: $DONE / $TOTAL stories complete"
echo ""
echo "Next Story: $STORY_ID"
echo "Title: $STORY_TITLE"
echo "Executor: $STORY_EXECUTOR"
echo "Acceptance: $STORY_AC"
echo ""

# Check for instructions.md
if [[ -f "$INSTRUCTIONS_FILE" ]]; then
  echo "Delegation policy: $INSTRUCTIONS_FILE"
  echo ""
fi

if [[ "$DRY_RUN" == "true" ]]; then
  echo "DRY RUN - Not executing. PRD ready at: $PRD_FILE"
  exit 0
fi

echo "=============================================="
echo ""
echo "DELEGATION PROTOCOL:"
echo "-------------------"
echo "1. Read story requirements above"
echo "2. UPDATE session-state.json (before delegating)"
echo "3. Delegate to: $STORY_EXECUTOR"
echo "4. After completion, UPDATE ALL state files:"
echo "   a. session-state.json - clear runningAgents, update checkpoint"
echo "   b. prd.json - set passes=true, add notes"
echo "   c. progress.txt - append completion entry with learnings"
echo "5. Git commit changes"
echo "6. Run /clear to continue loop"
echo ""
echo "STATE FILES TO UPDATE:"
echo "  .ralph/session-state.json  <- BEFORE and AFTER delegation"
echo "  .ralph/prd.json            <- AFTER completion"
echo "  .ralph/progress.txt        <- AFTER completion"
echo ""
echo "To stop: /ralph-loop --stop"
echo "=============================================="
```

---

## Delegation Protocol

The command MUST delegate to existing agents. It does NOT implement directly.

### Default Delegation Mapping

| Story Executor | Command |
|----------------|---------|
| `/architect` | Architecture review |
| `/conductor` | Implementation |
| `/audit` | Code review |
| `/test-all` | Testing |
| `/refactor` | Refactoring |

### Reading from instructions.md

If `.ralph/instructions.md` exists, follow its delegation rules.

---

## Safety Features

1. **Loop-active flag**: `.ralph/loop-active` controls auto-resume
2. **Max iterations**: Default 20 (tracked in progress.txt)
3. **EXIT_SIGNAL dual-gate**: Requires BOTH completion indicators AND explicit EXIT_SIGNAL
4. **Circuit breaker**: 3 consecutive no-progress loops = automatic stop
5. **Exit signals**: `BLOCKED` or `MANUAL_REQUIRED` in notes stops loop
6. **Verification gates**: TypeScript must compile, tests must pass
7. **Context window management**: `/clear` before 75% context - NEVER let autocompact trigger

---

## Context Window Management (CRITICAL)

**NEVER let autocompact trigger during RALPH loop. Always `/clear` before hitting context limits.**

### Why No Autocompact?

- Autocompact **summarizes and loses detail** - destroys work context
- RALPH loop is designed to reset with `/clear` between iterations
- State files (prd.json, progress.txt, session-state.json) preserve what matters
- Fresh context per iteration = clean slate with full capacity

### Context Budget Rule

**Stay within first 75% of context window. If approaching limit:**

1. Save current state to session-state.json
2. Update progress.txt with current work status
3. Run `/clear` immediately
4. SessionStart hook triggers `/ralph-loop --continue`

### Self-Monitoring

During RALPH loop execution, monitor your context usage:
- If you feel context is getting long (many tool calls, large outputs)
- If you've been working on a single story for extended time
- If you're about to do a large operation (big file reads, many searches)

**When in doubt, `/clear` and continue. Fresh context is always better than compacted context.**

### Per-Story Context Budget

Each story should ideally complete within a single context window. If a story is too large:
1. Break it into sub-tasks in session-state.json
2. Complete what you can
3. `/clear` and continue with remaining sub-tasks
4. Only mark story `passes: true` when ALL sub-tasks complete

---

## EXIT_SIGNAL Protocol (Dual-Gate Exit)

**The loop only exits when BOTH conditions are met:**
1. All stories have `passes: true`
2. Explicit `EXIT_SIGNAL: true` is set in loop state

### Why Dual-Gate?

Prevents premature exits when:
- Stories marked complete but verification pending
- Agent reports "done" but side effects still running
- False positives from heuristic completion detection

### Setting EXIT_SIGNAL

**Only set EXIT_SIGNAL when ALL of these are true:**
- Every story in prd.json has `passes: true`
- All verification gates passed (tests, build, lint)
- No pending work in session-state.json
- Git commit successful

```bash
# Set EXIT_SIGNAL in loop state
jq '.exitSignal = true | .exitReason = "All stories complete and verified"' \
  "$RALPH_DIR/loop-state.json" > "$RALPH_DIR/loop-state.json.tmp" \
  && mv "$RALPH_DIR/loop-state.json.tmp" "$RALPH_DIR/loop-state.json"
```

### Exit Check Logic

```bash
# Check dual-gate exit condition
ALL_PASS=$(jq '[.userStories[] | .passes] | all' "$PRD_FILE")
EXIT_SIGNAL=$(jq -r '.exitSignal // false' "$RALPH_DIR/loop-state.json" 2>/dev/null || echo "false")

if [[ "$ALL_PASS" == "true" && "$EXIT_SIGNAL" == "true" ]]; then
  echo "DUAL-GATE EXIT: All stories pass AND EXIT_SIGNAL received"
  rm -f "$RALPH_DIR/loop-active"
  exit 0
elif [[ "$ALL_PASS" == "true" && "$EXIT_SIGNAL" != "true" ]]; then
  echo "WARNING: All stories pass but EXIT_SIGNAL not set"
  echo "Verification may be pending - continuing loop"
fi
```

---

## Circuit Breaker (No-Progress Detection)

**Automatic stop after 3 consecutive loops with no progress.**

### What Counts as Progress?

- Story moved from `passes: false` to `passes: true`
- New files committed to git
- Meaningful changes to codebase (not just state files)

### Circuit Breaker State

Tracked in `.ralph/loop-state.json`:

```json
{
  "iteration": 5,
  "lastProgressIteration": 3,
  "noProgressCount": 2,
  "exitSignal": false,
  "exitReason": null,
  "circuitBreakerTripped": false
}
```

### Circuit Breaker Logic

```bash
# Read current state
ITERATION=$(jq -r '.iteration // 0' "$RALPH_DIR/loop-state.json" 2>/dev/null || echo "0")
NO_PROGRESS_COUNT=$(jq -r '.noProgressCount // 0' "$RALPH_DIR/loop-state.json" 2>/dev/null || echo "0")

# Check if progress was made this iteration
PREV_DONE=$(jq -r '.lastCompletedCount // 0' "$RALPH_DIR/loop-state.json" 2>/dev/null || echo "0")
CURR_DONE=$(jq '[.userStories[] | select(.passes == true)] | length' "$PRD_FILE")

if [[ "$CURR_DONE" -gt "$PREV_DONE" ]]; then
  # Progress made - reset counter
  NO_PROGRESS_COUNT=0
  echo "Progress: $PREV_DONE → $CURR_DONE stories complete"
else
  # No progress - increment counter
  NO_PROGRESS_COUNT=$((NO_PROGRESS_COUNT + 1))
  echo "WARNING: No progress this iteration ($NO_PROGRESS_COUNT consecutive)"
fi

# Check circuit breaker
if [[ "$NO_PROGRESS_COUNT" -ge 3 ]]; then
  echo ""
  echo "========================================"
  echo "CIRCUIT BREAKER TRIPPED"
  echo "========================================"
  echo "3 consecutive iterations with no progress"
  echo "Loop is stuck - manual intervention required"
  echo ""
  echo "Check:"
  echo "  1. Current story requirements in prd.json"
  echo "  2. Error logs in progress.txt"
  echo "  3. Agent delegation in session-state.json"
  echo "========================================"

  # Update state
  jq '.circuitBreakerTripped = true | .exitReason = "Circuit breaker: 3 no-progress iterations"' \
    "$RALPH_DIR/loop-state.json" > "$RALPH_DIR/loop-state.json.tmp" \
    && mv "$RALPH_DIR/loop-state.json.tmp" "$RALPH_DIR/loop-state.json"

  rm -f "$RALPH_DIR/loop-active"
  exit 1
fi

# Update state for next iteration
jq --argjson iter "$((ITERATION + 1))" \
   --argjson npc "$NO_PROGRESS_COUNT" \
   --argjson done "$CURR_DONE" \
   '.iteration = $iter | .noProgressCount = $npc | .lastCompletedCount = $done' \
   "$RALPH_DIR/loop-state.json" > "$RALPH_DIR/loop-state.json.tmp" \
   && mv "$RALPH_DIR/loop-state.json.tmp" "$RALPH_DIR/loop-state.json"
```

### Resetting Circuit Breaker

```bash
# After fixing the issue, reset and continue
jq '.noProgressCount = 0 | .circuitBreakerTripped = false' \
  "$RALPH_DIR/loop-state.json" > "$RALPH_DIR/loop-state.json.tmp" \
  && mv "$RALPH_DIR/loop-state.json.tmp" "$RALPH_DIR/loop-state.json"

touch "$RALPH_DIR/loop-active"
/ralph-loop --continue
```

---

## State Files

| File | Purpose |
|------|---------|
| `.ralph/prd.json` | PRD with user stories (`passes` flag per story) |
| `.ralph/progress.txt` | Learnings across iterations (append-only) |
| `.ralph/loop-active` | Flag for auto-resume (presence = loop enabled) |
| `.ralph/loop-state.json` | Loop state: iteration count, circuit breaker, EXIT_SIGNAL |
| `.ralph/session-state.json` | Current session state for crash recovery |
| `.ralph/instructions.md` | Delegation policy |

### loop-state.json Schema

```json
{
  "iteration": 1,
  "lastCompletedCount": 0,
  "noProgressCount": 0,
  "exitSignal": false,
  "exitReason": null,
  "circuitBreakerTripped": false,
  "startedAt": "2026-01-17T10:00:00Z",
  "lastUpdated": "2026-01-17T10:30:00Z"
}
```

---

## Session State Protocol (Crash Recovery)

**You MUST maintain `.ralph/session-state.json` throughout the session for crash recovery.**

### When to Update Session State

Update session-state.json at these checkpoints:
1. **Before delegating** to any agent
2. **After agent completes** (success or failure)
3. **When todo list changes** (task added, status changed)
4. **Before running /clear**

### Session State Schema

```json
{
  "lastUpdated": "2026-01-16T17:30:00Z",
  "currentStoryId": "US-001",
  "currentPhase": "implementation",
  "runningAgents": [
    {
      "agent": "implementation",
      "taskId": "task-abc123",
      "startedAt": "2026-01-16T17:25:00Z",
      "task": "Implement dark mode toggle"
    }
  ],
  "todoSnapshot": [
    { "content": "Implement backend API", "status": "completed" },
    { "content": "Implement frontend UI", "status": "in_progress" },
    { "content": "Run tests", "status": "pending" }
  ],
  "lastCheckpoint": {
    "action": "agent_delegated",
    "agent": "implementation",
    "timestamp": "2026-01-16T17:25:00Z"
  },
  "pendingWork": {
    "description": "Waiting for implementation agent to complete frontend UI",
    "resumeAction": "Check agent status, continue if complete, otherwise wait"
  }
}
```

### Update Commands

**Before delegating to agent:**
```bash
cat > "$RALPH_DIR/session-state.json" << EOF
{
  "lastUpdated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "currentStoryId": "$STORY_ID",
  "currentPhase": "delegating",
  "runningAgents": [
    {
      "agent": "$STORY_EXECUTOR",
      "startedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
      "task": "$STORY_TITLE"
    }
  ],
  "lastCheckpoint": {
    "action": "agent_delegated",
    "agent": "$STORY_EXECUTOR",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  },
  "pendingWork": {
    "description": "Waiting for $STORY_EXECUTOR to complete: $STORY_TITLE",
    "resumeAction": "Check if agent completed, verify results, update PRD"
  }
}
EOF
```

**After agent completes:**
```bash
jq '.runningAgents = [] | .currentPhase = "verification" | .lastCheckpoint = {
  "action": "agent_completed",
  "agent": "'$STORY_EXECUTOR'",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}' "$RALPH_DIR/session-state.json" > "$RALPH_DIR/session-state.json.tmp" \
  && mv "$RALPH_DIR/session-state.json.tmp" "$RALPH_DIR/session-state.json"
```

### Resumption on Session Start

When session starts (or after crash), check for session-state.json:

```bash
if [[ -f "$RALPH_DIR/session-state.json" ]]; then
  echo "Found existing session state - checking for incomplete work..."

  PENDING=$(jq -r '.pendingWork.description // empty' "$RALPH_DIR/session-state.json")
  RUNNING=$(jq -r '.runningAgents | length' "$RALPH_DIR/session-state.json")

  if [[ -n "$PENDING" || "$RUNNING" -gt 0 ]]; then
    echo ""
    echo "INCOMPLETE SESSION DETECTED"
    echo "=========================="
    echo "Pending: $PENDING"
    echo "Running agents: $RUNNING"
    echo ""
    echo "Resume action: $(jq -r '.pendingWork.resumeAction' "$RALPH_DIR/session-state.json")"
    echo ""
  fi
fi
```

### Why This Matters

Without session state:
- Crash = lost context about what was running
- No way to know if agent finished or crashed mid-task
- Manual investigation needed to figure out where to resume

With session state:
- Crash recovery knows exactly what was in progress
- Can verify if pending work completed
- Clear instructions for resumption

---

## State Update Protocol (MANDATORY)

**After EVERY story completion, you MUST update BOTH state files:**

### 1. Update prd.json

```bash
# Update the story's passes flag and add notes
jq --arg id "$STORY_ID" --arg notes "Completed via $STORY_EXECUTOR at $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '(.userStories[] | select(.id == $id)) |= (.passes = true | .notes = $notes)' \
  "$PRD_FILE" > "$PRD_FILE.tmp" && mv "$PRD_FILE.tmp" "$PRD_FILE"
```

### 2. Update progress.txt

```bash
# Append progress entry
cat >> "$PROGRESS_FILE" << EOF

---
## $(date -u +%Y-%m-%dT%H:%M:%SZ) - $STORY_ID Complete

**Executor**: $STORY_EXECUTOR
**Status**: Completed
**Learnings**: [Record any insights, blockers resolved, patterns discovered]
**Files Changed**: [List key files modified]
EOF
```

### Why Both Files Matter

- **prd.json**: Tracks completion status for loop continuation logic
- **progress.txt**: Preserves learnings across /clear cycles (context resets)

**If you skip progress.txt updates, learnings are lost when context clears.**

---

## Usage Examples

```bash
# Start from GitHub issue
/ralph-loop 459

# Use existing PRD
/ralph-loop --prd-only

# Resume after /clear
/ralph-loop --continue

# Stop the loop
/ralph-loop --stop

# Generate PRD only
/ralph-loop 459 --dry-run
```

---

**Generated**: 2026-01-16 (Internal Ralph Loop - Max Subscription)
