# Dev Memory System - Toolkit Context

This document outlines how the Claude Code Toolkit is currently structured and how the dev memory system will integrate with it.

## Current Toolkit Structure

### 1. Agents (`.claude/agents/`)

**Location:** `.claude/agents/*.md`

**Purpose:** Specialized agent definitions for delegating complex tasks

**Structure:**
- Each agent is a markdown file with frontmatter
- Example: `refactor.md`, `architect.md`, `database.md`
- Contains agent description, tools available, and behavior guidelines
- Total: 24 agents currently

**How they work:**
- Used via the `Task` tool with `subagent_type` parameter
- Each agent runs autonomously with specific tool access
- Agents defined in toolkit are synced to all target repos

### 2. Skills (`.claude/skills/`)

**Location:** `.claude/skills/<category>/<skill-name>/SKILL.md`

**Purpose:** Reusable, composable capabilities that can be invoked by agents or commands

**Structure:**
```
.claude/skills/
├── quality/
│   ├── validate-lint/SKILL.md
│   ├── quality-gate/SKILL.md
│   └── validate-build/SKILL.md
├── git-workflows/
│   ├── commit-with-validation/SKILL.md
│   └── create-pull-request/SKILL.md
├── memory/
│   └── project-memory/SKILL.md
└── ...
```

**Skill file format:**
```yaml
---
name: skill-name
description: Short description of what the skill does
---

# Skill Name

Detailed instructions for Claude on how to use this skill...
```

**Current categories:**
- `quality/` - Code quality, linting, build validation
- `git-workflows/` - Git operations (commit, PR creation, branching)
- `memory/` - Project memory using MCP
- `testing/` - Test execution
- `state-management/` - Workflow state persistence
- `security/` - Dependency audits
- `github-integration/` - GitHub API operations

**How they work:**
- Skills are invoked by name using the `Skill` tool
- Can be called from agents, commands, or directly by Claude
- Defined once in toolkit, available in all synced repos

### 3. Commands (`.claude/commands/`)

**Location:** `.claude/commands/<command-name>.md`

**Purpose:** User-facing slash commands that expand to prompts

**Structure:**
- Each command is a markdown file
- Invoked via `/command-name` in conversation
- Can delegate to agents or execute workflows
- Example: `/codex-triage`, `/fix-e2e-tests`, `/test-ui`

**Integration with agents:**
- Commands often use `Task` tool to delegate to specialized agents
- Hub-and-spoke architecture: commands delegate through `/orchestrator`

**Current count:** 48 commands

### 4. Hooks (`.claude/hooks/`)

**Location:** `.claude/hooks/*.sh`

**Purpose:** Shell scripts executed at specific tool lifecycle events

**Current hooks:**
```
.claude/hooks/
├── pre-tool-use.sh            # Before any tool execution
├── post-tool-use.sh           # After any tool execution
├── user-prompt-submit.sh      # When user submits a prompt
├── validate-code-quality.sh   # Code quality validation
└── ...
```

**How they work:**
- Configured in `.claude/settings.json` under `hooks` section
- Run automatically based on trigger events
- Can block operations (e.g., prevent commits if quality gates fail)
- Made executable during sync (`chmod +x`)

**Example configuration in settings.json:**
```json
{
  "hooks": {
    "PreToolUse": [".claude/hooks/pre-tool-use.sh"],
    "PostToolUse": [".claude/hooks/post-tool-use.sh"],
    "UserPromptSubmit": [".claude/hooks/user-prompt-submit.sh"]
  }
}
```

### 5. Config (`.claude/config.yml`)

**Location:** `.claude/config.yml`

**Purpose:** Centralized configuration for agents, commands, workflows

**Key sections:**
```yaml
delegation:
  useSlashCommandTool: true
  degradedFallback: true

agents:
  enabled: true
  autoRouting: true
  sessionLogging: true

commands:
  autoDiscovery: true
  excludePatterns: ["_*.md", "*.backup"]

orchestrator:
  maxParallelDelegations: 5
  delegationTimeoutMs: 300000

validation:
  requireTestsBeforeRefactor: true
  requireBuildValidation: true
  autoRevertOnFailure: true

workflows:
  uiTesting:
    requireDataSetup: true
    enforceSequence: true

safety:
  neverRestartServers: true
  confirmDestructive: true
```

**Preserved during sync:** Config files are NOT overwritten to preserve project-specific settings

### 6. Sync Mechanism

**Script:** `scripts/sync-claude-toolkit.sh`

**Purpose:** Sync toolkit configuration from `.claude-toolkit/` submodule to target repo's `.claude/`

**What it syncs:**
```bash
# Synced (overwritten each time)
agents/          → .claude/agents/
commands/        → .claude/commands/
hooks/           → .claude/hooks/
skills/          → .claude/skills/
prompts/         → .claude/prompts/
api-skills-source/ → .claude/api-skills-source/

# Preserved (NOT overwritten)
config.yml       → Project-specific configuration
settings.json    → Project-specific settings, hooks config
```

