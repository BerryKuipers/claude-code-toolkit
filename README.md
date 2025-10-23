# Claude Code Toolkit

**Universal Claude Code configuration: agents, skills, workflows, and SessionStart hooks for consistent development across projects.**

---

## 🎯 Purpose

This repository serves as the **single source of truth** for Claude Code configuration across all your projects. Instead of duplicating agents, skills, and workflows in every repository, reference this central toolkit.

## 📦 What's Included

### `.claude/` - Core Configuration

**SessionStart Hooks:**
- Auto-install GitHub CLI in web sessions (no root required)
- Environment setup automation
- Configured in `.claude/settings.json`

**Agents (10+):**
- `architect` - Architecture review and validation
- `conductor` - Complete workflow orchestration
- `database` - Safe database operations
- `design` - UI/UX design and review
- `refactor` - Safe code refactoring with tests
- `security-pentest` - Security testing
- `orchestrator` - Task routing and coordination
- `implementation` - Feature implementation
- `researcher` - Research and web search
- `audit` - Comprehensive code audit

**Slash Commands:**
- `/issue-pickup` - Pick up and implement GitHub issues
- `/conductor` - Start orchestrator workflow
- `/refactor` - Safe refactoring with validation

**Skills:**
- Quality gates and validation
- Test execution and coverage
- Build validation

### `scripts/` - Automation Scripts

- `install-gh-cli.sh` - Auto-install GitHub CLI (SessionStart hook)
- `copy-claude-config-to-repos.sh` - Deploy to multiple repos
- `deploy-claude-config-to-github-repos.sh` - Automated GitHub deployment

### `docs/` - Documentation

- `CLAUDE_CODE_WEB_SETUP_GUIDE.md` - Complete setup guide
- `COPY_TO_NEW_REPO.md` - How to copy config to new repos
- `PROJECT_CUSTOMIZATION_CHECKLIST.md` - What to customize per project
- `CENTRAL_REPO_STRATEGY.md` - This repository's strategy

### `templates/` - Project Templates

- `CLAUDE.md.template` - Template for project-specific rules
- `config-override.yml.template` - Template for project customizations

---

## 🚀 Quick Start

### Option 1: Git Submodule (Recommended)

**Add to existing project:**

```bash
cd your-project

# Add toolkit as submodule
git submodule add https://github.com/BerryKuipers/claude-code-toolkit.git .claude-toolkit

# Symlink .claude directory
ln -s .claude-toolkit/.claude .claude

# Copy scripts
cp .claude-toolkit/scripts/install-gh-cli.sh scripts/
chmod +x scripts/install-gh-cli.sh

# Create project-specific config
mkdir -p .claude/local
cp .claude-toolkit/templates/CLAUDE.md.template CLAUDE.md
# Edit CLAUDE.md with your project details

# Commit
git add .gitmodules .claude-toolkit .claude scripts/ CLAUDE.md
git commit -m "feat: Add Claude Code toolkit"
git push
```

**Update toolkit in all projects:**

```bash
# In toolkit repo: make improvements
cd claude-code-toolkit
git commit -m "feat: Improve architect agent"
git push

# In your projects: pull updates
cd your-project
git submodule update --remote .claude-toolkit
git add .claude-toolkit
git commit -m "chore: Update Claude Code toolkit"
git push
```

### Option 2: Direct Copy (Simple but not synced)

```bash
cd your-project

# Clone toolkit
git clone https://github.com/BerryKuipers/claude-code-toolkit.git /tmp/toolkit

# Copy config
cp -r /tmp/toolkit/.claude .
cp -r /tmp/toolkit/scripts .
cp -r /tmp/toolkit/docs .

# Customize for your project
nano .claude/config.yml  # Update workspace directory
nano CLAUDE.md          # Create project rules

# Commit
git add .claude/ scripts/ docs/ CLAUDE.md
git commit -m "feat: Add Claude Code configuration"
git push
```

### Option 3: Template Repository

**Use as GitHub template:**

```bash
# Create new project from template
gh repo create my-new-project --template BerryKuipers/claude-code-toolkit

# Customize
cd my-new-project
nano .claude/config.yml  # Update project name
nano CLAUDE.md          # Add project rules

git commit -am "chore: Customize for this project"
git push
```

