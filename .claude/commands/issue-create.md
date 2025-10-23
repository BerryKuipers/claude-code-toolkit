# GitHub Issue Creation Command

**Arguments:** --title=<string> --body=<markdown> --labels=<list> --assignee=<username>

**Success Criteria:** Successfully creates GitHub issue with provided details and returns issue URL

**Description:** Utility command for creating GitHub issues directly from the repository. Designed to be reusable by other commands like `/architect` for automated issue creation workflow.

---

## ⚠️ Important: Utility Tool Only

**This command creates GitHub issues ONLY** - it does NOT orchestrate other commands.

**Scope:**
- ✅ Create GitHub issue via `gh` CLI
- ✅ Set title, body, labels, assignee
- ✅ Return issue URL
- ❌ Does NOT orchestrate other commands
- ❌ Does NOT modify code

**Intended to be called by:** Other commands (e.g., `/architect`), OrchestratorAgent, or direct user invocation

---

## Core Capabilities

- **Direct GitHub Integration** - Creates issues using GitHub CLI (gh)
- **Flexible Input Formats** - Supports inline arguments or JSON input files
- **Label Management** - Handles comma-separated or array-format labels
- **Workflow Integration** - Automatically triggers relevant GitHub workflows for new issues
- **Validation** - Ensures required fields and validates GitHub connectivity
- **Output Standardization** - Returns both JSON and human-readable responses

## Usage Patterns

```bash
# Basic usage with inline arguments
/issue-create --title="Fix authentication bug" --body="Description of the issue..." --labels="bug,auth"

# Advanced usage with assignee
/issue-create --title="Implement feature X" --body="Feature requirements..." --labels="enhancement,frontend" --assignee="developer"

# JSON input file usage (for complex bodies)
/issue-create --input-file=/tmp/issue-data.json

# Orchestrator integration
/issue-create --title="Architecture Review Findings" --body="$(cat /tmp/architect-report.md)" --labels="architecture,tech-debt" --orchestrator-session=abc123
```

## Implementation

### **Step 1: Argument Processing**

```bash
#!/bin/bash

echo "📝 GITHUB ISSUE CREATOR"

# Initialize variables
TITLE=""
BODY=""
LABELS=""
ASSIGNEE=""
INPUT_FILE=""
ORCHESTRATOR_SESSION=""
OUTPUT_FORMAT="mixed"
OUTPUT_FILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --title=*)
      TITLE="${1#*=}"
      shift ;;
    --body=*)
      BODY="${1#*=}"
      shift ;;
    --labels=*)
      LABELS="${1#*=}"
      shift ;;
    --assignee=*)
      ASSIGNEE="${1#*=}"
      shift ;;
    --input-file=*)
      INPUT_FILE="${1#*=}"
      shift ;;
    --orchestrator-session=*)
      ORCHESTRATOR_SESSION="${1#*=}"
      shift ;;
    --output-format=*)
      OUTPUT_FORMAT="${1#*=}"
      shift ;;
    --output-file=*)
      OUTPUT_FILE="${1#*=}"
      shift ;;
    *)
      echo "❌ Unknown argument: $1"
      exit 1 ;;
  esac
done

# Set orchestrator defaults
if [[ -n "$ORCHESTRATOR_SESSION" ]]; then
  OUTPUT_FILE=${OUTPUT_FILE:-"/tmp/orchestrator-$ORCHESTRATOR_SESSION/issue-create-result.json"}
  OUTPUT_FORMAT=${OUTPUT_FORMAT:-"json"}
fi
```

### **Step 2: Input Validation and Processing**

