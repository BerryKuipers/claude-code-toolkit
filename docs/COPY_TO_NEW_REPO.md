# Quick Guide: Copy Claude Code Configuration to New Repository

## 1-Minute Setup

```bash
# In WescoBar repo
SOURCE_REPO="/home/user/WescoBar-Universe-Storyteller"
TARGET_REPO="/path/to/your-new-repo"

# 1. Copy SessionStart hooks (SAFE - won't overwrite project files)
mkdir -p "$TARGET_REPO/.claude"
mkdir -p "$TARGET_REPO/scripts"
cp "$SOURCE_REPO/.claude/settings.json" "$TARGET_REPO/.claude/"
cp "$SOURCE_REPO/scripts/install-gh-cli.sh" "$TARGET_REPO/scripts/"
chmod +x "$TARGET_REPO/scripts/install-gh-cli.sh"

# 2. Copy agents and skills (SAFE - universal, not project-specific)
cp "$SOURCE_REPO/.claude/config.yml" "$TARGET_REPO/.claude/"
cp -r "$SOURCE_REPO/.claude/agents" "$TARGET_REPO/.claude/"
cp -r "$SOURCE_REPO/.claude/commands" "$TARGET_REPO/.claude/"

# 3. Optional: Copy skills if you want them
# cp -r "$SOURCE_REPO/.claude/skills" "$TARGET_REPO/.claude/"  # CLI skills
# cp -r "$SOURCE_REPO/.claude/api-skills-source" "$TARGET_REPO/.claude/"  # API skills

# 4. Copy reference documentation (SAFE - goes to docs/ folder)
mkdir -p "$TARGET_REPO/docs"
cp "$SOURCE_REPO/docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md" "$TARGET_REPO/docs/"
cp "$SOURCE_REPO/docs/COPY_TO_NEW_REPO.md" "$TARGET_REPO/docs/"

# ⚠️ DON'T copy CLAUDE.md or README.md - those are project-specific!
# Create your own project rules file if needed
```

## What You Get

### Automatic in Web Sessions
- ✅ GitHub CLI auto-installs on session start
- ✅ Ready to create PRs, manage issues

### Available Agents
- `architect` - Architecture review and validation
- `conductor` - Complete workflow orchestration
- `database` - Safe database operations
- `design` - UI/UX design and review
- `implementation` - Feature implementation
- `orchestrator` - Task routing and coordination
- `refactor` - Safe code refactoring
- `researcher` - Research and web search
- `security-pentest` - Security testing
- `audit` - Comprehensive code audit

### Slash Commands
- `/issue-pickup` - Pick up and implement GitHub issue
- `/conductor` - Start orchestrator workflow
- `/architect` - Architecture review
- `/refactor` - Safe refactoring with validation

## Customize for Your Project

### Update `.claude/config.yml`

```yaml
# Line 200: Change workspace directory
workspace:
  tempDir: "/tmp/YOUR-PROJECT-NAME-orchestrator"

# Lines 154-159: Update GitHub labels
integrations:
  github:
    enabled: true
    defaultLabels:
      - "automated"
      - "your-label"  # Add your labels
```

### Create Your Own `CLAUDE.md` (Optional, Project-Specific)

**Don't copy the WescoBar CLAUDE.md** - create your own with your project rules!

This file is optional but helpful for defining:
- Project name and overview
- Tech stack
- Architectural patterns
- File/folder structure
- Build commands
- Any project-specific rules for AI assistants

Example:
```markdown
# Your Project Name - AI Assistant Rules

## 🎬 Project Overview
[Your project description]

**Tech Stack:**
- Frontend: [Your frontend stack]
- Backend: [Your backend stack]
- Database: [Your database]

## 🏗️ Architectural Rules
[Your architecture patterns]

## 📋 Common Commands
npm run dev    # Start development
npm run build  # Build for production
```

### Update Agent Instructions (Optional)

If your project structure differs:

```bash
# Edit agents that reference specific paths
nano "$TARGET_REPO/.claude/agents/architect.md"
nano "$TARGET_REPO/.claude/agents/design.md"
```

Replace references like:
- `src/components/` → Your component path
- `backend/` → Your backend path
- `package.json` → Your build files

## Test in New Repo

```bash
cd "$TARGET_REPO"

# Commit the configuration
git add .claude/ scripts/ CLAUDE.md
git commit -m "feat: Add Claude Code configuration with SessionStart hooks"
git push

# Start Claude Code web session
# Hook should auto-install gh CLI

# Verify
gh --version

# Test agent
# Use Task tool with subagent_type="architect"
```

## Prerequisites

### Domain Allowlist Required

Your Claude Code web environment needs these domains allowlisted:

```
github.com                          ✅ Usually already allowed
api.github.com                      ✅ Usually already allowed
raw.githubusercontent.com           ✅ Usually already allowed
release-assets.githubusercontent.com ⚠️  MUST ADD (for gh CLI downloads)
```

**Quick Test:**
```bash
curl -I https://release-assets.githubusercontent.com
# Should return 200 OK, not 403
```

**If 403 Forbidden:**
- Contact Claude Code administrator
- Request: "Add *.githubusercontent.com to proxy allowlist"

## Minimal Setup (No Agents)

If you only want SessionStart hooks without agents:

```bash
# Copy only hooks and scripts
cp "$SOURCE_REPO/.claude/settings.json" "$TARGET_REPO/.claude/"
cp "$SOURCE_REPO/scripts/install-gh-cli.sh" "$TARGET_REPO/scripts/"
chmod +x "$TARGET_REPO/scripts/install-gh-cli.sh"
```

This gives you auto-installing gh CLI without the full agent system.

## Add More Startup Tools

Edit `.claude/settings.json` to add more tools:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/install-gh-cli.sh"
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-node-tools.sh"
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/configure-git.sh"
          }
        ]
      }
    ]
  }
}
```

Create additional scripts:

**`scripts/setup-node-tools.sh`:**
```bash
#!/bin/bash
echo "📦 Installing Node.js tools..."
npm install -g typescript eslint prettier
echo "✅ Node tools ready"
```

**`scripts/configure-git.sh`:**
```bash
#!/bin/bash
echo "⚙️  Configuring git..."
git config --global init.defaultBranch main
git config --global pull.rebase false
echo "✅ Git configured"
```

## Files Reference

```
.claude/
├── settings.json           ⭐ SessionStart hooks (REQUIRED)
├── config.yml              📋 General config (customize)
├── agents/                 🤖 Custom agents (optional)
├── commands/               💬 Slash commands (optional)
└── skills/                 🛠️  Skills (optional)

scripts/
└── install-gh-cli.sh       ⭐ Auto-install script (REQUIRED)

CLAUDE.md                   📖 Project rules (customize)
docs/
├── CLAUDE_CODE_WEB_SETUP_GUIDE.md    📚 Full documentation
├── NEW_SESSION_PROMPT_WEB_HOOKS.txt  🚀 Session prompt
└── COPY_TO_NEW_REPO.md               📋 This file
```

⭐ = Required for basic SessionStart hooks
📋 = Customize for your project
🤖 = Optional (agents system)

## Troubleshooting

### Hook Not Running

```bash
# Check settings file
cat .claude/settings.json

# Verify script exists and is executable
ls -la scripts/install-gh-cli.sh
chmod +x scripts/install-gh-cli.sh

# Test manually
"$CLAUDE_PROJECT_DIR"/scripts/install-gh-cli.sh
```

### gh CLI Installation Fails

```bash
# Check environment
echo $CLAUDE_CODE_REMOTE  # Should be "true" in web sessions

# Check domain access
curl -I https://api.github.com
curl -I https://github.com

# If 403: Domain not allowlisted
# Solution: Add release-assets.githubusercontent.com to allowlist
```

### Agents Not Found

```bash
# Verify agents directory
ls .claude/agents/

# Use correct format in Task tool
# Task({ subagent_type: "architect", prompt: "..." })
```

## Complete Example

```bash
#!/bin/bash
# Complete setup script for new repository

SOURCE="/home/user/WescoBar-Universe-Storyteller"
TARGET="/home/user/my-new-project"

echo "📦 Copying Claude Code configuration..."

# Core files (required)
cp -r "$SOURCE/.claude" "$TARGET/"
mkdir -p "$TARGET/scripts"
cp "$SOURCE/scripts/install-gh-cli.sh" "$TARGET/scripts/"
chmod +x "$TARGET/scripts/install-gh-cli.sh"

# Documentation (optional)
mkdir -p "$TARGET/docs"
cp "$SOURCE/docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md" "$TARGET/docs/"
cp "$SOURCE/docs/NEW_SESSION_PROMPT_WEB_HOOKS.txt" "$TARGET/docs/"
cp "$SOURCE/CLAUDE.md" "$TARGET/"

echo "✅ Configuration copied!"
echo ""
echo "Next steps:"
echo "1. Edit $TARGET/.claude/config.yml (update project name)"
echo "2. Edit $TARGET/CLAUDE.md (update project details)"
echo "3. Commit and push"
echo "4. Start new Claude Code session"
echo "5. Verify: gh --version"
```

Save as `copy-claude-config.sh`, make executable, run:

```bash
chmod +x copy-claude-config.sh
./copy-claude-config.sh
```

---

**That's it!** Your new repository now has SessionStart hooks and the full Claude Code agent system.

For detailed explanations, see: `docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md`
