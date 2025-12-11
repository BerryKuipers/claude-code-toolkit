# Dev Memory Rules and Hooks

This document explains how the dev memory system integrates with git commits through hooks and rules.

## Hook Architecture

The dev memory system uses **PostToolUse hooks** to trigger after commits, not standard git hooks.

### Why PostToolUse Instead of Git Hooks?

| Aspect | Standard Git Hook | PostToolUse Hook |
|--------|------------------|------------------|
| Trigger | Direct git command | After Bash tool executes `git commit` |
| Context | Limited git context | Full Claude Code context |
| Blocking | Can block commit | Never blocks commit |
| Error handling | Fails commit on error | Logs warning, continues |
| Cross-platform | Varies by shell | Consistent via Claude Code |

### Hook Execution Flow

```
User commits via Claude Code
    ↓
Bash tool executes: git commit -m "..."
    ↓
Git creates commit successfully
    ↓
PostToolUse hook triggers
    ↓
.claude/hooks/post-commit-memory.sh runs
    ↓
Extract commit metadata
    ↓
Create pending update marker
    ↓
Claude processes pending updates
    ↓
dev-memory-update skill invoked
    ↓
Events appended to ai_memory/events.jsonl
```

## Hook File: `post-commit-memory.sh`

**Location:** `.claude/hooks/post-commit-memory.sh`

**Purpose:** Extract commit metadata and trigger dev memory update

**Permissions:** Executable (`chmod +x`)

**Content:**

```bash
#!/bin/bash
# Post-commit hook for dev memory updates

set -e

# Check if dev memory is enabled
CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
CONFIG_FILE="$CLAUDE_PROJECT_DIR/.claude/config.yml"

# Default to enabled if config doesn't exist
ENABLED=true
if [ -f "$CONFIG_FILE" ]; then
  if grep -q "devMemory:" "$CONFIG_FILE" && grep -A 1 "devMemory:" "$CONFIG_FILE" | grep -q "enabled: false"; then
    ENABLED=false
  fi
fi

if [ "$ENABLED" = false ]; then
  exit 0
fi

# Extract commit information
REPO=$(basename "$(git rev-parse --show-toplevel)")
BRANCH=$(git branch --show-current)
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_SHORT_HASH=$(git rev-parse --short HEAD)
COMMIT_MESSAGE=$(git log -1 --pretty=%B HEAD)
COMMIT_TIMESTAMP=$(git log -1 --format=%aI HEAD)
FILES_CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD | wc -l)

# Create pending update marker
MEMORY_DIR="$CLAUDE_PROJECT_DIR/ai_memory"
mkdir -p "$MEMORY_DIR"

PENDING_FILE="$MEMORY_DIR/.pending_updates"
cat >> "$PENDING_FILE" <<EOF
$COMMIT_HASH|$COMMIT_TIMESTAMP|$BRANCH|$REPO|$FILES_CHANGED
EOF

exit 0
```

### Hook Configuration

**In `.claude/settings.json`:**

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

**Important:**
- Multiple hooks can be configured
- Hooks run in array order
- Each hook should be idempotent
- Hooks should exit 0 on success

## Rules

The dev memory system follows these rules:

### Rule 1: Never Block Commits

**Principle:** Memory updates are supplementary, not critical

**Implementation:**
- Hook uses `set -e` but catches errors internally
- Always exits with code 0
- Logs warnings to stderr, not stdout
- Never throws fatal errors

**Example:**
```bash
# Even if memory update fails, commit succeeds
if ! process_memory_update; then
  echo "⚠️ Memory update failed, but commit succeeded" >&2
  exit 0
fi
```

### Rule 2: Configuration is Opt-Out

**Principle:** Dev memory enabled by default, disable explicitly

**Configuration check:**
```yaml
# .claude/config.yml
devMemory:
  enabled: false  # Explicitly disable
```

**Default behavior:** If `devMemory` section missing, assume enabled

### Rule 3: Graceful Degradation

**Scenarios:**

| Scenario | Behavior |
|----------|----------|
| `ai_memory/` doesn't exist | Create it |
| `events.jsonl` doesn't exist | Create it |
| Malformed JSONL line | Skip line, log warning |
| Commit message unparseable | Create generic event |
| No git repo | Skip silently |
| Config file missing | Assume defaults |

### Rule 4: Idempotent Operations

**Principle:** Running multiple times is safe

**Implementation:**
- Append-only JSONL (never rewrite)
- Event IDs unique by date + sequence
- Session updates append new versions
- mkdir -p (safe if exists)

### Rule 5: Cross-Platform Compatibility

