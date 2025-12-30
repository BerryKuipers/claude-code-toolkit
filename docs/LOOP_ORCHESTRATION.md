# Loop Orchestration System

The `/loop` command provides autonomous task orchestration that continues automatically until completion or max iterations.

## Quick Start

```bash
# Fix failing tests (auto-detects test framework)
/loop fix the failing tests for authentication

# Implement a feature (uses conductor workflow)
/loop implement user dark mode preference toggle

# Refactor code (uses refactor agent)
/loop refactor the payment service for better separation of concerns

# Security audit (uses audit agent with auto-fix)
/loop audit this codebase for security vulnerabilities
```

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                         /loop <task>                            │
├─────────────────────────────────────────────────────────────────┤
│  1. Parse task and detect mode (workflow/agent/audit/quick-fix) │
│  2. Select appropriate agents/workflows                         │
│  3. Detect verification gates (test/lint/build)                 │
│  4. Create loop state file                                      │
│  5. Start iteration 1                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ITERATION LOOP                               │
├─────────────────────────────────────────────────────────────────┤
│  Agent works on task...                                         │
│  Runs verification gates...                                     │
│                                                                 │
│  IF complete: Print <promise>DONE</promise>                     │
│  IF more work: Print <loop>CONTINUE</loop>                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Stop Hook Checks                             │
├─────────────────────────────────────────────────────────────────┤
│  - Check for DONE marker → disable loop                         │
│  - Check max iterations → hard stop                             │
│  - Otherwise → increment iteration, prepare continuation        │
└─────────────────────────────────────────────────────────────────┘
```

## Modes

### Auto Mode (Default)
The loop automatically detects the best mode based on task keywords:

| Keywords | Mode | Handler |
|----------|------|---------|
| implement, feature, build, create, add | workflow-run | Conductor agent |
| refactor, design, debug, review | agent-run | Specialized agent |
| audit, check, validate, scan, security | audit | Audit agent |
| fix, patch, update, change | quick-fix | Minimal intervention |

### Force Specific Mode
```bash
/loop implement dark mode --mode=agent      # Force single agent
/loop fix tests --mode=workflow             # Force full workflow
```

## Verification Gates

The loop automatically detects available verification tools:

### Node.js Projects
```bash
# Detected from package.json
pnpm test / npm test / yarn test    # if "test" script exists
npm run lint                        # if "lint" script exists
npm run build                       # if "build" script exists
```

### .NET Projects
```bash
dotnet test
dotnet build
```

### Always
```bash
git status --porcelain    # Check for uncommitted changes
```

## State Management

### State File Location
```
.claude/state/loop.local.json
```

### State Schema
```json
{
  "enabled": true,
  "mode": "auto",
  "completion_promise": "DONE",
  "max_iterations": 20,
  "iteration": 1,
  "original_arguments": "fix the failing tests",
  "selected_agents": ["debugger"],
  "verification_steps": ["pnpm test", "pnpm lint"],
  "last_result_summary": "Fixed 3/5 test failures",
  "session_token": "abc123...",
  "cwd": "/path/to/project",
  "started_at": "2025-12-30T10:00:00Z",
  "updated_at": "2025-12-30T10:15:00Z"
}
```

### Session Scoping
The loop includes safeguards against cross-session/cross-repo contamination:
- **session_token**: Generated from cwd + timestamp + PID
- **cwd**: Recorded working directory
- Hooks verify cwd matches before continuing

## Commands

### Start a Loop
```bash
/loop <task description> [options]

Options:
  --max=N         Maximum iterations (default: 20)
  --promise=TOKEN Completion marker (default: DONE)
  --mode=MODE     Force mode: auto|workflow|agent|audit|quick-fix
