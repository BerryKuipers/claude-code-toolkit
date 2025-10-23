# Claude Code Web Setup Guide

Complete guide for understanding and replicating the Claude Code configuration across repositories.

## Table of Contents
1. [SessionStart Hooks Overview](#sessionstart-hooks-overview)
2. [How Auto-Installation Works](#how-auto-installation-works)
3. [Claude Code Configuration Structure](#claude-code-configuration-structure)
4. [Copying to a New Repository](#copying-to-a-new-repository)
5. [Prerequisites & Domain Allowlist](#prerequisites--domain-allowlist)

---

## SessionStart Hooks Overview

**What are SessionStart Hooks?**
- Hooks that run automatically when a new Claude Code web session starts
- Defined in `.claude/settings.json`
- Execute shell scripts or commands before user interaction
- Perfect for environment setup, tool installation, validation checks

**Why Use Them?**
- **Web sessions are ephemeral** - No persistent installations between sessions
- **Automate setup** - gh CLI, linters, formatters install automatically
- **Consistent environment** - Every session starts with required tools
- **Save time** - No manual "install gh" every session

**How They Work:**
```
User opens Claude Code web session
         ↓
Claude Code reads .claude/settings.json
         ↓
Finds SessionStart hooks with matcher: "startup"
         ↓
Executes hook commands in order
         ↓
Session ready with all tools installed
```

---

## How Auto-Installation Works

### Current Setup: GitHub CLI Auto-Install

**Files Involved:**
- `.claude/settings.json` - Hook configuration
- `scripts/install-gh-cli.sh` - Installation script

**Flow:**

1. **Session Starts** → Claude Code reads `.claude/settings.json`:
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
             }
           ]
         }
       ]
     }
   }
   ```

2. **Script Executes** → `scripts/install-gh-cli.sh`:
   - ✅ Checks if `gh` already installed (skip if present)
   - ✅ Detects `CLAUDE_CODE_REMOTE=true` (only run in web sessions)
   - ✅ Fetches latest version from `api.github.com`
   - ✅ Downloads binary from `github.com/cli/cli/releases`
   - ✅ Installs to `~/.local/bin/gh` (no root required)
   - ✅ Adds `~/.local/bin` to PATH if needed
   - ✅ Verifies installation success

3. **Session Ready** → `gh` command available for PRs, issues, etc.

**Key Environment Variables:**
- `CLAUDE_CODE_REMOTE=true` - Indicates web session (not CLI)
- `CLAUDE_PROJECT_DIR` - Path to project root

**Domain Requirements:**
- `api.github.com` - Get latest version
- `github.com` - Download releases
- `release-assets.githubusercontent.com` - GitHub redirects here (needs allowlist!)

---

## Claude Code Configuration Structure

```
.claude/
├── settings.json           # SessionStart hooks (WEB ONLY)
├── config.yml              # General configuration (CLI + Web)
├── agents/                 # Custom agents
│   ├── architect.md
│   ├── conductor.md
│   ├── database.md
│   ├── design.md
│   ├── implementation.md
│   ├── orchestrator.md
│   └── ...
├── commands/               # Slash commands
│   ├── issue-pickup.md
│   ├── conductor.md
│   └── ...
├── skills/                 # Filesystem-based skills (CLI)
│   ├── quality/
│   ├── testing/
│   └── ...
└── api-skills-source/      # API-based skills (Anthropic Skills API)
    ├── upload-skills.py
    ├── quality-gate/
    └── ...

scripts/
└── install-gh-cli.sh       # SessionStart hook script
```

### File Purposes

#### `.claude/settings.json` (Web Sessions Only)
- **Purpose:** Define hooks for web sessions
- **Hooks Types:**
  - `SessionStart` - Run on session creation
  - `SessionEnd` - Run before session closes
  - `UserPromptSubmit` - Run before each user message
  - `ToolUse` - Run before tool execution

#### `.claude/config.yml` (CLI + Web)
- **Purpose:** General configuration, agent settings, integrations
- **Sections:**
  - `delegation` - Command delegation settings
  - `agents` - Agent system configuration
  - `orchestrator` - Workflow orchestration
  - `validation` - Quality gates
  - `integrations` - GitHub, Chrome DevTools, Loki, Seq

#### `.claude/agents/` (Custom Agents)
- **Purpose:** Define specialized agents with specific roles
- **Format:** Markdown files with instructions
- **Examples:**
  - `architect.md` - Architecture review and validation
  - `conductor.md` - Orchestrates complete workflows
  - `database.md` - Safe database operations
  - `design.md` - UI/UX design and review
  - `refactor.md` - Code refactoring with safety checks

**Agent Structure:**
```markdown
# Agent Name

