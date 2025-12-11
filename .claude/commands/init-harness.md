# Initialize Autonomous Coding Harness

Initialize the autonomous-coding harness and import features from GitHub issues.

## Instructions

### Import from GitHub Issues (Recommended)

```bash
# Import all open issues
bash .claude-toolkit/templates/harness/import-github-issues.sh

# Import issues with specific label
bash .claude-toolkit/templates/harness/import-github-issues.sh --label "feature"

# Import issues from a milestone
bash .claude-toolkit/templates/harness/import-github-issues.sh --milestone "v2.0"

# Import a single issue
bash .claude-toolkit/templates/harness/import-github-issues.sh --issue 123

# Combine filters
bash .claude-toolkit/templates/harness/import-github-issues.sh --label "enhancement" --limit 10
```

### Or Initialize Empty Harness

```bash
bash .claude-toolkit/templates/harness/init.sh
```

## After Import

The script creates `.claude/harness/feature_list.json` with features mapped from GitHub issues:

- Issue number → `id: "issue-123"`
- Title → `name`
- Body → `description`
- Labels with "priority" → `priority` (critical/high/medium/low)
- Milestone → `milestone`

## Working with Features

After importing, help the user:
1. Show the imported features: `jq '.features[] | {id, name, priority}' .claude/harness/feature_list.json`
2. Pick a feature to work on
3. Update feature status as work progresses

## Syncing Back to GitHub

When a feature is completed, close the GitHub issue:
```bash
gh issue close 123 --comment "Completed via autonomous coding session"
```
