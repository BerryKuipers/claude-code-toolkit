#!/bin/bash
# Deploy Claude Code Toolkit as Submodule (Cross-Platform)
# Usage: ./scripts/deploy-toolkit-submodule.sh [repo-name]
#
# Features:
# - Disables commit signing to prevent signing errors
# - Cross-platform compatible (Windows/Linux/Mac)
# - Automatic SessionStart hook setup
# - Idempotent (safe to run multiple times)

set -e

GITHUB_USER="BerryKuipers"
TOOLKIT_REPO="https://github.com/${GITHUB_USER}/claude-code-toolkit.git"
WORK_DIR="/tmp/toolkit-deployment"
BRANCH_PREFIX="claude/add-toolkit-submodule"

# Get repo name from argument or default to home-sage
REPO_NAME="${1:-home-sage}"

echo "🚀 Deploying Claude Code Toolkit to $REPO_NAME..."
echo ""

# Create work directory
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Clone repository
REPO_DIR="$WORK_DIR/$REPO_NAME"
if [ -d "$REPO_DIR" ]; then
  echo "  → Updating existing clone..."
  cd "$REPO_DIR"
  git fetch origin
else
  echo "  → Cloning $REPO_NAME..."
  if ! ~/.local/bin/gh repo clone "$GITHUB_USER/$REPO_NAME" "$REPO_DIR"; then
    echo "  ❌ Failed to clone $REPO_NAME"
    exit 1
  fi
  cd "$REPO_DIR"
fi

# Get default branch
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
echo "  → Default branch: $DEFAULT_BRANCH"

# Configure git auth
git config credential.helper ""
git config --local credential.helper '!/root/.local/bin/gh auth git-credential'

# Disable commit signing to avoid signing errors
git config --local commit.gpgsign false

# Checkout default branch
git checkout "$DEFAULT_BRANCH"
git pull origin "$DEFAULT_BRANCH"

# Create feature branch
BRANCH_NAME="${BRANCH_PREFIX}-$(date +%Y%m%d)"
echo "  → Creating branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME" 2>/dev/null || git checkout "$BRANCH_NAME"

echo ""
echo "📦 Adding toolkit as submodule..."

# Check if submodule already exists
if [ -f ".gitmodules" ] && grep -q "claude-code-toolkit" ".gitmodules"; then
  echo "  ⚠️  Toolkit submodule already exists"
else
  # Add submodule (disable signing for submodule operations)
  git submodule add "$TOOLKIT_REPO" .claude-toolkit
  git submodule init
  git submodule update

  # Disable signing in submodule too
  cd .claude-toolkit
  git config --local commit.gpgsign false
  cd ..

  echo "  ✅ Submodule added"
fi

echo ""
echo "📝 Creating/updating configuration..."

# Create scripts directory
mkdir -p scripts

# Copy bootstrap script from toolkit (critical - must exist in parent repo)
echo "  → Copying bootstrap script..."
cp .claude-toolkit/scripts/bootstrap-toolkit.sh scripts/
chmod +x scripts/bootstrap-toolkit.sh

# Copy sync script from toolkit (backup, can also be run directly)
echo "  → Copying sync script..."
cp .claude-toolkit/scripts/sync-claude-toolkit.sh scripts/
chmod +x scripts/sync-claude-toolkit.sh

# Copy gh CLI installer if not present
if [ ! -f "scripts/install-gh-cli.sh" ]; then
  echo "  → Copying gh CLI installer..."
  cp .claude-toolkit/scripts/install-gh-cli.sh scripts/
  chmod +x scripts/install-gh-cli.sh
fi

# Create or update settings.json
mkdir -p .claude
if [ ! -f ".claude/settings.json" ]; then
  echo "  → Creating settings.json..."
  cat > .claude/settings.json <<'EOF'
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "bash $(git rev-parse --show-toplevel)/scripts/bootstrap-toolkit.sh"
          }
        ]
      }
    ]
  }
}
EOF
else
  echo "  ⚠️  settings.json exists, please manually add sync hook"
fi

# Create .gitignore for synced files
echo "  → Updating .gitignore..."

# Remove blanket .claude/ ignore if exists (it blocks exceptions like !.claude/settings.json)
if grep -q "^\.claude/$" .gitignore 2>/dev/null; then
  echo "  → Removing blanket .claude/ ignore (incompatible with toolkit)"
  sed -i '/^\.claude\/$/d' .gitignore
fi

cat >> .gitignore <<'EOF'

# Claude Code Toolkit - Synced Files (don't commit duplicates)
.claude/agents/
.claude/commands/
.claude/skills/
.claude/api-skills-source/