**Requirements:**
- Works on Linux, Mac, Windows (Git Bash)
- Uses POSIX shell features only
- No bash 4+ specific features
- UTF-8 encoding everywhere

**Testing:**
```bash
# Test on different platforms
bash -n .claude/hooks/post-commit-memory.sh  # Syntax check
shellcheck .claude/hooks/post-commit-memory.sh  # Linting
```

## Hook Integration with Toolkit Sync

The hook is automatically synced to target repositories:

### Sync Process

1. **Toolkit sync runs:**
   ```bash
   bash scripts/sync-claude-toolkit.sh
   ```

2. **Hooks directory synced:**
   ```bash
   rsync -a --delete "$TOOLKIT_DIR/hooks/" "$TARGET_DIR/hooks/"
   ```

3. **Hooks made executable:**
   ```bash
   chmod +x "$TARGET_DIR/hooks/"*.sh
   ```

4. **Settings.json checked:**
   - If hooks not configured, warning shown
   - User must manually add to settings.json

### Manual Hook Setup

If sync doesn't auto-configure hooks:

1. **Edit `.claude/settings.json`:**
   ```json
   {
     "hooks": {
       "PostToolUse": [
         ".claude/hooks/post-commit-memory.sh"
       ]
     }
   }
   ```

2. **Verify hook is executable:**
   ```bash
   chmod +x .claude/hooks/post-commit-memory.sh
   ```

3. **Test hook:**
   ```bash
   # Make a test commit
   git commit --allow-empty -m "test: Verify dev memory hook"

   # Check if pending updates created
   cat ai_memory/.pending_updates
   ```

## Event Processing Flow

### Step 1: Commit Created

```bash
git commit -m "feat: Add user authentication

Implemented JWT-based auth.

Fixes #123"
```

### Step 2: PostToolUse Hook Triggered

```bash
# Claude Code detects Bash tool executed git commit
# Triggers all PostToolUse hooks
```

### Step 3: Metadata Extracted

```bash
REPO="my-project"
BRANCH="feature/user-auth"
COMMIT_HASH="a3b2c1d4e5f6..."
COMMIT_MESSAGE="feat: Add user authentication..."
COMMIT_TIMESTAMP="2025-12-10T21:13:00Z"
FILES_CHANGED=12
```

### Step 4: Pending Update Created

```bash
# Append to .pending_updates
echo "a3b2c1d4e5f6|2025-12-10T21:13:00Z|feature/user-auth|my-project|12" >> ai_memory/.pending_updates
```

### Step 5: Claude Processes Pending Updates

```bash
# Claude detects .pending_updates file
# Reads pending commits
# Invokes dev-memory-update skill for each
```

### Step 6: Event Created

```json
{"id":"evt-20251210-001","timestamp":"2025-12-10T21:13:00Z","repo":"my-project","branch":"feature/user-auth","type":"feature_implemented","title":"Add user authentication","summary":"Implemented JWT-based auth.","commit_hash":"a3b2c1d","related_issues":["#123"],"files_changed":12,"confidence":"high"}
```

### Step 7: Event Appended

```bash
echo "$EVENT_JSON" >> ai_memory/events.jsonl
```

### Step 8: Pending Update Cleared

```bash
# Remove processed commit from .pending_updates
# Or clear entire file if all processed
```

## Disabling Dev Memory

### Temporary Disable (One Commit)

Not directly supported. Dev memory runs on all commits when enabled.

Workaround:
```bash
# Temporarily move hook
mv .claude/hooks/post-commit-memory.sh .claude/hooks/post-commit-memory.sh.disabled

# Make commit
git commit -m "..."

# Restore hook
mv .claude/hooks/post-commit-memory.sh.disabled .claude/hooks/post-commit-memory.sh
```

### Permanent Disable (Project-Wide)

**In `.claude/config.yml`:**
```yaml
devMemory:
  enabled: false
```

**Or remove hook from settings.json:**
```json
{
  "hooks": {
    "PostToolUse": [
      ".claude/hooks/post-tool-use.sh"
      // Removed: ".claude/hooks/post-commit-memory.sh"
    ]
  }
}
```

## Error Handling

### Hook Errors

**Principle:** Never fail the commit, log errors gracefully

**Example error handling:**
```bash
#!/bin/bash
set -e  # Exit on error

# Trap errors
trap 'echo "⚠️ Dev memory hook failed at line $LINENO: $BASH_COMMAND" >&2; exit 0' ERR

# Hook logic here...

# Always exit 0 (success)
exit 0
```

### Processing Errors

**Scenarios:**

