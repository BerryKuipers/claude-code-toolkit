# Disable Reflection Logging

**Arguments:** (none)

**Description:** Disable the reflection system for the current project. The stop hook will no longer log reflection candidates.

---

## Workflow

### Step 1: Check Current State

```bash
CONFIG_FILE=".claude/config.yml"

# Check if config exists
if [ ! -f "$CONFIG_FILE" ]; then
  echo "ℹ️  No config.yml found - reflection was never enabled."
  exit 0
fi

# Check current state
if ! grep -q 'reflection:' "$CONFIG_FILE" 2>/dev/null; then
  echo "ℹ️  Reflection was never enabled for this project."
  exit 0
fi

if grep -A1 'reflection:' "$CONFIG_FILE" | grep -q 'enabled: false'; then
  echo "ℹ️  Reflection is already disabled for this project."
  exit 0
fi
```

### Step 2: Update Config File

Read the current `.claude/config.yml` file and set reflection to disabled:

```yaml
# Reflection Settings
reflection:
  enabled: false
  # ... other settings preserved
```

Change `enabled: true` to `enabled: false` in the reflection section.

### Step 3: Print Confirmation

```
✅ Reflection disabled for this project.

Your data is preserved:
  - .claude/state/reflection-candidates.jsonl (not deleted)
  - .claude/rules/19-learned-draft.mdc (not deleted)
  - .claude/rules/20-learned-patterns.mdc (not deleted)

The stop hook will no longer log new candidates.
Existing patterns and rules remain active.

To re-enable: /reflect-enable
```

---

## Expected Output

```
✅ Reflection disabled for this project.

Your data is preserved:
  - .claude/state/reflection-candidates.jsonl (not deleted)
  - .claude/rules/19-learned-draft.mdc (not deleted)
  - .claude/rules/20-learned-patterns.mdc (not deleted)
```

---

## Notes

- This command does NOT delete any existing candidates or patterns
- Learned rules remain active even when logging is disabled
- The only effect is stopping the stop hook from logging new candidates

---

## Related Commands

- `/reflect-enable` - Enable reflection logging
- `/reflect` - Analyze and apply learned patterns
- `/promote-learnings` - Consolidate draft patterns
