# Start Harness Workflow

Start an autonomous coding session using features from the harness feature_list.json.

## What This Does

1. Reads features from `.claude/harness/feature_list.json`
2. Picks the next pending feature (or specified feature)
3. Routes to the **conductor agent** for full-cycle implementation
4. Updates feature status in the harness as work progresses

## Instructions

### Step 1: Load Feature List

```bash
# Check harness exists
if [ ! -f ".claude/harness/feature_list.json" ]; then
  echo "Harness not initialized. Run: /init-harness"
  exit 1
fi

# Load features
FEATURES=$(cat .claude/harness/feature_list.json)
echo "$FEATURES" | jq '.features[] | {id, name, status, priority, github_issue}'
```

### Step 2: Select Feature

**If feature ID provided** (e.g., `/harness-start feature=issue-123`):
- Use that specific feature

**Otherwise**, select next pending feature by priority:
```bash
# Get highest priority pending feature
NEXT_FEATURE=$(echo "$FEATURES" | jq -r '
  .features
  | map(select(.status == "pending"))
  | sort_by(
      if .priority == "critical" then 0
      elif .priority == "high" then 1
      elif .priority == "medium" then 2
      else 3 end
    )
  | first
')

echo "Selected feature: $(echo $NEXT_FEATURE | jq -r '.name')"
```

### Step 3: Update Feature Status

Mark feature as in_progress:
```bash
FEATURE_ID="[SELECTED_FEATURE_ID]"

jq --arg id "$FEATURE_ID" '
  .features = [.features[] | if .id == $id then .status = "in_progress" else . end]
' .claude/harness/feature_list.json > .claude/harness/feature_list.json.tmp \
  && mv .claude/harness/feature_list.json.tmp .claude/harness/feature_list.json
```

### Step 4: Route to Orchestrator Agent

The **orchestrator** is the central routing hub. It will analyze the feature and delegate appropriately:
- For full-cycle features → Routes to **conductor agent** (6-phase workflow)
- For simpler tasks → Routes to appropriate specialized agent

**If feature has github_issue**, delegate to orchestrator:

```markdown
I need the orchestrator agent to handle this feature from the harness.

Feature: [FEATURE_NAME]
GitHub Issue: #[GITHUB_ISSUE_NUMBER]
Priority: [PRIORITY]
Description: [DESCRIPTION]

Acceptance Criteria:
[LIST_FROM_FEATURE]

This is a full-cycle feature implementation task. Please:
1. Route to the conductor agent for complete 6-phase workflow
2. Pass the GitHub issue number for proper tracking
3. Ensure all specialized agents are used as needed

The conductor will handle:
- Phase 1: Planning (architect agent, research if needed)
- Phase 2: Implementation (implementation agent, database agent)
- Phase 3: Quality (tests, audit agent, refactor agent)
- Phase 4: PR creation with proper issue linking
- Phase 5: Gemini review + CI validation
- Phase 6: Final report for human review
```

**If feature has NO github_issue**, create one first:
```bash
gh issue create \
  --title "[FEATURE_NAME]" \
  --body "[DESCRIPTION]\n\nAcceptance Criteria:\n[CRITERIA_LIST]" \
  --label "feature,harness-generated"
```

Then route to conductor with the new issue number.

### Step 5: Update Feature on Completion

When conductor completes, mark feature as completed:
```bash
FEATURE_ID="[FEATURE_ID]"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

jq --arg id "$FEATURE_ID" --arg ts "$TIMESTAMP" '
  .features = [.features[] |
    if .id == $id then
      .status = "completed" | .completed_at = $ts
    else .
    end
  ] |
  .metadata.completed_features = ([.features[] | select(.status == "completed")] | length) |
  .metadata.updated_at = $ts
' .claude/harness/feature_list.json > .claude/harness/feature_list.json.tmp \
  && mv .claude/harness/feature_list.json.tmp .claude/harness/feature_list.json
```

### Step 6: Log Progress

Append to progress file:
```bash
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$TIMESTAMP - Completed: [FEATURE_NAME] (PR #[PR_NUMBER])" >> .claude/harness/claude-progress.txt
```

## Usage Examples

```bash
# Start with next pending feature
/harness-start

# Start with specific feature
/harness-start feature=issue-123

# Start with specific priority
/harness-start priority=critical
```

## Agent Flow

```
/harness-start
    │
    ├── Load feature_list.json
    ├── Select next feature
    ├── Update status → in_progress
    │
    └── Delegate to Orchestrator Agent
            │
            └── Routes to Conductor Agent (full-cycle)
                    │
                    ├── Phase 1: Planning
                    │   └── Architect Agent (VSA validation)
                    │
                    ├── Phase 2: Implementation
                    │   ├── Implementation Agent (coding)
                    │   └── Database Agent (migrations)
                    │
                    ├── Phase 3: Quality Assurance
                    │   ├── Test Suite (all tests)
                    │   ├── Audit Agent (review)
                    │   ├── Refactor Agent (if needed)
                    │   └── UI Frontend Agent (browser testing)
                    │
                    ├── Phase 4: PR Creation
                    │
                    ├── Phase 5: Gemini Review + CI
                    │
                    └── Phase 6: Final Report
                            │
                            └── Update feature → completed
```

## Continuous Mode

For autonomous multi-feature sessions:

```bash
# Process all pending features
/harness-start --continuous

# Process up to N features
/harness-start --continuous --limit=3
```

In continuous mode, after completing one feature:
1. Check for more pending features
2. If found, start next feature
3. Continue until no pending features or limit reached
