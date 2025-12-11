#!/bin/bash
# Import GitHub issues into harness feature_list.json
# Usage: import-github-issues.sh [--label LABEL] [--milestone MILESTONE] [--limit N] [--issue NUMBER]

set -e

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
HARNESS_DIR="$PROJECT_ROOT/.claude/harness"
FEATURE_LIST="$HARNESS_DIR/feature_list.json"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
LABELS=""
MILESTONE=""
LIMIT=50
SINGLE_ISSUE=""
STATE="open"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --label|-l)
      LABELS="$2"
      shift 2
      ;;
    --milestone|-m)
      MILESTONE="$2"
      shift 2
      ;;
    --limit|-n)
      LIMIT="$2"
      shift 2
      ;;
    --issue|-i)
      SINGLE_ISSUE="$2"
      shift 2
      ;;
    --state|-s)
      STATE="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: import-github-issues.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  -l, --label LABEL      Filter by label (comma-separated)"
      echo "  -m, --milestone NAME   Filter by milestone"
      echo "  -n, --limit N          Max issues to import (default: 50)"
      echo "  -i, --issue NUMBER     Import single issue by number"
      echo "  -s, --state STATE      Issue state: open, closed, all (default: open)"
      echo "  -h, --help             Show this help"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check gh CLI
if ! command -v gh &> /dev/null; then
  echo "Error: gh CLI not found. Install with: scripts/install-gh-cli.sh"
  exit 1
fi

# Check jq
if ! command -v jq &> /dev/null; then
  echo "Error: jq not found. Install jq to use this script."
  exit 1
fi

# Check gh auth
if ! gh auth status &> /dev/null; then
  echo "Error: Not authenticated with GitHub. Run: gh auth login"
  exit 1
fi

# Create harness directory
mkdir -p "$HARNESS_DIR"

# Get repo name
REPO_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null)" || basename "$PROJECT_ROOT")

echo -e "${BLUE}=== Importing GitHub Issues to Harness ===${NC}"
echo "Repository: $REPO_NAME"

# Build gh command
GH_CMD="gh issue list --state $STATE --limit $LIMIT --json number,title,body,labels,milestone,assignees,createdAt,updatedAt"

if [ -n "$LABELS" ]; then
  GH_CMD="$GH_CMD --label \"$LABELS\""
  echo "Labels: $LABELS"
fi

if [ -n "$MILESTONE" ]; then
  GH_CMD="$GH_CMD --milestone \"$MILESTONE\""
  echo "Milestone: $MILESTONE"
fi

# Single issue mode
if [ -n "$SINGLE_ISSUE" ]; then
  echo "Importing issue #$SINGLE_ISSUE..."
  GH_CMD="gh issue view $SINGLE_ISSUE --json number,title,body,labels,milestone,assignees,createdAt,updatedAt"
  ISSUES=$(eval "$GH_CMD" | jq '[.]')
else
  echo "Fetching issues..."
  ISSUES=$(eval "$GH_CMD")
fi

# Count issues
COUNT=$(echo "$ISSUES" | jq 'length')
echo -e "${GREEN}Found $COUNT issue(s)${NC}"

if [ "$COUNT" -eq 0 ]; then
  echo "No issues to import."
  exit 0
fi

# Transform to feature_list.json format
echo "$ISSUES" | jq --arg repo "$REPO_NAME" '{
  project: {
    name: $repo,
    description: "Features imported from GitHub issues"
  },
  features: [.[] | {
    id: "issue-\(.number)",
    name: .title,
    description: (.body // "No description"),
    status: "pending",
    priority: (
      if (.labels | map(.name) | any(test("priority.*critical|critical|P0"; "i"))) then "critical"
      elif (.labels | map(.name) | any(test("priority.*high|high|P1"; "i"))) then "high"
      elif (.labels | map(.name) | any(test("priority.*low|low|P3"; "i"))) then "low"
      else "medium"
      end
    ),
    github_issue: .number,
    labels: [.labels[].name],
    milestone: (.milestone.title // null),
    assignees: [.assignees[].login],
    created_at: .createdAt,
    updated_at: .updatedAt
  }],
  metadata: {
    version: "1.0.0",
    source: "github",
    repository: $repo,
    imported_at: (now | todate),
    total_features: (. | length),
    completed_features: 0
  }
}' > "$FEATURE_LIST"

echo -e "${GREEN}Imported $COUNT features to: $FEATURE_LIST${NC}"
echo ""
echo "Features:"
jq -r '.features[] | "  - [\(.id)] \(.name) (\(.priority))"' "$FEATURE_LIST"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review: cat $FEATURE_LIST | jq ."
echo "  2. Start working on features"
echo "  3. Update status as you complete them"