# Claude Code Toolkit - Keep These (project-specific or reference content)
!.claude/settings.json
!.claude/config.yml
!.claude/local/
!.claude/prompts/
# Note: prompts/ is synced but NOT ignored - it's reference content that can be customized per project
EOF

# Run initial bootstrap (sets up toolkit and syncs)
echo ""
echo "🔄 Running initial bootstrap..."
./scripts/bootstrap-toolkit.sh

# Verify sync
AGENT_COUNT=$(ls .claude/agents/ 2>/dev/null | wc -l || echo "0")
COMMAND_COUNT=$(ls .claude/commands/ 2>/dev/null | wc -l || echo "0")

echo "  ✅ Synced: $AGENT_COUNT agents, $COMMAND_COUNT commands"

echo ""
echo "📋 Staging changes..."
git add .claude-toolkit .gitmodules scripts/ .claude/settings.json .gitignore

# Check if there are changes
if git diff --cached --quiet; then
  echo "  ℹ️  No changes to commit"
  exit 0
fi

echo ""
echo "💾 Committing..."
git commit -m "$(cat <<'EOF'
feat: Add Claude Code Toolkit with bootstrap initialization

Integrated claude-code-toolkit for universal agent/command/skill management.

Changes:
✅ Added .claude-toolkit as git submodule
✅ Deployed bootstrap-toolkit.sh to parent repo (solves chicken-and-egg problem)
✅ SessionStart hook uses bootstrap script from parent repo
✅ Added .gitignore for synced files

Bootstrap Solution:
The bootstrap script lives in the PARENT repo (not the submodule), so it can
run even when .claude-toolkit doesn't exist yet. It:
1. Detects if toolkit is missing
2. Attempts to clone using local proxy URL pattern
3. Falls back gracefully with clear instructions if blocked
4. Runs sync if successful

This solves the chicken-and-egg problem where SessionStart hooks couldn't
call scripts from .claude-toolkit/ because the submodule wasn't initialized.

Cross-Platform & Proxy-Aware:
- Works on Windows (Git Bash), Linux, Mac
- No symlinks required (file copy approach)
- Auto-detects Claude Code web session proxy
- Gracefully handles proxy restrictions
- Clear feedback when blocked vs successful

Files Synced from Toolkit:
- .claude/agents/ (15 specialized agents)
- .claude/commands/ (42 slash commands)
- .claude/skills/ (14 skills)
- .claude/api-skills-source/ (API skills)

SessionStart Hook (single command):
bash $(git rev-parse --show-toplevel)/scripts/bootstrap-toolkit.sh

Benefits:
✅ Single source of truth (claude-code-toolkit)
✅ Works in Claude Code web sessions
✅ Self-healing on session start
✅ Easy updates across all projects

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

echo ""
echo "⬆️  Pushing to GitHub..."

# Push with retry logic (up to 4 retries with exponential backoff)
PUSH_ATTEMPTS=0
MAX_PUSH_ATTEMPTS=4
PUSH_SUCCESS=false

while [ $PUSH_ATTEMPTS -lt $MAX_PUSH_ATTEMPTS ]; do
  if git push -u origin "$BRANCH_NAME"; then
    PUSH_SUCCESS=true
    echo "  ✅ Pushed successfully!"
    break
  else
    PUSH_ATTEMPTS=$((PUSH_ATTEMPTS + 1))
    if [ $PUSH_ATTEMPTS -lt $MAX_PUSH_ATTEMPTS ]; then
      WAIT_TIME=$((2 ** PUSH_ATTEMPTS))
      echo "  ⚠️  Push failed, retrying in ${WAIT_TIME}s (attempt $((PUSH_ATTEMPTS + 1))/$MAX_PUSH_ATTEMPTS)..."
      sleep $WAIT_TIME
    fi
  fi
done

if [ "$PUSH_SUCCESS" = false ]; then
  echo "  ❌ Push failed after $MAX_PUSH_ATTEMPTS attempts"
  exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "View changes:"
echo "  https://github.com/${GITHUB_USER}/${REPO_NAME}/tree/$BRANCH_NAME"
echo ""
echo "Create PR:"
echo "  ~/.local/bin/gh pr create --repo ${GITHUB_USER}/${REPO_NAME} --base $DEFAULT_BRANCH --head $BRANCH_NAME --title 'feat: Add Claude Code Toolkit as submodule'"
echo ""
echo "Test locally:"
echo "  cd $REPO_DIR"
echo "  ./scripts/sync-claude-toolkit.sh"