| Error | Handling |
|-------|----------|
| Invalid commit message | Create generic event |
| Missing git info | Log warning, skip |
| JSONL parse error | Skip malformed line |
| File write permission denied | Log error, continue |
| Disk full | Log error, continue |

**Never:**
- Throw uncaught exceptions
- Fail the commit
- Corrupt existing JSONL files
- Block the workflow

## Performance Considerations

### Hook Execution Time

**Target:** < 100ms per commit

**Measurements:**
- Extract metadata: ~10ms
- Write pending update: ~5ms
- Total hook time: ~15ms

**Async processing:**
- Hook creates marker file quickly
- Actual event extraction happens later
- Doesn't block commit completion

### File I/O

**Optimization:**
- Append-only writes (no reads in hook)
- Single write operation per commit
- No JSON parsing in hook
- Batch processing of pending updates

**Limits:**
- Max 1KB per pending update line
- Max 10,000 pending updates before rotation

## Debugging

### Enable Verbose Logging

```bash
# Edit post-commit-memory.sh
# Add at top:
set -x  # Enable trace mode

# Run commit
git commit -m "test"

# Check output
```

### Manual Trigger

```bash
# Test hook without committing
bash .claude/hooks/post-commit-memory.sh
```

### Check Pending Updates

```bash
# View pending commits
cat ai_memory/.pending_updates

# Count pending
wc -l ai_memory/.pending_updates
```

### Verify Events Created

```bash
# View last event
tail -n 1 ai_memory/events.jsonl | jq .

# Count events today
TODAY=$(date +%Y%m%d)
grep "\"id\":\"evt-$TODAY-" ai_memory/events.jsonl | wc -l
```

## Best Practices

### For Toolkit Maintainers

1. **Keep hook simple** - Complex logic in skill, not hook
2. **Test on all platforms** - Linux, Mac, Windows Git Bash
3. **Validate JSONL** - Ensure valid JSON before appending
4. **Document errors** - Clear error messages
5. **Version hook** - Track changes in git

### For Project Users

1. **Commit to git** - Track `ai_memory/*.jsonl` files
2. **Monitor file size** - Archive if > 10MB
3. **Review events** - Ensure quality of extracted data
4. **Customize config** - Adjust maxEventsPerCommit, skipCommitTypes
5. **Report issues** - If hook fails consistently

## Security Considerations

### Sensitive Data

**Never log:**
- Passwords or API keys
- Personal identifiable information (PII)
- Secrets or tokens
- Private business logic

**Commit message safety:**
- Dev memory only stores what's in commit messages
- Don't put secrets in commit messages
- Review events before pushing to public repos

### File Permissions

**Recommended:**
```bash
chmod 600 ai_memory/events.jsonl     # Owner read/write only
chmod 600 ai_memory/sessions.jsonl
chmod 700 ai_memory/                 # Owner access only
```

**Or:**
```bash
# If committing to git, use default permissions
# Git tracks file contents, not permissions
```

## Troubleshooting

### Hook not running?

1. **Check configuration:**
   ```bash
   cat .claude/settings.json | grep -A 5 "hooks"
   ```

2. **Check executable:**
   ```bash
   ls -l .claude/hooks/post-commit-memory.sh
   # Should show -rwxr-xr-x
   ```

3. **Check enabled:**
   ```bash
   grep -A 2 "devMemory:" .claude/config.yml
   # Should show enabled: true
   ```

4. **Manual test:**
   ```bash
   bash .claude/hooks/post-commit-memory.sh
   echo $?  # Should be 0
   ```

### Events not created?

1. **Check pending updates:**
   ```bash
   cat ai_memory/.pending_updates
   # Should show commit info
   ```

2. **Process manually:**
   ```bash
   # Ask Claude to process pending updates
   # Or invoke dev-memory-update skill manually
   ```

3. **Check permissions:**
   ```bash
   touch ai_memory/test.txt
   # If fails, check directory permissions
   ```

### Wrong event types?

1. **Review commit message format:**
   ```bash
   git log -1 --pretty=%B
   # Should start with type: feat:, fix:, etc.
   ```

2. **Check extraction logic:**
   - See `.claude/skills/memory/dev-memory/update/SKILL.md`
   - Review type inference rules

3. **Manually edit:**
   ```bash
   # Events are just JSON - edit directly
   nano ai_memory/events.jsonl
   ```

## See Also

- [dev-memory-context.md](./dev-memory-context.md) - Integration with toolkit
- [dev-memory-format.md](./dev-memory-format.md) - JSONL format spec
- [README.md](./README.md) - User guide