## Role
Brief description of agent's purpose

## Capabilities
- What the agent can do
- Tools it has access to

## Usage
When and how to use this agent

## Instructions
Detailed step-by-step instructions for the agent
```

#### `.claude/commands/` (Slash Commands)
- **Purpose:** Define custom `/command` shortcuts
- **Format:** Markdown files that expand to prompts
- **Examples:**
  - `/issue-pickup` - Pick up GitHub issue and implement
  - `/conductor` - Start orchestrator workflow
  - `/refactor` - Safe refactoring with validation

#### `.claude/skills/` (Filesystem Skills - CLI)
- **Purpose:** Reusable skill modules (CLI only)
- **Format:** `SKILL.md` with frontmatter
- **Categories:**
  - `quality/` - Type checking, linting, coverage
  - `testing/` - Test execution, validation
  - `git-workflows/` - Git operations, PR creation

#### `.claude/api-skills-source/` (API Skills - Web)
- **Purpose:** Skills uploaded to Anthropic Skills API (works in web sessions)
- **Format:** Folder with `SKILL.md` and optional `skill.py`
- **Upload:** `python3 upload-skills.py` (requires `ANTHROPIC_SKILLS_API_KEY`)
- **Examples:**
  - `quality-gate/` - Comprehensive quality validation

---

## Copying to a New Repository

### Quick Copy Method

**Step 1: Copy Claude Configuration**
```bash
# From source repo (this one)
cd /path/to/WescoBar-Universe-Storyteller

# To target repo
TARGET_REPO="/path/to/new-repo"

# Copy entire .claude directory
cp -r .claude "$TARGET_REPO/"

# Copy startup scripts
cp -r scripts/install-gh-cli.sh "$TARGET_REPO/scripts/"
chmod +x "$TARGET_REPO/scripts/install-gh-cli.sh"
```

**Step 2: Customize for New Repo**

Edit `.claude/config.yml`:
```yaml
# Update workspace directory
workspace:
  tempDir: "/tmp/your-project-name-orchestrator"  # Change this

# Update integration settings if needed
integrations:
  github:
    enabled: true
    defaultLabels:
      - "automated"
      - "your-custom-label"  # Add project-specific labels
```

Edit agents in `.claude/agents/`:
- Update references to your project structure
- Modify file paths and patterns
- Customize validation rules

Edit `CLAUDE.md` (if present):
```markdown
# Your Project Name - AI Assistant Rules

**Tech Stack:**
- Your tech stack here

**Architectural Rules:**
- Your architectural patterns
```

**Step 3: Test in New Repo**

```bash
cd "$TARGET_REPO"

# Start Claude Code web session
# The SessionStart hook should run automatically

# Verify gh CLI installed
gh --version

# Test an agent
# Use Task tool with an agent like "architect" or "design"
```

### Detailed Customization Guide

#### What to Keep As-Is
✅ `.claude/settings.json` - Hook configuration works universally
✅ `scripts/install-gh-cli.sh` - Installation script is generic
✅ `.claude/config.yml` structure - Core settings are portable
✅ Agent patterns - The agent delegation system is universal

#### What to Customize

**1. Project-Specific Agents**

If your agents reference specific files/folders, update them:

```markdown
<!-- Before (WescoBar specific) -->
- Search in `src/components/` for React components
- Check `backend/DATABASE.md` for schema

<!-- After (Your project) -->
- Search in `packages/ui/` for React components
- Check `prisma/schema.prisma` for schema
```

**2. Slash Commands**

Update commands to match your workflow:

```markdown
<!-- .claude/commands/your-command.md -->
You are tasked with [your workflow].

For this project:
- Source code: [your paths]
- Tests: [your test paths]
- Build command: [your build command]
```

**3. Validation Rules**

Update validation thresholds in `.claude/config.yml`:

```yaml
validation:
  requireTestsBeforeRefactor: true
  requireBuildValidation: true
  requireCoverageThreshold: 80  # Adjust for your project
```

**4. Tech Stack References**

Update any tech-stack-specific settings:
- TypeScript config paths
- Test runners (Jest vs Vitest)
- Build tools (Vite vs Webpack)
- Database (PostgreSQL vs MongoDB)

#### Adding New Hooks

**Example: Auto-install multiple tools**

Edit `.claude/settings.json`:
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
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/setup-environment.sh"
          }
        ]
      }
    ]
  }
}
```

