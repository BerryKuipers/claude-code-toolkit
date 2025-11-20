# Agent Session Files Guidelines

**Version:** 1.0
**Last Updated:** 2025-11-20

---

## Overview

Agents should use `.claude/agent-sessions/` for temporary working files created during sessions. This directory is excluded from git to keep the repository clean.

## Directory Purpose

**`.claude/agent-sessions/`** is for:
- Agent state files
- Session logs and notes
- Temporary analysis files
- Working drafts and scratchpads
- Any files that are session-specific and don't need to be committed

## Usage Guidelines

### ✅ DO: Use Session Directory

When creating temporary working files, use the session directory:

```bash
# Create session-specific files
echo "Analysis notes..." > .claude/agent-sessions/analysis-$(date +%Y%m%d-%H%M%S).md

# Create agent state files
echo "Current state..." > .claude/agent-sessions/agent-state-$(date +%Y%m%d-%H%M%S).json

# Create working notes
echo "Working notes..." > .claude/agent-sessions/notes-$(whoami)-$(date +%Y%m%d).md
```

### ❌ DON'T: Create Temporary Files in Main Directories

Don't create temporary files in:
- `.claude/agents/` (permanent agent definitions only)
- `.claude/commands/` (permanent command definitions only)
- `.claude/docs/` (permanent documentation only)
- Root directory (avoid clutter)
- `.claude/reviews/` (already gitignored, but prefer agent-sessions/)

### File Naming Convention

Use descriptive, timestamped names:

```
.claude/agent-sessions/
├── analysis-20251120-143022.md
├── conductor-state-20251120-143500.json
├── working-notes-berry-20251120.md
├── scratch-implementation-20251120.md
└── session-log-20251120-143022.txt
```

**Pattern:** `{purpose}-{identifier}-{timestamp}.{ext}`

## When to Use Session Directory

### Use for Temporary Files:
- ✅ Agent working notes during task execution
- ✅ Session state for resumption
- ✅ Temporary analysis files
- ✅ Scratchpads and drafts
- ✅ Debug logs
- ✅ Intermediate results

### Don't Use for Permanent Files:
- ❌ Agent definitions (use `.claude/agents/`)
- ❌ Command definitions (use `.claude/commands/`)
- ❌ Documentation (use `.claude/docs/`)
- ❌ Workflows (use `.claude/prompts/workflows/`)
- ❌ Shared configurations (use `.claude/shared/`)

## Cleanup

Session files can be safely deleted after:
- Session ends
- Task completes
- Agent finishes execution
- User manually cleans up

**Automatic cleanup is NOT implemented** - files persist until manually deleted.

## Git Exclusion

The following patterns are excluded from git (see `.gitignore`):

```gitignore
# Agent session directory
.claude/agent-sessions/*
!.claude/agent-sessions/.gitkeep

# Agent working files at root level (fallback)
*-agent-notes.md
*-session-*.md
*-working-*.md
*-scratch-*.md
```

## Examples

### Conductor Agent Working State

```bash
# Save conductor state during workflow
cat > .claude/agent-sessions/conductor-state-$(date +%Y%m%d-%H%M%S).json <<EOF
{
  "phase": 2,
  "issueNumber": 123,
  "branchName": "feature/issue-123-new-feature",
  "completedSteps": ["architecture", "implementation"]
}
EOF
```

### QA Triage Analysis Notes

```bash
# Save triage analysis
cat > .claude/agent-sessions/qa-triage-analysis-$(date +%Y%m%d-%H%M%S).md <<EOF
# QA Triage Analysis - $(date)

## Issues Found
- Login flow broken on mobile
- API timeout on /users endpoint

## Recommendations
- Fix mobile CSS
- Increase API timeout
EOF
```

### Implementation Agent Scratchpad

```bash
# Working notes during implementation
cat > .claude/agent-sessions/implementation-notes-$(date +%Y%m%d).md <<EOF
# Implementation Notes

## Current Task
Implementing character traits feature

## Progress
- [x] Created CharacterTraits component
- [ ] Add backend endpoint
- [ ] Write E2E tests
EOF
```

## Agent Integration

### For Agent Developers

When creating or updating agents, include guidance about using the session directory:

```markdown
## Session Files

During execution, save temporary files to `.claude/agent-sessions/`:

- Working notes: `.claude/agent-sessions/notes-$(date +%Y%m%d-%H%M%S).md`
- State files: `.claude/agent-sessions/state-$(date +%Y%m%d-%H%M%S).json`
- Analysis: `.claude/agent-sessions/analysis-$(date +%Y%m%d-%H%M%S).md`

These files are excluded from git and can be deleted after the session.
```

### For Users

Session files are created in `.claude/agent-sessions/` and are not tracked by git. You can safely:
- Delete them anytime
- Review them for debugging
- Keep them for reference
- Ignore them completely

## Benefits

1. **Clean Repository** - Temporary files don't clutter git history
2. **Easy Cleanup** - Single directory to clean up
3. **Clear Separation** - Temporary vs permanent files are obvious
4. **No Conflicts** - Session files won't cause merge conflicts
5. **Better Organization** - All session files in one place

## Migration

If you find temporary files in other directories:

```bash
# Find potential session files
find .claude -name "*-notes.md" -o -name "*-scratch-*.md" -o -name "*-working-*.md"

# Move them to session directory
mv .claude/agents/some-working-file.md .claude/agent-sessions/

# Or delete if no longer needed
rm .claude/agents/old-session-file.md
```

---

**Last Updated:** 2025-11-20
**Maintained By:** Claude Code Toolkit Team