```bash
echo "🔍 Validating input parameters..."

# Load from input file if provided
if [[ -n "$INPUT_FILE" && -f "$INPUT_FILE" ]]; then
  echo "📄 Loading issue data from $INPUT_FILE"

  if command -v jq >/dev/null 2>&1; then
    TITLE=${TITLE:-$(cat "$INPUT_FILE" | jq -r '.title // empty')}
    BODY=${BODY:-$(cat "$INPUT_FILE" | jq -r '.body // empty')}
    LABELS=${LABELS:-$(cat "$INPUT_FILE" | jq -r '.labels // empty' | tr -d '[]" ' | tr ',' ' ')}
    ASSIGNEE=${ASSIGNEE:-$(cat "$INPUT_FILE" | jq -r '.assignee // empty')}
  else
    echo "⚠️  jq not available - skipping JSON input file processing"
  fi
fi

# Validate required fields
if [[ -z "$TITLE" ]]; then
  echo "❌ Error: --title is required"
  exit 1
fi

if [[ -z "$BODY" ]]; then
  echo "❌ Error: --body is required"
  exit 1
fi

# Validate GitHub CLI availability
if ! command -v gh >/dev/null 2>&1; then
  echo "❌ Error: GitHub CLI (gh) is not installed"
  echo "💡 Install with: winget install GitHub.cli"
  exit 1
fi

# Check GitHub authentication
if ! gh auth status >/dev/null 2>&1; then
  echo "❌ Error: GitHub CLI not authenticated"
  echo "💡 Run: gh auth login"
  exit 1
fi

echo "✅ Input validation complete"
echo "📋 Title: $TITLE"
echo "📝 Body length: $(echo "$BODY" | wc -c) characters"
echo "🏷️  Labels: ${LABELS:-"none"}"
echo "👤 Assignee: ${ASSIGNEE:-"none"}"
```

### **Step 3: Issue Creation**