Create `scripts/setup-environment.sh`:
```bash
#!/bin/bash
set -e

echo "🔧 Setting up development environment..."

# Install project-specific tools
if [ "$CLAUDE_CODE_REMOTE" = "true" ]; then
  # Web session setup
  npm install -g your-cli-tool
  apt-get update && apt-get install -y your-system-tool
fi

echo "✅ Environment ready"
```

---

## Prerequisites & Domain Allowlist

### For Claude Code Web Sessions

**Required Proxy Allowlist Domains:**

```
# Already allowed (typical defaults)
github.com
api.github.com
raw.githubusercontent.com
*.github.io
npmjs.com
*.npmjs.org
registry.npmjs.org

# MUST ADD for gh CLI installation
release-assets.githubusercontent.com
# OR use wildcard
*.githubusercontent.com

# Optional but recommended
cli.github.com           # For apt/dnf package repos (alternative install method)
```

**How to Request Allowlist Addition:**

If you manage the proxy:
```
Add to allowed_hosts JWT claim:
"release-assets.githubusercontent.com,cli.github.com"
```

If you're a user:
- Contact your Claude Code administrator
- Request: "Add *.githubusercontent.com to proxy allowlist for release downloads"
- Reason: "Required for SessionStart hooks to auto-install GitHub CLI from releases"

### Testing Allowlist

Test if domains are accessible:
```bash
# Should return 200 OK
curl -I https://api.github.com/repos/cli/cli/releases/latest

# Should return 200 OK (after redirect)
curl -I https://github.com/cli/cli/releases/download/v2.82.1/gh_2.82.1_linux_amd64.tar.gz

# Should NOT return 403
curl -I https://release-assets.githubusercontent.com
```

---

## Example: New Session Prompt

Use this prompt when starting a fresh session in a repository with this setup:

```
Hi! This repository is configured with Claude Code SessionStart hooks for automatic environment setup.

On session start, the following should have happened automatically:
1. GitHub CLI (gh) installed via scripts/install-gh-cli.sh
2. Environment configured for development

Please verify:
- Run: gh --version
- Check: Custom agents available in .claude/agents/
- Test: Task tool with subagent_type="architect" or similar

If gh CLI is missing, the domain allowlist may need updating. Required domain:
- release-assets.githubusercontent.com (or *.githubusercontent.com)

Configuration overview:
- .claude/settings.json - SessionStart hooks
- .claude/agents/ - Custom specialized agents
- .claude/config.yml - Orchestration and validation rules
- scripts/install-gh-cli.sh - Auto-installation script

Ready to work! What would you like me to help with?
```

---

## Troubleshooting

### Hook Didn't Run

**Check:**
1. `.claude/settings.json` exists and has correct JSON syntax
2. Script path uses `$CLAUDE_PROJECT_DIR` variable
3. Script is executable: `chmod +x scripts/install-gh-cli.sh`
4. Check hook output in session logs (if available)

### Installation Failed

**Common Issues:**

**403 Forbidden:**
- Domain not in allowlist
- Add `release-assets.githubusercontent.com` to proxy allowlist

**Command not found:**
- Script not executable: `chmod +x scripts/install-gh-cli.sh`
- Wrong path in settings.json

**Timeout:**
- Increase timeout in settings.json (if supported)
- Check network connectivity

### Agents Not Working

**Check:**
1. `.claude/agents/` directory exists
2. Agent markdown files have correct format
3. Use Task tool with correct `subagent_type` parameter
4. Agent name matches filename (without .md)

---

## Summary

**What You've Learned:**
- ✅ SessionStart hooks automate web session setup
- ✅ `.claude/settings.json` defines hooks for web
- ✅ Scripts in `scripts/` handle installation
- ✅ `.claude/agents/` provides specialized AI agents
- ✅ Configuration is portable across repositories
- ✅ Domain allowlist critical for external downloads

**Quick Reference:**
```bash
# Copy configuration to new repo
cp -r .claude /path/to/new-repo/
cp scripts/install-gh-cli.sh /path/to/new-repo/scripts/

# Test in new session
gh --version

# Use an agent
# Task({ subagent_type: "architect", prompt: "Review architecture" })
```

**Next Steps:**
1. Merge PR #29 to enable SessionStart hooks
2. Verify domain allowlist includes `release-assets.githubusercontent.com`
3. Start new session and test auto-installation
4. Copy configuration to other repositories as needed

---

**Documentation References:**
- [Claude Code Hooks Reference](https://docs.claude.com/en/docs/claude-code/hooks)
- [Claude Code Agents](https://docs.claude.com/en/docs/claude-code/agents)
- [GitHub CLI Installation](https://github.com/cli/cli#installation)
