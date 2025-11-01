#!/bin/bash
# Update all open PRs with the gh-detect-or-fallback.sh fix and merge them
# This fixes the cosmetic warning "⚠️ gh CLI status unknown" on session start

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_SCRIPT="$SCRIPT_DIR/gh-detect-or-fallback.sh"
WORK_DIR="/tmp/claude-pr-updates"
BRANCH_NAME="claude/add-gh-auth-hooks-20251101"

# List of repositories with open PRs (repo:PR_number)
REPOS=(
  "BerryKuipers/mcp-servers:1"
  "BerryKuipers/SceneSpeak:79"
  "BerryKuipers/MixItUp:57"
  "BerryKuipers/audiotagger_2025:2"
  "BerryKuipers/TuneScout:113"
  "BerryKuipers/AgenticDevelopment:36"
  "BerryKuipers/quantfolio:3"
  "BerryKuipers/oraculum:48"
  "BerryKuipers/home-sage:3"
  "BerryKuipers/mcp-qdrant:1"
  "BerryKuipers/GreenSphere-:1"
  "BerryKuipers/TetherKey:62"
  "BerryKuipers/TribeVibe:183"
)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Updating and Merging gh-auth-hooks PRs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Fix: Remove premature warning in gh-detect-or-fallback.sh"
echo "Source: $SOURCE_SCRIPT"
echo ""

# Verify source script exists
if [ ! -f "$SOURCE_SCRIPT" ]; then
  echo "❌ Source script not found: $SOURCE_SCRIPT"
  exit 1
fi

# Create work directory
mkdir -p "$WORK_DIR"

UPDATED=0
MERGED=0
FAILED=0
SKIPPED=0

