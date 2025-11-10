#!/bin/bash
# Update all PR branches with Gemini review fixes

set -e

WESCOBAR_DIR="/mnt/d/berry/Projects/Wescobar"
WORK_DIR="/tmp/claude-config-deployment"
BRANCH_NAME="claude/add-gh-auth-hooks-20251101"

REPOS=(
  "TribeVibe"
  "home-sage"
  "TuneScout"
  "SceneSpeak"
  "quantfolio"
  "AgenticDevelopment"
  "TetherKey"
  "mcp-servers"
  "mcp-qdrant"
  "GreenSphere-"
  "oraculum"
  "audiotagger_2025"
  "MixItUp"
  "Rijwijs"
)

echo "🔄 Updating PR branches with Gemini review fixes..."
echo "Source: $WESCOBAR_DIR"
echo ""

SUCCESS=0
FAILED=0

for REPO in "${REPOS[@]}"; do
  echo "---"
  echo "📦 Updating: $REPO"

  cd "$WORK_DIR/$REPO"

  # Checkout the PR branch
  git checkout "$BRANCH_NAME"

  # Copy updated files
  cp "$WESCOBAR_DIR/scripts/gh-login-if-token.sh" scripts/
  cp "$WESCOBAR_DIR/scripts/install-gh-cli.sh" scripts/
  cp "$WESCOBAR_DIR/docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md" docs/ 2>/dev/null || true
  cp "$WESCOBAR_DIR/docs/COPY_TO_NEW_REPO.md" docs/ 2>/dev/null || true

  # Fix tempDir in config.yml (use repo-specific name)
  if [ -f ".claude/config.yml" ]; then
    REPO_LOWER=$(echo "$REPO" | tr '[:upper:]' '[:lower:]' | tr '-' '-')
    sed -i "s|tempDir: \"/tmp/.*-orchestrator\"|tempDir: \"/tmp/${REPO_LOWER}-orchestrator\"|" .claude/config.yml
  fi

  # Check if there are changes
  if git diff --quiet; then
    echo "  ℹ️  No changes"
    continue
  fi

  # Commit and push
  git add scripts/ docs/ .claude/config.yml 2>/dev/null || git add scripts/
  git commit -m "fix: Address Gemini code review feedback

- Always create state file in gh-login-if-token.sh
- Use set -Eeuo pipefail for better error handling
- Remove apt-get example (requires root)
- Document chmod for all scripts
- Fix tempDir to use lowercase repo name

Addresses all Gemini Code Assist review suggestions."

  git push

  if [ $? -eq 0 ]; then
    echo "  ✅ Updated successfully"
    SUCCESS=$((SUCCESS + 1))
  else
    echo "  ❌ Push failed"
    FAILED=$((FAILED + 1))
  fi
done

echo ""
echo "📊 Update Summary:"
echo "  ✅ Success: $SUCCESS"
echo "  ❌ Failed: $FAILED"
echo "Done!"
