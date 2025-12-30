# Loop Stop Command

**Arguments:** [--status] [--clean]

**Description:** Stop an active loop orchestration and optionally clean up state.

---

## Purpose

Immediately stop any active `/loop` orchestration:
```bash
/loop-stop              # Stop active loop
/loop-stop --status     # Show loop status without stopping
/loop-stop --clean      # Stop and remove state file
```

---

## Workflow

### Step 1: Parse Arguments

```bash
SHOW_STATUS_ONLY=false
CLEAN_STATE=false

for arg in "$@"; do
  case $arg in
    --status) SHOW_STATUS_ONLY=true ;;
    --clean) CLEAN_STATE=true ;;
  esac
done

STATE_FILE=".claude/state/loop.local.json"
```

### Step 2: Check for Active Loop

```bash
if [ ! -f "$STATE_FILE" ]; then
  echo "No active loop found."
  echo ""
  echo "To start a loop: /loop <task description>"
  exit 0
fi

# Read state
ENABLED=$(jq -r '.enabled // false' "$STATE_FILE")
TASK=$(jq -r '.original_arguments // "unknown"' "$STATE_FILE")
ITERATION=$(jq -r '.iteration // 1' "$STATE_FILE")
MAX_ITER=$(jq -r '.max_iterations // 20' "$STATE_FILE")
MODE=$(jq -r '.mode // "auto"' "$STATE_FILE")
STARTED=$(jq -r '.started_at // "unknown"' "$STATE_FILE")
```

### Step 3: Display Status

```bash
echo "======================================"
echo " LOOP STATUS"
echo "======================================"
echo "Active: $ENABLED"
echo "Task: $TASK"
echo "Mode: $MODE"
echo "Iteration: $ITERATION / $MAX_ITER"
echo "Started: $STARTED"
echo "State file: $STATE_FILE"
echo "======================================"
```

### Step 4: Stop Loop (Unless Status Only)

```bash
if [ "$SHOW_STATUS_ONLY" = "true" ]; then
  echo ""
  echo "Use /loop-stop to disable this loop."
  exit 0
fi

if [ "$ENABLED" != "true" ]; then
  echo ""
  echo "Loop is already disabled."

  if [ "$CLEAN_STATE" = "true" ]; then
    rm -f "$STATE_FILE"
    rm -f ".claude/state/loop.continue"
    rm -f ".claude/state/loop.log"
    echo "State files cleaned."
  fi

  exit 0
fi

# Disable the loop
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
jq --arg reason "Manual stop via /loop-stop" \
   --arg ts "$TIMESTAMP" \
   '.enabled = false | .disabled_reason = $reason | .disabled_at = $ts' \
   "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"

echo ""
echo "Loop STOPPED."
echo "Iterations completed: $ITERATION"
```

### Step 5: Clean State (If Requested)

```bash
if [ "$CLEAN_STATE" = "true" ]; then
  rm -f "$STATE_FILE"
  rm -f ".claude/state/loop.continue"
  rm -f ".claude/state/loop.log"
  echo "State files removed."
fi
```

### Step 6: Provide Next Steps

```bash
echo ""
echo "To resume this task: /loop $TASK"
echo "To start a new loop: /loop <new task>"
```

---

## Usage Examples

### Stop Active Loop
```bash
/loop-stop
```

### Check Status Only
```bash
/loop-stop --status
```

### Stop and Clean Up
```bash
/loop-stop --clean
```

---

## Expected Outcomes

### Success
- Loop disabled immediately
- State preserved for potential resumption
- Clear status displayed

### No Active Loop
- Message indicating no loop found
- Guidance on how to start a loop

### Already Stopped
- Message indicating loop already disabled
- Option to clean state files

---

## Related Commands

- `/loop <task>` - Start a new loop orchestration
- `/conductor` - Full workflow without looping
- `/audit` - One-time audit

---

**Generated**: 2025-12-30 (Loop Orchestration System)
