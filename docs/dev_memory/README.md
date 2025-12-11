# Developer Memory System

Automatic development event tracking and session briefing system for Claude Code projects.

## Overview

The Dev Memory System automatically tracks your development activities (commits, features, bugs, refactorings) in a lightweight, append-only JSONL format. It provides:

- **Automatic event extraction** from git commits
- **Timeline view** of project evolution
- **Session briefings** for context when starting work
- **Open questions tracking** for unresolved decisions
- **Next steps** automatically extracted from TODOs

## Quick Start

### For Projects Using the Toolkit

1. **Sync the toolkit** (happens automatically on SessionStart):
   ```bash
   bash scripts/sync-claude-toolkit.sh
   ```

2. **Make commits** as usual:
   ```bash
   git add .
   git commit -m "feat: Add user authentication

   Implemented JWT-based auth with httpOnly cookies.
   Supports 2FA for admin users.

   Fixes #123

   TODO: Add rate limiting for login attempts
   "
   ```

3. **Memory is updated automatically** via post-commit hook

4. **Generate a briefing** at session start:
   ```
   Ask Claude: "Generate a session briefing from dev memory"
   ```

### What Gets Created

After sync, each project will have:

```
your-project/
├── ai_memory/
│   ├── .gitkeep           # Created by sync
│   ├── events.jsonl       # Created on first commit
│   ├── sessions.jsonl     # Created on first commit
│   └── SESSION_BRIEFING.md # Created on demand
├── .claude/
│   ├── hooks/
│   │   └── post-commit-memory.sh  # Synced from toolkit
│   └── skills/
│       └── memory/
│           └── dev-memory/
│               ├── update/SKILL.md
│               └── briefing/SKILL.md
```

## Architecture

### Components

1. **Skills** (`.claude/skills/memory/dev-memory/`)
   - `update/SKILL.md` - Extract events from commits
   - `briefing/SKILL.md` - Generate session briefings

2. **Hooks** (`.claude/hooks/`)
   - `post-commit-memory.sh` - Called by husky, writes to `.pending_updates`
   - `process-pending-memory.sh` - Processes pending updates into `events.jsonl`

3. **Data Storage** (`ai_memory/`)
   - `events.jsonl` - One event per line
   - `sessions.jsonl` - Session summaries
   - `SESSION_BRIEFING.md` - Latest briefing

4. **Sync Integration** (`scripts/sync-claude-toolkit.sh`)
   - Creates `ai_memory/` directory
   - Syncs skills and hooks
   - Idempotent and safe

### Data Flow

```
git commit (outside Claude session)
    ↓
husky post-commit hook (.husky/post-commit)
    ↓
post-commit-memory.sh
    ↓
ai_memory/.pending_updates (append)

---

Claude session start/stop
    ↓
process-pending-memory.sh (SessionStart & Stop hooks)
    ↓
Read .pending_updates
    ↓
events.jsonl (append)
    ↓
Clear .pending_updates

---

Session briefing (on demand)
    ↓
dev-memory-briefing skill
    ↓
Load & filter events
    ↓
Generate SESSION_BRIEFING.md
    ↓
Display to user
```

### Hook Architecture

1. **Husky Git Hook** (`.husky/post-commit`)
   - Runs after every `git commit`
   - Calls `.claude/hooks/post-commit-memory.sh`
   - Writes commit metadata to `ai_memory/.pending_updates`
   - Works even when Claude is not running

2. **Claude Code Hooks** (in `.claude/settings.json`)
   - `SessionStart`: Runs `process-pending-memory.sh` to catch up on commits made outside Claude
   - `Stop`: Runs `process-pending-memory.sh` to capture commits made during the session

3. **Processing Hook** (`.claude/hooks/process-pending-memory.sh`)
   - Reads `.pending_updates` file
   - Extracts commit type from message (feat/fix/refactor/etc.)
   - Writes structured events to `events.jsonl`
   - Clears pending file after processing

## Event Format

Each event in `events.jsonl` is a JSON object:

```json
{
  "id": "evt-20251210-001",
  "timestamp": "2025-12-10T21:13:00Z",
  "repo": "my-project",
  "branch": "feature/user-auth",
  "type": "feature_implemented",
  "title": "Add user authentication",
  "summary": "Implemented JWT-based auth with httpOnly cookies...",
  "commit_hash": "a3b2c1d",
  "related_issues": ["#123"],
  "open_questions": ["Should we add rate limiting?"],
  "next_steps": ["Add rate limiting for login attempts"],
  "confidence": "high"
}
```

