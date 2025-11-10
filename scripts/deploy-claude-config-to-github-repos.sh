#!/bin/bash
# Deploy Claude Code configuration to multiple GitHub repositories
# Creates branches, commits, pushes, and optionally creates PRs
# Usage: ./scripts/deploy-claude-config-to-github-repos.sh

set -e

WESCOBAR_DIR="/home/user/WescoBar-Universe-Storyteller"
WORK_DIR="/tmp/claude-config-deployment"
GITHUB_USER="BerryKuipers"
BRANCH_PREFIX="claude/add-sessionstart-hooks"

# Define target repositories (GitHub repo names)
# Organized by priority
REPOS=(
  # 🔥 HIGH PRIORITY
  "TribeVibe"
  "home-sage"
  "TuneScout"
  "SceneSpeak"
  "quantfolio"

  # 🟡 MEDIUM PRIORITY
  "AgenticDevelopment"
  "TetherKey"
  "mcp-servers"
  "mcp-qdrant"

  # 🟢 ACTIVE PROJECTS
  "GreenSphere-"
  "oraculum"
  "audiotagger_2025"
  "MixItUp"

  # 🔵 ADDITIONAL
  "PinballDreaming"
  "GenZeditAi"
  "crypto-insight"
  "json-event-editor"
  "nas-playlist-generator"
  "GreenHomeAI"
  "crypto_ui"
)

# Configuration
CREATE_PRS=true      # Set to false to just push branches without creating PRs
CLEANUP_AFTER=true   # Set to false to keep cloned repos for inspection

echo "🚀 Deploying Claude Code configuration to GitHub repositories..."
echo "Source: $WESCOBAR_DIR"
echo "Work directory: $WORK_DIR"
echo "GitHub user: $GITHUB_USER"
echo ""

# Create work directory
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Process each repository
SUCCESS_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0

for REPO_NAME in "${REPOS[@]}"; do
  echo "---"
  echo "📦 Processing: $REPO_NAME"

  REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
  REPO_DIR="$WORK_DIR/$REPO_NAME"
  BRANCH_NAME="${BRANCH_PREFIX}-$(date +%Y%m%d)"

  # Clone or update repository
  if [ -d "$REPO_DIR" ]; then
    echo "  → Repository already cloned, updating..."
    cd "$REPO_DIR"
    git fetch origin
  else
    echo "  → Cloning via gh CLI..."
    if ! ~/.local/bin/gh repo clone "$GITHUB_USER/$REPO_NAME" "$REPO_DIR" 2>/dev/null; then
      echo "  ❌ Failed to clone (repo may not exist or not accessible)"
      SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
      continue
    fi
    cd "$REPO_DIR"
  fi

  # Get default branch name
  DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
  echo "  → Default branch: $DEFAULT_BRANCH"

  # Configure git to use gh CLI for auth
  git config credential.helper ""
  git config --local credential.helper '!~/.local/bin/gh auth git-credential'

  # Checkout default branch
  git checkout "$DEFAULT_BRANCH"
  git pull origin "$DEFAULT_BRANCH"

  # Check if branch already exists
  if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "  ⚠️  Branch $BRANCH_NAME already exists, using it"
    git checkout "$BRANCH_NAME"
  else
    echo "  → Creating branch: $BRANCH_NAME"
    git checkout -b "$BRANCH_NAME"
  fi

  # Create directories
  echo "  → Creating directories..."
  mkdir -p .claude scripts docs

  # Copy configuration files
  echo "  → Copying SessionStart hooks..."
  cp "$WESCOBAR_DIR/.claude/settings.json" .claude/

  echo "  → Copying gh CLI installer..."
  cp "$WESCOBAR_DIR/scripts/install-gh-cli.sh" scripts/
  chmod +x scripts/install-gh-cli.sh

  echo "  → Copying agents and commands..."
  cp "$WESCOBAR_DIR/.claude/config.yml" .claude/
  cp -r "$WESCOBAR_DIR/.claude/agents" .claude/
  cp -r "$WESCOBAR_DIR/.claude/commands" .claude/

  echo "  → Copying documentation..."
  cp "$WESCOBAR_DIR/docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md" docs/
  cp "$WESCOBAR_DIR/docs/COPY_TO_NEW_REPO.md" docs/
  cp "$WESCOBAR_DIR/docs/PROJECT_CUSTOMIZATION_CHECKLIST.md" docs/

  # Customize config.yml
  echo "  → Customizing config.yml..."
  if [ -f ".claude/config.yml" ]; then
    sed -i "s|tempDir: \"/tmp/.*-orchestrator\"|tempDir: \"/tmp/${REPO_NAME}-orchestrator\"|" .claude/config.yml
  fi

  # Check if there are changes
  if git diff --quiet && git diff --cached --quiet; then
    echo "  ℹ️  No changes detected (config already present?)"
    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
    continue
  fi

  # Stage changes
  echo "  → Staging changes..."
  git add .claude/ scripts/ docs/

  # Commit
  echo "  → Committing..."
  git commit -m "$(cat <<'EOF'
feat: Add Claude Code SessionStart hooks and agent system

Adds comprehensive Claude Code configuration for web sessions:

Configuration Files:
- .claude/settings.json - SessionStart hooks for auto-setup
- .claude/config.yml - Orchestration and validation rules
- .claude/agents/ - Specialized agents (architect, conductor, database, etc.)
- .claude/commands/ - Slash commands for workflows

Scripts:
- scripts/install-gh-cli.sh - Auto-install GitHub CLI in web sessions

Documentation:
- docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md - Complete setup guide
- docs/COPY_TO_NEW_REPO.md - Quick reference for copying config

Features:
✅ GitHub CLI auto-installs on session start (no root required)
✅ 10+ specialized agents for development workflows
✅ Orchestrator for complete feature cycles
✅ Safe refactoring with validation gates
✅ Architecture review and design agents

Ready to use in Claude Code web sessions!

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

  # Push to GitHub
  echo "  → Pushing to GitHub..."
  if git push -u origin "$BRANCH_NAME" 2>&1 | tee /tmp/git-push-output.txt; then
    echo "  ✅ Pushed successfully!"

    # Create PR if enabled
    if [ "$CREATE_PRS" = true ]; then
      echo "  → Creating pull request..."
      PR_BODY="## Add Claude Code Configuration

This PR adds comprehensive Claude Code configuration for web sessions.

### What's Included:

**SessionStart Hooks:**
- Auto-installs GitHub CLI on every session start
- No root access required (installs to ~/.local/bin)

**Agents (10+):**
- \`architect\` - Architecture review and validation
- \`conductor\` - Complete workflow orchestration
- \`database\` - Safe database operations
- \`design\` - UI/UX design and review
- \`refactor\` - Safe code refactoring
- \`security-pentest\` - Security testing
- And more...

**Slash Commands:**
- \`/issue-pickup\` - Pick up and implement GitHub issues
- \`/conductor\` - Start orchestrator workflow
- \`/refactor\` - Safe refactoring with tests

**Documentation:**
- Complete setup guide
- Troubleshooting instructions
- How to customize for this project

### Benefits:

✅ Consistent development environment across sessions
✅ Automated tool installation (gh CLI)
✅ Specialized agents for complex tasks
✅ Quality gates and validation
✅ Works in both CLI and web sessions

### ⚠️ IMPORTANT: Customization Required

**Before merging, review: \`docs/PROJECT_CUSTOMIZATION_CHECKLIST.md\`**

This configuration was copied from WescoBar-Universe-Storyteller and contains:
- ✅ Universal settings (SessionStart hooks, agent system, gh CLI installer)
- ⚠️ Project-specific paths and tech stack references that need updating

**Required Changes:**
1. [ ] Update \`.claude/config.yml\` workspace directory (line ~200)
2. [ ] Update GitHub labels in \`.claude/config.yml\` (lines ~154-159)
3. [ ] Review agent file paths in \`.claude/agents/*.md\`
4. [ ] Update build/test commands if they differ
5. [ ] Create custom \`CLAUDE.md\` with your project rules (optional)

**Quick Check:**
- Does your project use React? (agents assume React)
- Build command: \`npm run build\`? (agents assume npm)
- Components in \`src/components/\`? (agents assume this path)

If any differ, see checklist for details.

### Documentation

- 📋 **\`docs/PROJECT_CUSTOMIZATION_CHECKLIST.md\`** - What to customize
- 📖 **\`docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md\`** - How it all works
- 📚 **\`docs/COPY_TO_NEW_REPO.md\`** - Copy guide for other repos

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

      if ~/.local/bin/gh pr create \
        --repo "$GITHUB_USER/$REPO_NAME" \
        --title "feat: Add Claude Code SessionStart hooks and agent system" \
        --body "$PR_BODY" \
        --head "$BRANCH_NAME" \
        --base "$DEFAULT_BRANCH" 2>&1; then
        echo "  ✅ Pull request created!"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
      else
        echo "  ⚠️  PR creation failed, but branch is pushed"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
      fi
    else
      echo "  ✅ Branch pushed (PR creation disabled)"
      SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    fi
  else
    echo "  ❌ Push failed"
    FAILED_COUNT=$((FAILED_COUNT + 1))
  fi

  echo ""
done

# Cleanup
if [ "$CLEANUP_AFTER" = true ]; then
  echo "🧹 Cleaning up work directory..."
  cd /tmp
  rm -rf "$WORK_DIR"
fi

# Summary
echo "---"
echo "📊 Deployment Summary:"
echo "  ✅ Successful: $SUCCESS_COUNT"
echo "  ❌ Failed: $FAILED_COUNT"
echo "  ⏭️  Skipped: $SKIPPED_COUNT"
echo "  📦 Total: ${#REPOS[@]}"
echo ""

if [ $SUCCESS_COUNT -gt 0 ]; then
  echo "🎉 Successfully deployed to $SUCCESS_COUNT repositories!"
  echo ""
  echo "View pull requests:"
  echo "  ~/.local/bin/gh pr list --repo $GITHUB_USER/<repo-name>"
  echo ""
fi

if [ $FAILED_COUNT -gt 0 ]; then
  echo "⚠️  Some deployments failed. Check output above for details."
fi

echo "Done!"
