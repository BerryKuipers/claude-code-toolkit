# Agent Session Files - Quick Reference

**For all agents: Use `.claude/agent-sessions/` for temporary working files.**

## Quick Usage

```bash
# Create session files in the sessions directory
.claude/agent-sessions/notes-$(date +%Y%m%d-%H%M%S).md
.claude/agent-sessions/state-$(date +%Y%m%d-%H%M%S).json
.claude/agent-sessions/analysis-$(date +%Y%m%d).md
```

## What Goes Here

✅ **DO use for:**
- Working notes and scratchpads
- Agent state files
- Temporary analysis
- Session logs

❌ **DON'T use for:**
- Permanent documentation (use `.claude/docs/`)
- Agent definitions (use `.claude/agents/`)
- Command definitions (use `.claude/commands/`)

## Why

- Keeps repository clean
- Excluded from git automatically
- Easy to clean up after sessions
- No merge conflicts

**Full documentation:** `.claude/docs/agent-session-files.md`