### Event Types

| Type | Description | Example |
|------|-------------|---------|
| `feature_implemented` | New functionality | "Add dark mode toggle" |
| `bug_fixed` | Bug resolution | "Fix race condition in auth" |
| `refactor` | Code restructuring | "Extract service layer" |
| `decision` | Architectural choice | "Chose Prisma over TypeORM" |
| `test_added` | Test coverage | "Add E2E tests for checkout" |
| `docs_updated` | Documentation | "Update API docs" |
| `breaking_change` | API changes | "Change auth API to require 2FA" |

## Briefing Format

Session briefings show:

```markdown
# my-project – Development Briefing

**Generated:** 2025-12-10T22:30:00Z
**Branch:** feature/user-auth

## Where We Are

- **Status:** Actively building features
- **Active branches:** feature/user-auth, main
- **Active epics:** epic-auth-system

## Recent Activity

- **feature_implemented:** 3
- **bug_fixed:** 1

## Timeline (Last 20 Events)

- **[2025-12-10]** ✨ Add user authentication
  - Implemented JWT-based auth with httpOnly cookies
  - Related: #123

## Open Questions

- Should we add rate limiting for login attempts?

## Suggested Next Steps

- [ ] Add rate limiting for login attempts
- [ ] Update API documentation
```

## Configuration

In `.claude/config.yml`:

```yaml
devMemory:
  enabled: true                # Enable dev memory system
  autoUpdateOnCommit: true     # Run update hook automatically
  maxEventsPerCommit: 3        # Max events to extract per commit
  skipCommitTypes:             # Commit types to skip
    - 'chore'
    - 'build'
    - 'ci'
  briefing:
    showOnSessionStart: false  # Don't auto-show (opt-in)
    defaultMaxEvents: 20       # Events to show in briefing
    defaultDaysBack: 30        # Look back N days
```

## Best Practices

### Writing Commits for Better Memory

1. **Use Conventional Commits format:**
   ```
   feat: Add user profile editing
   fix: Resolve memory leak in context compaction
   refactor: Extract repository layer from services
   ```

2. **Link issues and PRs:**
   ```
   Fixes #123
   Related to #456
   PR #789
   ```

3. **Mention epics:**
   ```
   Part of epic-auth-system
   ```

4. **Add TODOs for next steps:**
   ```
   TODO: Add rate limiting
   TODO: Update documentation
   ```

5. **Ask questions in commit body:**
   ```
   Should we cache this per-user or globally?
   Is 15min token expiry too short?
   ```

### Using Memory Effectively

1. **Generate briefings before starting work:**
   - See what happened recently
   - Review open questions
   - Check next steps

2. **Filter by scope:**
   - Branch: Focus on current feature
   - Epic: See all related work
   - Issue: Review context for specific issue

3. **Commit JSONL files to git:**
   - Track project history
   - Share context with team
   - Preserve across repo clones

4. **Review memory periodically:**
   - Check event quality
   - Manually add important decisions
   - Archive old events if file grows large

## Manual Event Addition

You can manually append events to `events.jsonl`:

```bash
# Add a decision event
cat >> ai_memory/events.jsonl <<'EOF'
{"id":"evt-20251210-099","timestamp":"2025-12-10T15:00:00Z","repo":"my-project","branch":"main","type":"decision","title":"Chose PostgreSQL over MongoDB","summary":"Selected PostgreSQL for relational data model and ACID guarantees. MongoDB considered but relational queries more important than document flexibility.","tags":["architecture","database","decision"],"confidence":"high"}
EOF
```

## Troubleshooting

### Memory not updating?

**Check configuration:**
```bash
# Ensure enabled in config
grep -A 2 "devMemory:" .claude/config.yml
```

**Check hook exists:**
```bash
ls -la .claude/hooks/post-commit-memory.sh
# Should be executable
```

**Check hook is configured:**
```bash
# Look for PostToolUse hooks in settings.json
cat .claude/settings.json | grep -A 5 "hooks"
```

**Manual trigger:**
```bash
# Manually run the hook
bash .claude/hooks/post-commit-memory.sh
```

### Events not appearing in briefing?

