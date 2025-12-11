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

### Step 4: Route to Conductor Agent

**If feature has github_issue**, delegate to conductor with issue number:

```markdown
I need the conductor agent to implement this feature from the harness.

Feature: [FEATURE_NAME]
GitHub Issue: #[GITHUB_ISSUE_NUMBER]
Priority: [PRIORITY]
Description: [DESCRIPTION]

Acceptance Criteria:
[LIST_FROM_FEATURE]

Please execute full-cycle workflow:
1. Architecture planning
2. Implementation following project patterns
3. Quality assurance (tests, audit, build)
4. PR creation linked to issue #[GITHUB_ISSUE_NUMBER]
5. Gemini review handling
6. CI validation

Use all specialized agents as needed:
- architect for VSA compliance
- implementation for coding
- database for migrations
- refactor for quality improvements
- audit for code review
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
    └── Delegate to Conductor Agent
            │
            ├── Architect Agent (VSA validation)
            ├── Implementation Agent (coding)
            ├── Database Agent (migrations)
            ├── Refactor Agent (quality)
            ├── Audit Agent (review)
            ├── UI Frontend Agent (browser testing)
            │
            └── PR Created + CI Validated
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
