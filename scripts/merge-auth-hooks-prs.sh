#!/bin/bash
# Merge all open PRs with gh CLI authentication hooks
# Based on the successfully merged Rijwijs PR implementation

set -e

echo "🔀 Merging all open gh-auth-hooks PRs..."
echo ""

# List of repositories with open PRs (from gh search results)
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

SUCCESS=0
FAILED=0
SKIPPED=0

for REPO_PR in "${REPOS[@]}"; do
  REPO="${REPO_PR%:*}"
  PR_NUM="${REPO_PR#*:}"
  REPO_NAME="${REPO#*/}"

  echo "---"
  echo "📦 Processing: $REPO_NAME (PR #$PR_NUM)"

  # Check PR status first
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

  # Check if PR is mergeable (no conflicts)
  MERGEABLE=$(gh pr view "$PR_NUM" --repo "$REPO" --json mergeable --jq '.mergeable' 2>/dev/null || echo "UNKNOWN")

  if [ "$MERGEABLE" = "CONFLICTING" ]; then
    echo "  ⚠️  PR has merge conflicts, skipping"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # Check CI status
  CI_STATUS=$(gh pr view "$PR_NUM" --repo "$REPO" --json statusCheckRollup --jq '.statusCheckRollup | if . == null or . == [] then "NONE" else (map(.state) | if any(. == "FAILURE") then "FAILURE" elif any(. == "PENDING") then "PENDING" else "SUCCESS" end) end' 2>/dev/null || echo "UNKNOWN")

  if [ "$CI_STATUS" = "FAILURE" ]; then
    echo "  ⚠️  CI checks failing, skipping"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  if [ "$CI_STATUS" = "PENDING" ]; then
    echo "  ⏳ CI checks still running, skipping for now"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # Get PR details for confirmation
  PR_TITLE=$(gh pr view "$PR_NUM" --repo "$REPO" --json title --jq '.title')
  echo "  📋 Title: $PR_TITLE"
  echo "  ✅ Mergeable: Yes"
  echo "  ✅ CI Status: $CI_STATUS"

  # Merge the PR using squash merge (clean history)
  echo "  🔀 Merging..."
  if gh pr merge "$PR_NUM" --repo "$REPO" --squash --delete-branch --auto; then
    echo "  ✅ Merged successfully"
    SUCCESS=$((SUCCESS + 1))
  else
    echo "  ❌ Merge failed"
    FAILED=$((FAILED + 1))
  fi

  # Brief pause between merges
  sleep 2
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Merge Summary:"
echo "  ✅ Successfully merged: $SUCCESS"
echo "  ❌ Failed: $FAILED"
echo "  ⏭️  Skipped: $SKIPPED"
echo "  📝 Total processed: ${#REPOS[@]}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $FAILED -gt 0 ]; then
  echo "⚠️  Some PRs failed to merge. Check the output above for details."
  exit 1
fi

if [ $SUCCESS -eq 0 ]; then
  echo "ℹ️  No PRs were merged (all skipped or failed)."
  exit 0
fi

echo "🎉 All eligible PRs merged successfully!"
echo ""
echo "💡 Note: Skipped PRs may need manual attention:"
echo "  - Check for merge conflicts"
echo "  - Wait for CI checks to complete"
echo "  - Review any failing tests"