**Sync strategy:**
- Uses `rsync -a --delete` for complete sync
- Falls back to `cp -rf` if rsync unavailable (Windows compatibility)
- Makes hook scripts executable after sync
- Warns if hooks not configured in settings.json
- Idempotent: safe to run multiple times

**Trigger:**
- SessionStart hooks (`.claude/settings.json`)
- Manual execution: `./scripts/sync-claude-toolkit.sh`
- Runs automatically when Claude Code session starts (if configured)

**Submodule update:**
- Attempts `git submodule update --init --remote .claude-toolkit`
- Gracefully handles network failures and 403 errors
- Uses existing toolkit version if update fails

### 7. Settings & SessionStart Hooks

**File:** `.claude/settings.json`

**Purpose:** Configure Claude Code environment, permissions, hooks

**Example structure:**
```json
{
  "sessionStart": [
    "bash scripts/sync-claude-toolkit.sh"
  ],
  "hooks": {
    "PreToolUse": [".claude/hooks/pre-tool-use.sh"],
    "PostToolUse": [".claude/hooks/post-tool-use.sh"]
  },
  "env": {
    "CUSTOM_VAR": "value"
  }
}
```

**SessionStart hook:**
- Runs commands when Claude Code session starts
- Typically syncs toolkit: `bash scripts/sync-claude-toolkit.sh`
- Can install dependencies: `bash scripts/install-gh-cli.sh`

## Integration Points for Dev Memory

Based on this structure, the dev memory system will integrate as follows:

### 1. Memory Data Storage (per target repo)

**Location:** `<target-repo>/ai_memory/`

```
ai_memory/
├── events.jsonl          # Append-only event log
├── sessions.jsonl        # Session summaries
├── SESSION_BRIEFING.md   # Generated briefing
└── .gitkeep              # Ensure directory exists
```

**NOT synced from toolkit** - this is target repo data, not toolkit code

### 2. Dev Memory Skills

**Location:** `.claude/skills/memory/dev-memory/`

```
.claude/skills/memory/dev-memory/
├── update/SKILL.md        # dev_memory_update skill
└── briefing/SKILL.md      # dev_memory_briefing skill
```

**Synced via:** `scripts/sync-claude-toolkit.sh` (like other skills)

### 3. Dev Memory Hooks

**Location:** `.claude/hooks/post-commit-memory.sh`

**Purpose:** Automatically call dev_memory_update after each commit

**Triggered by:** PostToolUse hook when Bash tool runs `git commit`

**Configuration in settings.json:**
```json
{
  "hooks": {
    "PostToolUse": [
      ".claude/hooks/post-tool-use.sh",
      ".claude/hooks/post-commit-memory.sh"
    ]
  }
}
```

**Synced via:** `scripts/sync-claude-toolkit.sh` (like other hooks)

### 4. Sync Integration

**Add to sync script:**
```bash
# After syncing skills
echo "  → Ensuring ai_memory skeleton exists..."
mkdir -p "$PROJECT_DIR/ai_memory"
if [ ! -f "$PROJECT_DIR/ai_memory/.gitkeep" ]; then
  echo "# AI Memory Storage" > "$PROJECT_DIR/ai_memory/.gitkeep"
fi
```

**Idempotent:** Running sync multiple times won't duplicate or break anything

### 5. Config Integration

**Optional config.yml section:**
```yaml
devMemory:
  enabled: true
  autoUpdateOnCommit: true
  maxEventsPerCommit: 3
  sessionBriefingOnStart: false
```

**Project-specific:** Projects can disable/customize behavior

## Reusable Patterns from Existing Skills

### From `commit-with-validation` skill:
- Parsing commit metadata (hash, message, timestamp, branch)
- Extracting issue numbers from commit messages
- Running post-commit logic safely
- Handling git authorship checks

### From `project-memory` skill:
- Storing structured context with tags
- Recalling context based on queries
- Categorizing memories (architecture, patterns, fixes, etc.)
- Integration with MCP tools

### From quality skills:
- Running validation checks without blocking workflow
- Returning structured output (JSON format)
- Graceful failure handling
- Integration with hooks

## Design Principles for Dev Memory

Based on toolkit patterns:

1. **Idempotent sync:** Running sync multiple times must be safe
2. **Opt-in by config:** Projects can disable via config.yml
3. **Non-blocking:** Memory updates shouldn't fail commits
4. **Append-only:** JSONL files are never rewritten, only appended
5. **Self-contained:** Skills work without external dependencies (beyond git)
6. **Cross-platform:** Must work on Linux, Mac, Windows (Git Bash)
7. **Framework-agnostic:** Works for any project type
8. **Graceful degradation:** If memory update fails, log warning but continue

## Next Steps

1. Design JSONL data formats (events.jsonl, sessions.jsonl)
2. Implement dev_memory_update skill
3. Implement dev_memory_briefing skill
4. Create post-commit hook
5. Integrate with sync mechanism
6. Add config defaults
7. Test idempotency
8. Document usage
