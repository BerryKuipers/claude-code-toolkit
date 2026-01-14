# Ralph Loop Command

**Arguments:** [issue-number|--auto] [--dry-run] [--headless] [--iterations=N (default: 20)] [--agent=claude|opencode (default: claude)] [--force] [--no-policy]

**Description:** Launch Ralph TUI-driven autonomous loop from a GitHub issue, generating PRD JSON and enforcing task execution through existing Claude Code agents and slash-commands.

---

## Purpose

Combines GitHub issue selection (via `/issue-pickup`) with Ralph TUI orchestration:

```bash
/ralph-loop                     # Auto-select best issue, generate PRD, launch Ralph
/ralph-loop 123                 # Use specific issue #123
/ralph-loop --dry-run           # Generate files but don't launch TUI
/ralph-loop --headless          # Run without interactive TUI
/ralph-loop --iterations=10     # Limit to 10 iterations
```

---

## Prerequisites

This command requires:
1. **GitHub CLI** (`gh`) - For issue fetching
2. **ralph-tui** - Either installed globally, via bunx, or npx
3. **Project-specific `.ralph/` directory** - With instructions.md (optional, provides agent policy)

---

## Workflow

### Step 1: Parse Arguments and Detect Environment

```bash
ISSUE_NUMBER=""
DRY_RUN="false"
HEADLESS="false"
MAX_ITERATIONS="20"
AGENT_OVERRIDE="claude"
FORCE_OVERWRITE="false"
NO_POLICY="false"

# Parse arguments
for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN="true" ;;
    --headless) HEADLESS="true" ;;
    --iterations=*) MAX_ITERATIONS="${arg#*=}" ;;
    --agent=*) AGENT_OVERRIDE="${arg#*=}" ;;
    --auto) ISSUE_NUMBER="auto" ;;
    --force) FORCE_OVERWRITE="true" ;;
    --no-policy) NO_POLICY="true" ;;
    [0-9]*) ISSUE_NUMBER="$arg" ;;
  esac
done

# Project paths (repo-agnostic defaults)
PROJECT_ROOT="$(pwd)"
RALPH_DIR="${PROJECT_ROOT}/.ralph"
PRD_FILE="${RALPH_DIR}/prd.json"
PROGRESS_FILE="${RALPH_DIR}/progress.txt"
INSTRUCTIONS_FILE="${RALPH_DIR}/instructions.md"

echo "Ralph Loop - Autonomous PRD-driven development"
echo "=============================================="
echo "Project: $PROJECT_ROOT"
echo "Ralph directory: $RALPH_DIR"
```

### Step 2: Verify GitHub Authentication

```bash
echo ""
echo "Checking GitHub authentication..."

if ! command -v gh &> /dev/null; then
  echo "GitHub CLI (gh) is not installed."
  echo ""
  echo "Install instructions:"
  echo "  - macOS: brew install gh"
  echo "  - Linux: sudo apt install gh OR sudo dnf install gh"
  echo "  - Windows: winget install GitHub.cli"
  echo ""
  echo "After installing, run: gh auth login"
  exit 1
fi

if ! gh auth status &> /dev/null; then
  echo "GitHub CLI is not authenticated."
  echo ""
  echo "Run: gh auth login"
  echo "Then retry this command."
  exit 1
fi

echo "GitHub authentication verified"
```

### Step 3: Resolve Ralph TUI Execution Method

