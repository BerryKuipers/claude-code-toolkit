#!/bin/bash
# Merge remaining PRs that failed with auto-merge
# Using direct squash merge without --auto flag

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔀 Merging remaining gh-auth-hooks PRs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# List of repositories with open PRs that failed to merge
REPOS=(
  "BerryKuipers/mcp-servers:1"
  "BerryKuipers/SceneSpeak:79"
  "BerryKuipers/MixItUp:57"
  "BerryKuipers/audiotagger_2025:2"
  "BerryKuipers/AgenticDevelopment:36"
  "BerryKuipers/quantfolio:3"
  "BerryKuipers/oraculum:48"
  "BerryKuipers/mcp-qdrant:1"
  "BerryKuipers/GreenSphere-:1"
  "BerryKuipers/TetherKey:62"
  "BerryKuipers/TribeVibe:183"
)

MERGED=0
FAILED=0
SKIPPED=0

for REPO_PR in "${REPOS[@]}"; do
  REPO="${REPO_PR%:*}"
  PR_NUM="${REPO_PR#*:}"
  REPO_NAME="${REPO#*/}"

  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📦 Merging: $REPO_NAME (PR #$PR_NUM)"

  # Check PR status
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

  # Check if mergeable
  MERGEABLE=$(gh pr view "$PR_NUM" --repo "$REPO" --json mergeable --jq '.mergeable' 2>/dev/null || echo "UNKNOWN")

  if [ "$MERGEABLE" = "CONFLICTING" ]; then
    echo "  ⚠️  PR has merge conflicts, cannot merge"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # Merge without --auto flag (direct merge)
  echo "  🔀 Merging..."
  if gh pr merge "$PR_NUM" --repo "$REPO" --squash --delete-branch; then
    echo "  ✅ Merged successfully!"
    MERGED=$((MERGED + 1))
  else
    echo "  ❌ Merge failed"
    FAILED=$((FAILED + 1))
  fi

  sleep 2
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Merge Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Merged: $MERGED"
echo "  ⏭️  Skipped: $SKIPPED"
echo "  ❌ Failed: $FAILED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $MERGED -gt 0 ]; then
  echo ""
  echo "🎉 Successfully merged $MERGED PRs!"
fi

if [ $FAILED -gt 0 ]; then
  echo ""
  echo "⚠️  $FAILED PRs failed to merge."
  exit 1
fi

echo ""
echo "✅ All done!"