**Check filters:**
- Wrong branch? (briefing defaults to current branch)
- Too far back? (default: 30 days)
- Wrong repo name?

**Check file exists:**
```bash
cat ai_memory/events.jsonl | wc -l
# Should show number of events
```

**Parse manually:**
```bash
# View all events
cat ai_memory/events.jsonl | jq .

# Filter by type
cat ai_memory/events.jsonl | jq 'select(.type == "feature_implemented")'

# Recent events
tail -n 10 ai_memory/events.jsonl | jq .
```

### File growing too large?

**Check size:**
```bash
wc -l ai_memory/events.jsonl
# If > 10,000 lines, consider archiving
```

**Archive old events:**
```bash
# Move events older than 1 year to archive
grep "\"timestamp\":\"2024-" ai_memory/events.jsonl > ai_memory/events-2024.jsonl
gzip ai_memory/events-2024.jsonl

# Remove from main file (BE CAREFUL - make backup first)
cp ai_memory/events.jsonl ai_memory/events.jsonl.backup
grep -v "\"timestamp\":\"2024-" ai_memory/events.jsonl.backup > ai_memory/events.jsonl
```

## Documentation

- **[dev-memory-context.md](./dev-memory-context.md)** - Toolkit integration details
- **[dev-memory-format.md](./dev-memory-format.md)** - JSONL format specification
- **[dev-memory-rules-and-hooks.md](./dev-memory-rules-and-hooks.md)** - Hook configuration

## Examples

### Example 1: Feature Development Timeline

```bash
# Developer works on auth feature over 3 days
# Commits:
# - Day 1: feat: Add login endpoint
# - Day 1: feat: Add JWT token generation
# - Day 2: fix: Handle expired tokens correctly
# - Day 2: test: Add auth integration tests
# - Day 3: docs: Update API documentation for auth

# Result in events.jsonl:
# - 5 events (1 per commit)
# - Linked to issue #123
# - Open questions tracked
# - Next steps extracted from TODOs
```

### Example 2: Bug Fix Session

```bash
# Developer fixes memory leak
# Commit:
# fix: Resolve memory leak in context compaction
#
# Compaction was holding references to old slices.
# Added explicit cleanup and WeakMap for cache.
# Reduced memory usage by ~40% under heavy load.
#
# Fixes #305

# Result:
# - Event type: bug_fixed
# - Summary extracted from commit body
# - Linked to issue #305
# - Session updated with bug fix activity
```

### Example 3: Session Briefing

```bash
# Developer starts work after weekend
# Asks Claude: "Generate a session briefing"

# Claude loads events from ai_memory/events.jsonl
# Filters to current branch
# Shows last 20 events
# Highlights open questions and next steps
# Writes SESSION_BRIEFING.md
# Displays briefing to developer
```

## Integration with Other Tools

### Git Hooks

Compatible with existing git hooks:
- Runs as PostToolUse hook (not standard git hook)
- Non-blocking (won't fail commits)
- Can coexist with pre-commit, lint-staged, etc.

### CI/CD

Add to CI pipeline for historical analysis:

```yaml
# .github/workflows/memory-analysis.yml
- name: Analyze dev memory
  run: |
    echo "Recent features:"
    cat ai_memory/events.jsonl | jq -r 'select(.type == "feature_implemented") | .title' | tail -n 10
```

### Project Management

Export events for reporting:

```bash
# Features shipped this sprint
cat ai_memory/events.jsonl | jq -r 'select(.type == "feature_implemented" and (.timestamp | startswith("2025-12"))) | .title'

# Bugs fixed this month
cat ai_memory/events.jsonl | jq -r 'select(.type == "bug_fixed" and (.timestamp | startswith("2025-12"))) | .title'
```

## Roadmap

Future enhancements:

- [ ] Web UI for browsing events
- [ ] Event search and filtering
- [ ] Export to GitHub Issues/Projects
- [ ] Team aggregation (combine events from multiple devs)
- [ ] Automatic epic detection
- [ ] Integration with project-memory skill (MCP)
- [ ] Automatic file size rotation
- [ ] Event quality scoring

## Contributing

To improve the dev memory system:

1. Follow toolkit patterns (see `dev-memory-context.md`)
2. Keep skills framework-agnostic
3. Maintain backward compatibility with JSONL format
4. Add tests for event extraction logic
5. Update documentation

## License

Part of the Claude Code Toolkit project.