for REPO_PR in "${REPOS[@]}"; do
  REPO="${REPO_PR%:*}"
  PR_NUM="${REPO_PR#*:}"
  REPO_NAME="${REPO#*/}"

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📦 Processing: $REPO_NAME (PR #$PR_NUM)"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

  # Check PR status first
  echo "  → Checking PR status..."
  PR_STATE=$(gh pr view "$PR_NUM" --repo "$REPO" --json state --jq '.state' 2>/dev/null || echo "ERROR")

  if [ "$PR_STATE" = "ERROR" ]; then
    echo "  ❌ Failed to get PR status"
    FAILED=$((FAILED + 1))
    continue
  fi

  if [ "$PR_STATE" != "OPEN" ]; then
    echo "  ⏭️  PR is $PR_STATE, skipping"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # Clone/checkout the PR branch
  REPO_DIR="$WORK_DIR/$REPO_NAME"

  if [ -d "$REPO_DIR" ]; then
    echo "  → Using existing clone at $REPO_DIR"
    cd "$REPO_DIR"
    git fetch origin "$BRANCH_NAME"
    git checkout "$BRANCH_NAME"
    git pull origin "$BRANCH_NAME"
  else
    echo "  → Cloning repository..."
    cd "$WORK_DIR"
    gh repo clone "$REPO" "$REPO_NAME" -- --depth 1 --no-single-branch
    cd "$REPO_DIR"
    git checkout "$BRANCH_NAME"
  fi

  # Update the gh-detect-or-fallback.sh script
  echo "  → Updating gh-detect-or-fallback.sh..."

  if [ ! -f "scripts/gh-detect-or-fallback.sh" ]; then
    echo "  ⚠️  Script not found in repo, skipping"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # Copy the fixed script
  cp "$SOURCE_SCRIPT" scripts/gh-detect-or-fallback.sh
  chmod +x scripts/gh-detect-or-fallback.sh

  # Check if there are changes
  if git diff --quiet; then
    echo "  ℹ️  No changes needed"
    # Even if no changes, try to merge if PR is ready
  else
    # Commit and push the changes
    echo "  → Committing changes..."
    git add scripts/gh-detect-or-fallback.sh
    git commit -m "fix: Remove premature gh CLI warning during SessionStart

- Don't show 'gh CLI status unknown' warning during initial setup
- Check if gh is actually installed and authenticated before warning
- Only show warning if gh CLI is truly unavailable after setup

This fixes the cosmetic warning that appeared before gh CLI installation
completed during SessionStart hook execution.

Improves user experience by eliminating false warnings."

    echo "  → Pushing to remote..."
    if ! git push origin "$BRANCH_NAME"; then
      echo "  ❌ Push failed"
      FAILED=$((FAILED + 1))
      continue
    fi

    echo "  ✅ Updated successfully"
    UPDATED=$((UPDATED + 1))
  fi

  # Now try to merge the PR
  echo "  → Checking if PR is ready to merge..."

  # Check if PR is mergeable (no conflicts)
  MERGEABLE=$(gh pr view "$PR_NUM" --repo "$REPO" --json mergeable --jq '.mergeable' 2>/dev/null || echo "UNKNOWN")

  if [ "$MERGEABLE" = "CONFLICTING" ]; then
    echo "  ⚠️  PR has merge conflicts, cannot merge"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # Check CI status
  CI_STATUS=$(gh pr view "$PR_NUM" --repo "$REPO" --json statusCheckRollup --jq '.statusCheckRollup | if . == null or . == [] then "NONE" else (map(.state) | if any(. == "FAILURE") then "FAILURE" elif any(. == "PENDING") then "PENDING" else "SUCCESS" end) end' 2>/dev/null || echo "UNKNOWN")

  if [ "$CI_STATUS" = "FAILURE" ]; then
    echo "  ⚠️  CI checks failing, skipping merge"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  if [ "$CI_STATUS" = "PENDING" ]; then
    echo "  ⏳ CI checks still running, skipping merge for now"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  echo "  ✅ PR is ready to merge"
  echo "     - State: $PR_STATE"
  echo "     - Mergeable: $MERGEABLE"
  echo "     - CI Status: $CI_STATUS"

  # Merge the PR using squash merge
  echo "  🔀 Merging PR..."
  if gh pr merge "$PR_NUM" --repo "$REPO" --squash --delete-branch --auto; then
    echo "  ✅ Merged successfully!"
    MERGED=$((MERGED + 1))
  else
    echo "  ❌ Merge failed"
    FAILED=$((FAILED + 1))
  fi

  echo ""
  # Brief pause between operations
  sleep 2
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Final Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📝 Total PRs processed: ${#REPOS[@]}"
echo "  🔄 PRs updated: $UPDATED"
echo "  ✅ PRs merged: $MERGED"
echo "  ⏭️  PRs skipped: $SKIPPED"
echo "  ❌ PRs failed: $FAILED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $MERGED -gt 0 ]; then
  echo "🎉 Successfully merged $MERGED PRs!"
  echo ""
  echo "✨ The gh CLI authentication hooks are now deployed to:"
  for REPO_PR in "${REPOS[@]}"; do
    REPO="${REPO_PR%:*}"
    PR_NUM="${REPO_PR#*:}"
    REPO_NAME="${REPO#*/}"

    # Check if it was merged
    PR_STATE=$(gh pr view "$PR_NUM" --repo "$REPO" --json state --jq '.state' 2>/dev/null || echo "")
    if [ "$PR_STATE" = "MERGED" ]; then
      echo "   ✅ $REPO_NAME"
    fi
  done
fi

if [ $SKIPPED -gt 0 ]; then
  echo ""
  echo "ℹ️  $SKIPPED PRs were skipped. Common reasons:"
  echo "   - PR already merged or closed"
  echo "   - Merge conflicts present"
  echo "   - CI checks still running or failing"
  echo "   - No changes needed"
fi

if [ $FAILED -gt 0 ]; then
  echo ""
  echo "⚠️  $FAILED PRs failed. Check the output above for details."
  exit 1
fi

echo ""
echo "✅ All done!"
