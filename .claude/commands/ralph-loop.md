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

# Read PRD and find next incomplete story
INCOMPLETE=$(jq -r '[.userStories[] | select(.passes == false)][0] // empty' "$PRD_FILE" 2>/dev/null)

if [[ -z "$INCOMPLETE" ]]; then
  # All stories complete
  rm -f "$RALPH_DIR/loop-active"
  echo ""
  echo "ALL STORIES COMPLETE!"
  echo "====================="
  echo "PRD: $PRD_FILE"
  exit 0
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
3. **Exit signals**: `BLOCKED` or `MANUAL_REQUIRED` in notes stops loop
4. **Verification gates**: TypeScript must compile, tests must pass

---

## State Files

| File | Purpose |
|------|---------|
| `.ralph/prd.json` | PRD with user stories |
| `.ralph/progress.txt` | Learnings across iterations |
| `.ralph/loop-active` | Flag for auto-resume |
| `.ralph/instructions.md` | Delegation policy |
| `.ralph/session-state.json` | **NEW** - Current session state for crash recovery |

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