```

### Stop a Loop
```bash
/loop-stop              # Stop active loop
/loop-stop --status     # Show status without stopping
/loop-stop --clean      # Stop and remove state files
```

## Hooks

### SessionStart: loop-session-start.sh
- Checks for active loop or continuation file
- Displays loop status and continuation prompt
- Runs automatically when session starts

### Stop: loop-controller.sh / loop-controller.ps1
- Enforces max_iterations safety limit
- Detects completion markers
- Prepares continuation state for next session
- Available in both Bash and PowerShell for Windows compatibility

## Integration with Existing System

### Uses Existing Agents
- **conductor**: Full workflow orchestration
- **orchestrator**: Task routing
- **architect**: Architecture validation
- **audit**: Code quality
- **refactor**: Code improvement
- **implementation**: Feature building
- **debugger**: Test fixing

### Uses Existing Commands
- `/test-all`: Comprehensive testing
- `/audit`: Quality audit
- `/refactor`: Code improvement
- `/conductor`: Full workflow

## Verification Testing

### Test 1: Basic Loop
```bash
# In any repo with the toolkit
/loop fix a simple typo in README.md

# Expected:
# - State file created
# - Task classified as quick-fix
# - Completes in 1-2 iterations
# - Prints <promise>DONE</promise>
```

### Test 2: Max Iterations
```bash
/loop implement world peace --max=3

# Expected:
# - Runs 3 iterations
# - Hard stops at max
# - State shows "Max iterations reached"
```

### Test 3: Stop Command
```bash
/loop implement a complex feature
# ... let it run 1-2 iterations ...
/loop-stop

# Expected:
# - Loop disabled immediately
# - Status displayed
# - Can resume with /loop <same task>
```

### Test 4: Cross-Session Resume
```bash
# Session 1:
/loop refactor the authentication module
# ... runs iteration 1 ...
# End session

# Session 2:
# On SessionStart, loop-session-start.sh runs
# Expected output:
# ======================================
#  ACTIVE LOOP DETECTED
# ======================================
# Task: refactor the authentication module
# Current iteration: 2 / 20
# ...
```

## Windows Compatibility

The loop system includes PowerShell support:

### PowerShell Hook
`.claude/hooks/loop-controller.ps1` provides identical functionality to the bash version:
- Reads JSON state with ConvertFrom-Json
- Updates state with ConvertTo-Json
- Enforces same safety limits

### Using on Windows
If bash is unavailable, update settings.json to use PowerShell:
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -ExecutionPolicy Bypass -File .claude/hooks/loop-controller.ps1"
          }
        ]
      }
    ]
  }
}
```

## Troubleshooting

### Loop Not Continuing
1. Check state file exists: `cat .claude/state/loop.local.json`
2. Verify enabled=true
3. Check iteration < max_iterations
4. Ensure hooks are registered in settings.json

### Loop Not Stopping
1. Check for DONE marker in output: `<promise>DONE</promise>`
2. Or set done flag manually:
   ```bash
   jq '.done = true' .claude/state/loop.local.json > tmp && mv tmp .claude/state/loop.local.json
   ```
3. Or run `/loop-stop`

### State File Corruption
```bash
# Reset state
/loop-stop --clean
# Start fresh
/loop <task>
```

### Cross-Repo Contamination
The loop checks cwd before continuing. If you see "ignoring" in logs, the state file is from a different directory. Use `/loop-stop --clean` to reset.

## Architecture Decisions

### Why Repo-Local State?
- Prevents cross-repo loops from interfering
- Allows per-project configuration
- State is not synced (intentionally)

### Why Session Token?
- Prevents stale loops from resurrecting
- Identifies specific session for debugging
- Allows safe cleanup of old state

### Why Both Bash and PowerShell?
- Windows users often have issues with bash quoting
- PowerShell is more reliable on Windows
- Choice available based on environment

### Why Max Iterations Default 20?
- Prevents runaway loops
- Enough for most complex tasks
- Can be overridden per-task

## Future Enhancements

Potential improvements for consideration:
1. **Webhook notifications** on loop completion
2. **Integration with CI/CD** for automated testing loops
3. **Parallel loop execution** for independent tasks
4. **Loop history** tracking across sessions
5. **Cost estimation** based on iteration count
