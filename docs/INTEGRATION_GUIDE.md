# Claude Code Toolkit Integration Guide

This guide explains how the different components of the Claude Code Toolkit work together and how to integrate them into your projects.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Claude Code Toolkit                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  Hook System    │    │ Memory System   │    │ Harness System  │         │
│  │  (Automation)   │    │ (Dev Context)   │    │ (Feature Work)  │         │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘         │
│           │                      │                      │                  │
│           └──────────────────────┼──────────────────────┘                  │
│                                  │                                          │
│  ┌───────────────────────────────┴───────────────────────────────┐         │
│  │                      Sync Script                               │         │
│  │              (scripts/sync-claude-toolkit.sh)                  │         │
│  └───────────────────────────────────────────────────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Relationships

### 1. Hook System

**Purpose:** Automate recurring tasks and enforce quality gates.

**Files:**
- `templates/settings-with-hooks.json` - Hook configuration template
- `.claude/hooks/*.sh` - Hook scripts

**Integration Points:**
- SessionStart hooks trigger sync and memory processing
- PostToolUse hooks track commits for memory
- PreToolUse hooks validate code quality

### 2. Memory System

**Purpose:** Track development context across sessions.

**Files:**
- `.claude/hooks/post-commit-memory.sh` - Records commits
- `.claude/hooks/process-pending-memory.sh` - Processes pending updates
- `ai_memory/events.jsonl` - Event storage
- `ai_memory/.pending_updates` - Pending commits queue

**Integration Points:**
- Husky `post-commit` writes to `.pending_updates`
- SessionStart/Stop hooks process pending updates
- Skills generate briefings from events

### 3. Harness System

**Purpose:** Enable structured, feature-driven development sessions.

**Files:**
- `templates/harness/feature_list.json` - Feature tracking
- `templates/harness/claude-progress.txt` - Progress log
- `templates/harness/app_spec.txt` - Project context
- `templates/harness/*-session-*.sh` - Session hooks

**Integration Points:**
- SessionStart hooks update progress on session start
- Stop hooks save progress on session end
- Feature list drives todo items and work focus

## Data Flow Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Git Commit  │────▶│ Husky Hook   │────▶│.pending_     │
│              │     │ post-commit  │     │ updates      │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                      ┌──────────────────────────┘
                      │
                      ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Session      │────▶│ process-     │────▶│ events.jsonl │
│ Start/Stop   │     │ pending-     │     │              │
│              │     │ memory.sh    │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                      ┌──────────────────────────┘
                      │
                      ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ User Request │────▶│ briefing     │────▶│SESSION_      │
│ "briefing"   │     │ skill        │     │BRIEFING.md   │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Setup Sequence

### Initial Setup

1. **Add toolkit as submodule:**
   ```bash
   git submodule add https://github.com/YourOrg/claude-code-toolkit .claude-toolkit
   ```

2. **Run initial sync:**
   ```bash
   bash .claude-toolkit/scripts/sync-claude-toolkit.sh
   ```

3. **Configure settings.json:**
   ```bash
   # Option A: Use template
   cp .claude-toolkit/templates/settings-with-hooks.json .claude/settings.json

   # Option B: Merge into existing settings
   # Edit .claude/settings.json manually
   ```

4. **Setup Husky (for git hooks):**
   ```bash
   npx husky init
   cp .claude-toolkit/templates/husky/post-commit .husky/
   chmod +x .husky/post-commit
   ```

5. **Initialize harness (optional):**
   ```bash
   bash .claude-toolkit/templates/harness/init.sh
   ```

### Session Lifecycle

```
SessionStart
    │
    ├── git submodule update (toolkit sync)
    ├── sync-claude-toolkit.sh (sync files)
    ├── process-pending-memory.sh (memory)
    └── harness-session-start.sh (harness - if enabled)

During Session
    │
    ├── PreToolUse hooks (validation)
    ├── PostToolUse hooks (tracking)
    └── UserPromptSubmit hooks (routing)

Stop
    │
    ├── harness-session-stop.sh (harness - if enabled)
    └── process-pending-memory.sh (memory)
```

## Configuration Files

### settings.json

The central configuration for Claude Code hooks:

```json
{
  "hooks": {
    "SessionStart": [
      {"matcher": "startup", "hooks": [
        {"type": "command", "command": "bash -c \"...sync script...\""},
        {"type": "command", "command": "bash -c \"...memory processing...\""}
      ]}
    ],
    "Stop": [...],
    "PreToolUse": [...],
    "PostToolUse": [...]
  }
}
```

### config.yml

Project-specific configuration:

```yaml
devMemory:
  enabled: true
  autoUpdateOnCommit: true

harness:
  enabled: false  # Enable when using feature-driven development
```

## Windows Compatibility

All hooks use the `bash -c "..."` wrapper pattern for Windows compatibility:

```json
{
  "type": "command",
  "command": "bash -c \"test -f script.sh && bash script.sh\""
}
```

**Key patterns:**
- Always wrap in `bash -c "..."`
- Use `test -f ... && ...` instead of `|| true`
- Avoid `2>/dev/null || true` (use `2>nul` for error suppression if needed)

## Troubleshooting

### Hooks not running

1. Check settings.json syntax:
   ```bash
   cat .claude/settings.json | jq .
   ```

2. Verify hook scripts exist and are executable:
   ```bash
   ls -la .claude/hooks/*.sh
   ```

3. Check Claude Code hook output in session logs

### Memory not updating

1. Check `.pending_updates` file:
   ```bash
   cat ai_memory/.pending_updates
   ```

2. Manually run processing:
   ```bash
   bash .claude/hooks/process-pending-memory.sh
   ```

3. Check events.jsonl:
   ```bash
   tail ai_memory/events.jsonl
   ```

### Harness not tracking

1. Verify harness is initialized:
   ```bash
   ls .claude/harness/
   ```

2. Check feature_list.json is valid JSON:
   ```bash
   jq . .claude/harness/feature_list.json
   ```

## File Reference

| File | Purpose |
|------|---------|
| `settings.json` | Hook configuration |
| `config.yml` | Project settings |
| `hooks/process-pending-memory.sh` | Process commit queue |
| `hooks/post-commit-memory.sh` | Record commits |
| `harness/feature_list.json` | Feature tracking |
| `harness/claude-progress.txt` | Session progress |
| `ai_memory/events.jsonl` | Event history |

## Related Documentation

- [Memory System](./dev_memory/README.md)
- [Autonomous Harness](./AUTONOMOUS_CODING_HARNESS.md)
- [Settings Examples](./settings-examples/)
- [Code Quality Enforcement](./CODE_QUALITY_ENFORCEMENT.md)