---

## 🔧 Customization

Each project has different requirements. Customize the toolkit for your project:

### Required Customizations

**1. Update `.claude/config.yml`:**

```yaml
# Line ~200: Update workspace directory
workspace:
  tempDir: "/tmp/YOUR-PROJECT-NAME-orchestrator"

# Lines ~154-159: Update GitHub labels
integrations:
  github:
    defaultLabels:
      - "automated"
      - "your-labels-here"
```

**2. Create `CLAUDE.md`:**

Use `templates/CLAUDE.md.template` as starting point.

**3. Review agent paths:**

Update `.claude/agents/*.md` if your project structure differs from:
- `src/components/` (UI components)
- `backend/` (backend code)
- `npm run build` (build command)
- `npm run test` (test command)

See `docs/PROJECT_CUSTOMIZATION_CHECKLIST.md` for complete list.

---

## 📖 Documentation

- **[Setup Guide](docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md)** - How SessionStart hooks work
- **[Customization](docs/PROJECT_CUSTOMIZATION_CHECKLIST.md)** - What to customize
- **[Copy Guide](docs/COPY_TO_NEW_REPO.md)** - Copy to new repositories
- **[Central Strategy](docs/CENTRAL_REPO_STRATEGY.md)** - Why this repo exists

---

## 🏗️ Project Structure

```
claude-code-toolkit/
├── .claude/                    # Core configuration
│   ├── settings.json          # SessionStart hooks
│   ├── config.yml             # Base configuration
│   ├── agents/                # Specialized agents
│   ├── commands/              # Slash commands
│   └── skills/                # Skills and workflows
├── scripts/                    # Automation scripts
│   ├── install-gh-cli.sh      # SessionStart hook script
│   └── deploy-*.sh            # Deployment scripts
├── docs/                       # Documentation
├── templates/                  # Project templates
│   ├── CLAUDE.md.template     # Project rules template
│   └── config-override.yml.template
└── README.md                   # This file
```

---

## 🎯 Use Cases

### For Web Sessions

✅ GitHub CLI auto-installs every session (no root!)
✅ Consistent agent experience across all projects
✅ SessionStart hooks run automatically
✅ Always up-to-date via submodule

### For Local Development

✅ Same agents in CLI and web
✅ Offline support (agents in local submodule)
✅ Version locking per project
✅ Easy testing of toolkit updates

### For Teams

✅ Shared agent definitions
✅ Consistent workflows across developers
✅ Centralized improvements
✅ Template for new projects

---

## 🔄 Workflow

**Update agents once, apply everywhere:**

```bash
# 1. Improve agent in toolkit
cd claude-code-toolkit
nano .claude/agents/architect.md  # Make it better
git commit -m "feat: Improve architect pattern detection"
git push

# 2. Projects using submodules auto-update on next session
# Or manually:
cd your-project
git submodule update --remote
```

**SessionStart hook keeps toolkit synced:**

```json
// .claude/settings.json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "git submodule update --init --remote .claude-toolkit"
      }
    ]
  }
}
```

---

## 🧪 Testing

Before deploying to all projects:

1. Test in one project first
2. Verify agents work with that project's structure
3. Update toolkit if needed
4. Deploy to remaining projects

---

## 🤝 Contributing

### Reporting Issues

Found a bug or have a suggestion?
- Open an issue with details
- Include which agent/skill
- Provide example project structure if relevant

### Adding Agents

1. Create agent in `.claude/agents/your-agent.md`
2. Follow existing agent structure
3. Make it project-agnostic (use variables for paths)
4. Document in agent file
5. Submit PR

### Improving Documentation

Documentation improvements welcome!
- Clarify confusing sections
- Add examples
- Fix typos

---

## 📝 License

MIT License - Use freely in your projects.

---

## 🙋 Support

**Questions?**
- Check `docs/` folder
- Review `templates/` for examples
- Open an issue

**Used By:**
- WescoBar-Universe-Storyteller
- TribeVibe
- home-sage
- + 17 more projects

---

**Made with Claude Code** 🤖
