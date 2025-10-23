# Smart Resumption Integration

## Add to any command (3 steps):

### 1. **Add to beginning of command:**

```markdown
## 🔄 Smart Resumption Check

```bash
STATE_FILE=".claude/state/[COMMAND_NAME].json"

# Check for existing state
if [ -f "$STATE_FILE" ]; then
  echo "🔄 Previous session found:"
  echo "📍 Progress: $(jq -r '.completedSteps | length' "$STATE_FILE") steps completed"
  echo "🕒 Started: $(jq -r '.timestamp' "$STATE_FILE")"
  echo ""
  echo "Resume from step $(jq -r '.currentStep' "$STATE_FILE")? [R/F/S]"
  echo "R=Resume, F=Fresh start, S=Show status"

  case "$RESUME_CHOICE" in
    F|f) rm -f "$STATE_FILE"; echo "🆕 Starting fresh";;
    S|s) cat "$STATE_FILE" | jq '.'; exit 0;;
    *) echo "▶️ Resuming..."; COMPLETED_STEPS=$(jq -r '.completedSteps | join(" ")' "$STATE_FILE");;
  esac
fi

# Helper functions
should_skip_step() { [[ " $COMPLETED_STEPS " =~ " $1 " ]]; }
save_step() {
  mkdir -p ".claude/state"
  cat > "$STATE_FILE" << EOF
{
  "command": "[COMMAND_NAME]",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "context": $3,
  "completedSteps": [$(echo "$COMPLETED_STEPS $1" | tr ' ' ',' | sed 's/^,//')],
  "currentStep": $(($1 + 1)),
  "metadata": {"lastActivity": "$2"}
}
EOF
  COMPLETED_STEPS="$COMPLETED_STEPS $1"
}
```
```

### 2. **Wrap each major step:**

```markdown
### Step X: [Step Name]

```bash
if should_skip_step X; then
  echo "⏭️ Step X already completed"
else
```

[Original step content here]

```bash
  save_step X "Step X completed" '{"key": "value"}'
fi
```
```

### 3. **Add at successful completion:**

```markdown
```bash
rm -f "$STATE_FILE"
echo "🧹 Session complete - state cleaned"
```

🎉 [Success message]
```

## Replace [COMMAND_NAME] with:
- `issue-pickup`
- `refactor`
- `pr-process`
- etc.

**That's it! Your command now has smart resumption.** 🚀