```bash
echo "🚀 Creating GitHub issue..."

CREATION_START_TIME=$(date +%s)

# Prepare gh command
GH_CMD="gh issue create --title \"$TITLE\""

# Add body (handle multiline properly)
TEMP_BODY_FILE="/tmp/issue-body-$$.md"
echo "$BODY" > "$TEMP_BODY_FILE"
GH_CMD="$GH_CMD --body-file \"$TEMP_BODY_FILE\""

# Add labels if provided
if [[ -n "$LABELS" ]]; then
  # Convert comma-separated to space-separated and clean up
  CLEAN_LABELS=$(echo "$LABELS" | tr ',' ' ' | tr -d '"[]' | xargs)
  for label in $CLEAN_LABELS; do
    GH_CMD="$GH_CMD --label \"$label\""
  done
fi

# Add assignee if provided
if [[ -n "$ASSIGNEE" ]]; then
  GH_CMD="$GH_CMD --assignee \"$ASSIGNEE\""
fi

# Execute issue creation
echo "🔧 Executing: $GH_CMD"
ISSUE_URL=$(eval $GH_CMD 2>&1)
CREATION_EXIT_CODE=$?
CREATION_END_TIME=$(date +%s)
CREATION_DURATION=$((CREATION_END_TIME - CREATION_START_TIME))

# Clean up temporary file
rm -f "$TEMP_BODY_FILE"

# Check creation result
if [[ $CREATION_EXIT_CODE -eq 0 ]]; then
  echo "✅ Issue created successfully!"
  echo "🔗 URL: $ISSUE_URL"

  # Extract issue number from URL
  ISSUE_NUMBER=$(echo "$ISSUE_URL" | sed -E 's|.*/issues/([0-9]+).*|\1|')

  SUCCESS=true
  ERROR_MESSAGE=""

  # Step 3.1: Trigger relevant GitHub workflows for the new issue
  echo "🔄 Triggering GitHub workflows for issue #$ISSUE_NUMBER..."

  WORKFLOWS_TRIGGERED=0
  WORKFLOW_ERRORS=0

  # Workflow 1: Issue Analysis Workflow
  if gh workflow list --json name,path | jq -r '.[] | select(.name | test("analyze.*issue"; "i")) | .path' | head -1 | read -r ANALYSIS_WORKFLOW; then
    echo "📊 Triggering issue analysis workflow: $ANALYSIS_WORKFLOW"

    if gh workflow run "$ANALYSIS_WORKFLOW" -f "issue_number=$ISSUE_NUMBER" -f "auto_created=true" >/dev/null 2>&1; then
      WORKFLOWS_TRIGGERED=$((WORKFLOWS_TRIGGERED + 1))
      echo "✅ Issue analysis workflow triggered"
    else
      WORKFLOW_ERRORS=$((WORKFLOW_ERRORS + 1))
      echo "⚠️  Failed to trigger issue analysis workflow"
    fi
  fi

  # Workflow 2: Label-specific workflows
  if [[ -n "$LABELS" ]]; then
    # Check for architecture-related labels
    if echo "$LABELS" | grep -qi "architecture\|tech-debt"; then
      ARCH_WORKFLOW=$(gh workflow list --json name,path | jq -r '.[] | select(.name | test("architecture.*review"; "i")) | .path' | head -1)

      if [[ -n "$ARCH_WORKFLOW" ]]; then
        echo "🏗️  Triggering architecture review workflow: $ARCH_WORKFLOW"

        if gh workflow run "$ARCH_WORKFLOW" -f "issue_number=$ISSUE_NUMBER" -f "scope=targeted" >/dev/null 2>&1; then
          WORKFLOWS_TRIGGERED=$((WORKFLOWS_TRIGGERED + 1))
          echo "✅ Architecture review workflow triggered"
        else
          WORKFLOW_ERRORS=$((WORKFLOW_ERRORS + 1))
          echo "⚠️  Failed to trigger architecture workflow"
        fi
      fi
    fi

    # Check for database-related labels
    if echo "$LABELS" | grep -qi "database\|migration"; then
      DB_WORKFLOW=$(gh workflow list --json name,path | jq -r '.[] | select(.name | test("database.*analysis"; "i")) | .path' | head -1)

      if [[ -n "$DB_WORKFLOW" ]]; then
        echo "💾 Triggering database analysis workflow: $DB_WORKFLOW"

        if gh workflow run "$DB_WORKFLOW" -f "issue_number=$ISSUE_NUMBER" -f "focus=migration" >/dev/null 2>&1; then
          WORKFLOWS_TRIGGERED=$((WORKFLOWS_TRIGGERED + 1))
          echo "✅ Database analysis workflow triggered"
        else
          WORKFLOW_ERRORS=$((WORKFLOW_ERRORS + 1))
          echo "⚠️  Failed to trigger database workflow"
        fi
      fi
    fi

    # Check for critical/bug labels
    if echo "$LABELS" | grep -qi "critical\|bug"; then
      URGENT_WORKFLOW=$(gh workflow list --json name,path | jq -r '.[] | select(.name | test("urgent.*triage"; "i")) | .path' | head -1)

      if [[ -n "$URGENT_WORKFLOW" ]]; then
        echo "🚨 Triggering urgent triage workflow: $URGENT_WORKFLOW"

        if gh workflow run "$URGENT_WORKFLOW" -f "issue_number=$ISSUE_NUMBER" -f "severity=critical" >/dev/null 2>&1; then
          WORKFLOWS_TRIGGERED=$((WORKFLOWS_TRIGGERED + 1))
          echo "✅ Urgent triage workflow triggered"
        else
          WORKFLOW_ERRORS=$((WORKFLOW_ERRORS + 1))
          echo "⚠️  Failed to trigger urgent workflow"
        fi
      fi
    fi
  fi

  # Workflow 3: General issue processing workflow
  GENERAL_WORKFLOW=$(gh workflow list --json name,path | jq -r '.[] | select(.name | test("issue.*process"; "i")) | .path' | head -1)

  if [[ -n "$GENERAL_WORKFLOW" ]]; then
    echo "⚙️  Triggering general issue processing: $GENERAL_WORKFLOW"

    # Build workflow inputs
    WORKFLOW_INPUTS="-f issue_number=$ISSUE_NUMBER -f created_by=claude-code"

    if [[ -n "$LABELS" ]]; then
      WORKFLOW_INPUTS="$WORKFLOW_INPUTS -f labels=\"$LABELS\""
    fi

    if gh workflow run "$GENERAL_WORKFLOW" $WORKFLOW_INPUTS >/dev/null 2>&1; then
      WORKFLOWS_TRIGGERED=$((WORKFLOWS_TRIGGERED + 1))
      echo "✅ General processing workflow triggered"
    else
      WORKFLOW_ERRORS=$((WORKFLOW_ERRORS + 1))
      echo "⚠️  Failed to trigger general workflow"
    fi
  fi

  echo "🔄 Workflow Summary: $WORKFLOWS_TRIGGERED triggered, $WORKFLOW_ERRORS errors"

else
  echo "❌ Failed to create issue"
  echo "Error: $ISSUE_URL"

  SUCCESS=false
  ERROR_MESSAGE="$ISSUE_URL"
  ISSUE_URL=""
  ISSUE_NUMBER=""
  WORKFLOWS_TRIGGERED=0
  WORKFLOW_ERRORS=0
fi
```