```bash
echo ""
echo "Resolving ralph-tui execution method..."

RALPH_CMD=""
RALPH_METHOD=""
RALPH_VERSION=""

# Pinned version for stability (override via .ralph/config or env)
# Update this when a new stable version is tested
RALPH_PINNED_VERSION="${RALPH_TUI_VERSION:-1.0.0}"

# Check for project-specific version override
if [[ -f "$RALPH_DIR/config" ]]; then
  PROJECT_VERSION=$(grep -E '^version=' "$RALPH_DIR/config" 2>/dev/null | cut -d= -f2)
  if [[ -n "$PROJECT_VERSION" ]]; then
    RALPH_PINNED_VERSION="$PROJECT_VERSION"
    echo "Using project-pinned version: $RALPH_PINNED_VERSION"
  fi
fi

# Resolution order (strict):
# 1. PATH binary (global install)
# 2. bunx (if bun exists AND bunx can resolve)
# 3. npx with pinned version (NOT @latest for stability)

echo "Resolution order: PATH -> bunx -> npx@$RALPH_PINNED_VERSION"
echo ""

# 1. Check PATH first (most reliable)
if command -v ralph-tui &> /dev/null; then
  RALPH_CMD="ralph-tui"
  RALPH_METHOD="PATH"
  RALPH_VERSION=$(ralph-tui --version 2>/dev/null || echo "unknown")
  echo "[1] Found ralph-tui in PATH"
  echo "    Version: $RALPH_VERSION"
  echo "    Location: $(which ralph-tui)"

# 2. Check for bun AND verify bunx can resolve
elif command -v bun &> /dev/null; then
  echo "[1] ralph-tui not in PATH"
  echo "[2] Checking bunx..."

  # Verify bunx can actually resolve ralph-tui (don't trust bun existing alone)
  if bunx ralph-tui --version &> /dev/null; then
    RALPH_CMD="bunx ralph-tui"
    RALPH_METHOD="bunx"
    RALPH_VERSION=$(bunx ralph-tui --version 2>/dev/null || echo "unknown")
    echo "    bunx resolved successfully"
    echo "    Version: $RALPH_VERSION"
  else
    echo "    bunx exists but cannot resolve ralph-tui"
    echo "[3] Falling back to npx..."

    # Fallback to npx even though bun exists
    if command -v npx &> /dev/null; then
      RALPH_CMD="npx -y ralph-tui@$RALPH_PINNED_VERSION"
      RALPH_METHOD="npx"
      echo "    Using npx with pinned version: $RALPH_PINNED_VERSION"
    fi
  fi

# 3. Fallback to npx with PINNED version (not @latest)
elif command -v npx &> /dev/null; then
  echo "[1] ralph-tui not in PATH"
  echo "[2] bun not available"
  echo "[3] Using npx with pinned version..."

  RALPH_CMD="npx -y ralph-tui@$RALPH_PINNED_VERSION"
  RALPH_METHOD="npx"
  echo "    Version: $RALPH_PINNED_VERSION (pinned)"
  echo "    Note: Set RALPH_TUI_VERSION env or .ralph/config to override"

else
  echo "[1] ralph-tui not in PATH"
  echo "[2] bun not available"
  echo "[3] npx not available"
  echo ""
  echo "ralph-tui is not available and no package manager found."
  echo ""
  echo "Install ralph-tui using one of:"
  echo "  - bun install -g ralph-tui    (recommended)"
  echo "  - npm install -g ralph-tui"
  echo ""
  echo "Or ensure bun or npm is available for ephemeral execution."
  exit 1
fi

# Final verification
if [[ -z "$RALPH_CMD" ]]; then
  echo ""
  echo "Failed to resolve ralph-tui execution method."
  exit 1
fi

echo "Resolved execution: $RALPH_CMD (method: $RALPH_METHOD)"
```

### Step 4: Pick GitHub Issue

