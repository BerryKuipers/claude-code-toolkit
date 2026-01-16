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

### Step 5: Execute Loop

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
echo "2. Delegate to: $STORY_EXECUTOR"
echo "3. After completion, update PRD:"
echo "   - Set passes=true for $STORY_ID"
echo "   - Add timestamped notes"
echo "4. Git commit changes"
echo "5. Run /clear to continue loop"
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