### **Step 4: Response Generation**

```bash
echo "📊 Generating response..."

# Create structured output for orchestrator integration
if [[ "$OUTPUT_FORMAT" == "json" && -n "$OUTPUT_FILE" ]]; then
  cat > "$OUTPUT_FILE" << EOF
{
  "orchestratorResult": {
    "commandName": "issue-create",
    "sessionId": "$ORCHESTRATOR_SESSION",
    "status": "$(if [[ "$SUCCESS" == true ]]; then echo "completed"; else echo "failed"; fi)",
    "executionTime": $CREATION_DURATION,
    "startTime": "$(date -d @$CREATION_START_TIME -Iseconds)",
    "endTime": "$(date -d @$CREATION_END_TIME -Iseconds)"
  },
  "results": {
    "success": $SUCCESS,
    "issueUrl": "$ISSUE_URL",
    "issueNumber": "$ISSUE_NUMBER",
    "title": "$TITLE",
    "labels": [$(echo "$LABELS" | tr ' ' '\n' | sed 's/.*/\"&\"/' | paste -sd ',' -)],
    "assignee": "$ASSIGNEE",
    "creationTime": $CREATION_DURATION,
    "workflowsTriggered": $WORKFLOWS_TRIGGERED,
    "workflowErrors": $WORKFLOW_ERRORS
  },
  "error": {
    "occurred": $(if [[ "$SUCCESS" == true ]]; then echo "false"; else echo "true"; fi),
    "message": "$ERROR_MESSAGE"
  },
  "recommendations": [
    "$(if [[ "$SUCCESS" == true ]]; then echo "Issue created successfully - consider adding to project board"; else echo "Check GitHub permissions and network connectivity"; fi)"
  ],
  "nextActions": [
    "$(if [[ "$SUCCESS" == true ]]; then echo "Review and triage the created issue"; else echo "Resolve creation error and retry"; fi)"
  ]
}
EOF
fi

# Generate human-readable output
if [[ "$OUTPUT_FORMAT" == "text" || "$OUTPUT_FORMAT" == "mixed" ]]; then
  if [[ "$SUCCESS" == true ]]; then
    echo ""
    echo "🎉 SUCCESS: GitHub issue created!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 Title: $TITLE"
    echo "🔢 Issue #$ISSUE_NUMBER"
    echo "🔗 URL: $ISSUE_URL"
    echo "🏷️  Labels: ${LABELS:-"none"}"
    echo "👤 Assignee: ${ASSIGNEE:-"unassigned"}"
    echo "⏱️  Created in: ${CREATION_DURATION}s"
    echo "🔄 Workflows: $WORKFLOWS_TRIGGERED triggered, $WORKFLOW_ERRORS errors"
    echo ""
    echo "💡 Next steps:"
    echo "   • Review and refine issue description"
    echo "   • Add to appropriate project board"
    echo "   • Set priority and milestone"
    echo "   • Link related issues or PRs"
  else
    echo ""
    echo "❌ FAILED: Could not create GitHub issue"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 Title: $TITLE"
    echo "❗ Error: $ERROR_MESSAGE"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   • Check GitHub authentication: gh auth status"
    echo "   • Verify repository permissions"
    echo "   • Ensure network connectivity"
    echo "   • Check rate limits: gh api rate_limit"
  fi
fi
```