```bash
echo ""
echo "Selecting GitHub issue..."

# Reuse issue-pickup logic for smart selection
if [[ -z "$ISSUE_NUMBER" || "$ISSUE_NUMBER" == "auto" ]]; then
  echo "Auto-selecting best issue from backlog..."

  # Get repo info
  REPO_OWNER=$(gh repo view --json owner --jq '.owner.login' 2>/dev/null)
  REPO_NAME=$(gh repo view --json name --jq '.name' 2>/dev/null)

  if [[ -z "$REPO_OWNER" || -z "$REPO_NAME" ]]; then
    echo "Could not determine repository. Ensure you're in a git repo with GitHub remote."
    exit 1
  fi

  echo "Repository: $REPO_OWNER/$REPO_NAME"

  # Smart issue selection: prioritize by labels and assignee
  # Priority: high-priority > bug > enhancement > unassigned
  SELECTED_ISSUE=$(gh issue list \
    --state open \
    --limit 20 \
    --json number,title,labels,assignees \
    --jq '
      # Sort by priority: assigned to me > unassigned > assigned to others
      # Then by labels: high-priority > bug > enhancement > other
      sort_by(
        (if (.assignees | length) == 0 then 1
         elif (.assignees | map(.login) | index(env.USER // "")) then 0
         else 2 end),
        (if (.labels | map(.name) | index("high-priority")) then 0
         elif (.labels | map(.name) | index("bug")) then 1
         elif (.labels | map(.name) | index("enhancement")) then 2
         else 3 end)
      ) | .[0]
    ' 2>/dev/null)

  if [[ -z "$SELECTED_ISSUE" || "$SELECTED_ISSUE" == "null" ]]; then
    echo "No open issues found in repository."
    echo "Create an issue first, or specify an issue number manually."
    exit 1
  fi

  ISSUE_NUMBER=$(echo "$SELECTED_ISSUE" | jq -r '.number')
  ISSUE_TITLE=$(echo "$SELECTED_ISSUE" | jq -r '.title')

  echo "Selected: #$ISSUE_NUMBER - $ISSUE_TITLE"
else
  # Fetch specified issue
  ISSUE_DATA=$(gh issue view "$ISSUE_NUMBER" --json number,title,body,labels 2>/dev/null)

  if [[ -z "$ISSUE_DATA" ]]; then
    echo "Issue #$ISSUE_NUMBER not found or not accessible."
    exit 1
  fi

  ISSUE_TITLE=$(echo "$ISSUE_DATA" | jq -r '.title')
  echo "Using: #$ISSUE_NUMBER - $ISSUE_TITLE"
fi

# Fetch full issue data
ISSUE_BODY=$(gh issue view "$ISSUE_NUMBER" --json body --jq '.body' 2>/dev/null)
ISSUE_LABELS=$(gh issue view "$ISSUE_NUMBER" --json labels --jq '[.labels[].name] | join(",")' 2>/dev/null)
```

### Step 5: Generate PRD JSON from Issue

```bash
echo ""
echo "Generating PRD JSON from issue..."

# Create .ralph directory if needed
mkdir -p "$RALPH_DIR"

# Determine branch name
SAFE_TITLE=$(echo "$ISSUE_TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//' | cut -c1-50)
BRANCH_NAME="feature/issue-${ISSUE_NUMBER}-${SAFE_TITLE}"

# Extract checklist items from issue body (if present)
# GitHub checklists: - [ ] item or - [x] item
CHECKLIST_ITEMS=$(echo "$ISSUE_BODY" | grep -oP '(?<=- \[ \] |^- \[ \] ).*' | head -20 || echo "")

# Function to detect appropriate executor agent based on content
detect_executor() {
  local content="$1"
  local content_lower=$(echo "$content" | tr '[:upper:]' '[:lower:]')

  # Architecture/design keywords -> architect
  if [[ "$content_lower" =~ architect|design|structure|layer|pattern|interface|contract ]]; then
    echo "/architect"
  # Testing keywords -> test-all
  elif [[ "$content_lower" =~ test|spec|coverage|validate|verify ]]; then
    echo "/test-all"
  # Audit/review keywords -> audit
  elif [[ "$content_lower" =~ audit|review|security|quality|lint ]]; then
    echo "/audit"
  # Refactor keywords -> refactor
  elif [[ "$content_lower" =~ refactor|cleanup|improve|optimize ]]; then
    echo "/refactor"
  # UI/UX keywords -> design agent
  elif [[ "$content_lower" =~ ui|ux|component|style|css|layout|responsive ]]; then
    echo "design agent"
  # Database keywords -> database agent
  elif [[ "$content_lower" =~ database|db|schema|migration|prisma|sql ]]; then
    echo "database agent"
  # Default -> conductor for implementation
  else
    echo "/conductor"
  fi
}

# Build user stories from issue content
USER_STORIES="[]"
STORY_ID=1

# If issue has checklist items, convert each to a user story
if [[ -n "$CHECKLIST_ITEMS" ]]; then
  echo "Found checklist items in issue - converting to user stories"

  while IFS= read -r item; do
    if [[ -n "$item" ]]; then
      # Detect appropriate executor for this item
      EXECUTOR=$(detect_executor "$item")

      STORY=$(jq -n \
        --arg id "US-$(printf '%03d' $STORY_ID)" \
        --arg title "$item" \
        --arg desc "Implement: $item" \
        --arg executor "$EXECUTOR" \
        '{
          id: $id,
          title: $title,
          description: $desc,
          acceptanceCriteria: ["Implementation complete", "Tests pass", "Code reviewed"],
          priority: ($ARGS.positional[0] | tonumber),
          passes: false,
          notes: "",
          executor: ("Use Claude Code agent: " + $executor)
        }' --args "$STORY_ID")

      USER_STORIES=$(echo "$USER_STORIES" | jq --argjson story "$STORY" '. + [$story]')
      STORY_ID=$((STORY_ID + 1))
    fi
  done <<< "$CHECKLIST_ITEMS"
else
  # Create single user story from issue title/body
  echo "No checklist found - creating single user story from issue"

  # Detect appropriate executor for this issue
  EXECUTOR=$(detect_executor "$ISSUE_TITLE $ISSUE_BODY")

  # Extract acceptance criteria from issue body if present
  AC_SECTION=$(echo "$ISSUE_BODY" | grep -A 10 -i "acceptance criteria" | grep "^-" | head -5 || echo "")

  if [[ -n "$AC_SECTION" ]]; then
    AC_JSON=$(echo "$AC_SECTION" | sed 's/^- //' | jq -R -s 'split("\n") | map(select(length > 0))')
  else
    AC_JSON='["Implementation complete", "All tests pass", "Code follows project conventions"]'
  fi

  USER_STORIES=$(jq -n \
    --arg title "$ISSUE_TITLE" \
    --arg desc "$ISSUE_BODY" \
    --argjson ac "$AC_JSON" \
    --arg executor "$EXECUTOR" \
    '[{
      id: "US-001",
      title: $title,
      description: ($desc // "Implement the feature as described"),
      acceptanceCriteria: $ac,
      priority: 1,
      passes: false,
      notes: "",
      executor: ("Use Claude Code agent: " + $executor)
    }]')
fi

# Get project name from package.json or directory name
PROJECT_NAME=$(jq -r '.name // empty' package.json 2>/dev/null || basename "$PROJECT_ROOT")

# Build complete PRD JSON
PRD_JSON=$(jq -n \
  --arg project "$PROJECT_NAME" \
  --arg branch "$BRANCH_NAME" \
  --arg desc "Implementation for GitHub Issue #$ISSUE_NUMBER: $ISSUE_TITLE" \
  --argjson stories "$USER_STORIES" \
  --arg issueNumber "$ISSUE_NUMBER" \
  --arg issueTitle "$ISSUE_TITLE" \
  '{
    project: $project,
    branchName: $branch,
    description: $desc,
    userStories: $stories,
    metadata: {
      sourceIssue: ($issueNumber | tonumber),
      sourceTitle: $issueTitle,
      generatedAt: (now | todate),
      generatedBy: "ralph-loop"
    }
  }')

# Check for existing PRD and protect against in-flight work
if [[ -f "$PRD_FILE" ]]; then
  echo "Existing PRD found - checking state..."

  EXISTING_ISSUE=$(jq -r '.metadata.sourceIssue // 0' "$PRD_FILE" 2>/dev/null)

  # Detect in-flight work: stories with passes=false but have notes (work started)
  IN_FLIGHT_COUNT=$(jq '[.userStories[] | select(.passes == false and .notes != "")] | length' "$PRD_FILE" 2>/dev/null || echo "0")
  INCOMPLETE_COUNT=$(jq '[.userStories[] | select(.passes == false)] | length' "$PRD_FILE" 2>/dev/null || echo "0")
  TOTAL_COUNT=$(jq '.userStories | length' "$PRD_FILE" 2>/dev/null || echo "0")

  if [[ "$IN_FLIGHT_COUNT" -gt 0 && "$FORCE_OVERWRITE" != "true" ]]; then
    echo ""
    echo "IN-FLIGHT WORK DETECTED"
    echo "======================="
    echo "Existing PRD has $IN_FLIGHT_COUNT stories with work in progress."
    echo "Issue: #$EXISTING_ISSUE"
    echo "Progress: $((TOTAL_COUNT - INCOMPLETE_COUNT))/$TOTAL_COUNT stories complete"
    echo ""
    echo "Options:"
    echo "  1. Resume existing work: /ralph-loop (without new issue number)"
    echo "  2. Force overwrite: /ralph-loop $ISSUE_NUMBER --force"
    echo "  3. Create separate PRD: PRD will be saved as prd.$ISSUE_NUMBER.json"
    echo ""

    if [[ "$ISSUE_NUMBER" != "$EXISTING_ISSUE" ]]; then
      echo "Creating issue-specific PRD to preserve in-flight work..."
      PRD_FILE="${RALPH_DIR}/prd.${ISSUE_NUMBER}.json"
      echo "New PRD location: $PRD_FILE"
    else
      echo "Continuing with same issue - will merge/update existing PRD"
    fi

  elif [[ "$EXISTING_ISSUE" == "$ISSUE_NUMBER" ]]; then
    echo "PRD already exists for issue #$ISSUE_NUMBER"

    if [[ "$INCOMPLETE_COUNT" -gt 0 ]]; then
      echo "Status: $((TOTAL_COUNT - INCOMPLETE_COUNT))/$TOTAL_COUNT stories complete"
      echo "Updating PRD with latest issue content..."
    else
      echo "All stories complete - regenerating PRD for fresh run"
    fi

  else
    echo "Different issue in existing PRD (#$EXISTING_ISSUE)"

    if [[ "$FORCE_OVERWRITE" == "true" ]]; then
      echo "Force flag set - overwriting existing PRD"
      cp "$PRD_FILE" "${PRD_FILE}.backup.$(date +%Y%m%d%H%M%S)"
    else
      echo "Creating issue-specific PRD: prd.${ISSUE_NUMBER}.json"
      cp "$PRD_FILE" "${PRD_FILE}.backup.$(date +%Y%m%d%H%M%S)"
      PRD_FILE="${RALPH_DIR}/prd.${ISSUE_NUMBER}.json"
    fi
  fi
fi

# Write PRD JSON
echo "$PRD_JSON" | jq '.' > "$PRD_FILE"
echo "PRD written to: $PRD_FILE"
echo "User stories: $(echo "$USER_STORIES" | jq 'length')"
```