### **Step 5: Command Self-Evaluation**

```bash
# Track command performance for continuous improvement
COMMAND_METRICS_FILE=".claude/commands/.issue-create-metrics.json"

cat >> "$COMMAND_METRICS_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "executionTime": $CREATION_DURATION,
  "success": $SUCCESS,
  "titleLength": $(echo "$TITLE" | wc -c),
  "bodyLength": $(echo "$BODY" | wc -c),
  "labelsCount": $(echo "$LABELS" | wc -w),
  "hasAssignee": $(if [[ -n "$ASSIGNEE" ]]; then echo "true"; else echo "false"; fi),
  "issueNumber": "$ISSUE_NUMBER"
}
EOF

echo "🤖 Performance metrics logged for continuous improvement"

# Exit with appropriate code
if [[ "$SUCCESS" == true ]]; then
  exit 0
else
  exit 1
fi
```

## GitHub Workflow Integration

The command automatically triggers relevant GitHub workflows after creating issues:

### **Workflow Detection and Triggering**

```bash
# The command intelligently detects and triggers workflows based on:

# 1. Issue Analysis Workflows
gh workflow run "analyze-existing-issues.yml" -f "issue_number=$ISSUE_NUMBER" -f "auto_created=true"

# 2. Label-specific Workflows
- architecture/tech-debt → architecture-review.yml
- database/migration → database-analysis.yml
- critical/bug → urgent-triage.yml

# 3. General Processing
gh workflow run "issue-process.yml" -f "issue_number=$ISSUE_NUMBER" -f "created_by=claude-code"
```

### **Supported Workflow Patterns**

```yaml
# Example: analyze-existing-issues.yml
name: Analyze Issues
on:
  workflow_dispatch:
    inputs:
      issue_number:
        description: 'Issue number to analyze'
        required: true
      auto_created:
        description: 'Was this issue auto-created'
        required: false
        default: 'false'
      max_issues:
        description: 'Maximum issues to process'
        required: false
        default: '5'
      skip_analyzed:
        description: 'Skip already analyzed issues'
        required: false
        default: 'true'
```

## Integration Examples

### **Usage by /architect Command**

```bash
# In architect.md, after generating findings
if [[ $CRITICAL_ISSUES -gt 0 ]]; then
  echo "🎯 Creating GitHub issues for critical findings..."

  for issue in "${CRITICAL_FINDINGS[@]}"; do
    ISSUE_TITLE=$(echo "$issue" | jq -r '.title')
    ISSUE_BODY=$(echo "$issue" | jq -r '.body')
    ISSUE_LABELS=$(echo "$issue" | jq -r '.labels | join(",")')

    # Creates issue AND triggers relevant workflows automatically
    /issue-create --title="$ISSUE_TITLE" --body="$ISSUE_BODY" --labels="$ISSUE_LABELS,architecture"
  done
fi
```

### **Usage by Other Commands**

```bash
# Quick issue creation from any command
/issue-create --title="Performance Degradation Detected" --body="Command execution time increased by 40% over baseline" --labels="performance,bug"

# Complex issue with detailed analysis
ISSUE_BODY=$(cat << 'EOF'
## Problem Description
Database migration analysis detected critical safety issues.

## Issues Found
- 5 migrations without transaction boundaries
- 3 column renames without existence checks
- 2 destructive operations without rollback plans

## Recommendations
1. Add IF EXISTS checks to all column operations
2. Wrap migrations in explicit transactions
3. Create rollback procedures

## Analysis Data
See attached migration-analysis.json for detailed findings.
EOF
)

/issue-create --title="Critical Migration Safety Issues" --body="$ISSUE_BODY" --labels="database,migration,critical,tech-debt"
```

---

**Note:** This command provides a clean, reusable interface for GitHub issue creation that integrates seamlessly with the TribeVibe command ecosystem and orchestrator patterns.