### Step 6: Initialize Progress File

```bash
echo ""
echo "Initializing progress file..."

if [[ ! -f "$PROGRESS_FILE" ]]; then
  cat > "$PROGRESS_FILE" << EOF
# Ralph Loop Progress - Issue #$ISSUE_NUMBER
Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## Session Context
- Issue: #$ISSUE_NUMBER - $ISSUE_TITLE
- Branch: $BRANCH_NAME
- Project: $PROJECT_NAME

## Learnings
(Ralph will append learnings here between iterations)

## Completed Stories
(Updated as user stories pass validation)

EOF
  echo "Progress file created: $PROGRESS_FILE"
else
  echo "Progress file exists: $PROGRESS_FILE"
  # Append new session marker
  echo "" >> "$PROGRESS_FILE"
  echo "---" >> "$PROGRESS_FILE"
  echo "## New Session - $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$PROGRESS_FILE"
  echo "Issue: #$ISSUE_NUMBER - $ISSUE_TITLE" >> "$PROGRESS_FILE"
fi
```

### Step 7: Pre-flight Check - Instructions Policy

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

## Agent Delegation Policy

You MUST delegate work to existing Claude Code agents. Do NOT implement directly.

### Delegation Mapping

- Architecture: `/architect`
- Implementation: `/conductor`
- Code review: `/audit`
- Testing: `/test-all`

### Execution Protocol

For each PRD user story:
1. Analyze which agent is needed
2. Delegate using the appropriate slash-command
3. Verify completion
4. Update passes flag only when verified
POLICY
    echo "Created minimal policy: $INSTRUCTIONS_FILE"
    echo "Review and customize before running Ralph."
    echo ""
    echo "Run again to continue: /ralph-loop $ISSUE_NUMBER"
    exit 0
  fi
fi
```

### Step 8: Build and Execute Ralph Command

```bash
echo ""
echo "=============================================="
echo "RALPH LOOP EXECUTION"
echo "=============================================="

# Build command with flags (always include iterations and agent for transparency)
FULL_CMD="$RALPH_CMD run --prd \"$PRD_FILE\" --iterations $MAX_ITERATIONS --agent $AGENT_OVERRIDE"

if [[ "$HEADLESS" == "true" ]]; then
  FULL_CMD="$FULL_CMD --headless"
fi

echo ""
echo "Execution command:"
echo "  $FULL_CMD"
echo ""
echo "Working directory: $PROJECT_ROOT"
echo "PRD file: $PRD_FILE"
echo "Progress file: $PROGRESS_FILE"

if [[ "$DRY_RUN" == "true" ]]; then
  echo ""
  echo "=============================================="
  echo "DRY RUN MODE - Files generated, TUI not launched"
  echo "=============================================="
  echo ""
  echo "Generated files:"
  echo "  - $PRD_FILE"
  echo "  - $PROGRESS_FILE"
  echo ""
  echo "PRD contents:"
  cat "$PRD_FILE" | jq '.'
  echo ""
  echo "To launch Ralph manually:"
  echo "  cd $PROJECT_ROOT && $FULL_CMD"
  exit 0
fi

echo ""
echo "Launching Ralph TUI..."
echo "(Press 's' to start, 'q' to quit, '?' for help)"
echo ""

# Execute Ralph
cd "$PROJECT_ROOT" && eval "$FULL_CMD"
```

---

## Important: Agent Delegation Policy

This command generates PRD JSON for Ralph TUI. For Ralph to properly delegate to Claude Code agents, the project MUST have a `.ralph/instructions.md` file that enforces:

1. **No direct implementation** - Ralph must invoke existing agents
2. **Agent routing** - Map PRD items to appropriate agents:
   - Architecture changes -> `/architect`
   - Code implementation -> `/conductor` or implementation agent
   - Code review -> `/audit`
   - UI/UX changes -> design agent
3. **Rule compliance** - All agents must follow project rules in `.claude/rules/`

See project-specific documentation for the required instructions file format.

---

## Usage Examples

### Auto-Select Issue
```bash
/ralph-loop
# Picks best open issue, generates PRD, launches TUI
```

### Specific Issue
```bash
/ralph-loop 123
# Uses issue #123
```

### Dry Run (Generate Only)
```bash
/ralph-loop --dry-run
# Creates PRD and progress files, prints command, doesn't launch
```

### Headless Mode
```bash
/ralph-loop --headless --iterations=5
# Runs without TUI, max 5 iterations
```

### Custom Agent
```bash
/ralph-loop --agent=opencode
# Uses OpenCode instead of Claude
```

---

## Related Commands

- `/issue-pickup` - Full issue workflow with PR creation
- `/loop` - Internal loop orchestration (different protocol)
- `/conductor` - Full workflow orchestration

---

## Technical Notes

**State Files:**
- PRD: `.ralph/prd.json`
- Progress: `.ralph/progress.txt`
- Instructions: `.ralph/instructions.md` (project-specific)

**Execution Methods:**
1. `ralph-tui` (PATH) - Global installation
2. `bunx ralph-tui` - Ephemeral via bun
3. `npx -y ralph-tui@latest` - Ephemeral via npm

**PRD JSON Schema:**
```json
{
  "project": "string",
  "branchName": "string",
  "description": "string",
  "userStories": [{
    "id": "US-001",
    "title": "string",
    "description": "string",
    "acceptanceCriteria": ["string"],
    "priority": 1,
    "passes": false,
    "notes": ""
  }],
  "metadata": {
    "sourceIssue": 123,
    "generatedAt": "ISO-8601",
    "generatedBy": "ralph-loop"
  }
}
```

---

**Generated**: 2026-01-14 (Ralph Loop Integration)
