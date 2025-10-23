# Orchestrator - Central Command Hub Entrypoint

**Arguments:** task="<natural language description>" [mode=full|advisory]

**Success Criteria:** Successfully delegates to OrchestratorAgent and returns consolidated results

**Description:** Entrypoint slash-command that delegates all orchestration logic to the OrchestratorAgent. This command serves as the user-facing interface for intelligent task routing and workflow coordination.

---

## ⚠️ Important: This is an Entrypoint Only

**This slash-command does NOT contain orchestration logic.**

All orchestration intelligence, task routing, and workflow coordination is handled by:
- **OrchestratorAgent** (`.claude/agents/orchestrator.md`)

This command simply provides a convenient `/orchestrator` interface for users.

---

## How It Works

```
User: /orchestrator task="..." mode=...
         ↓
This Slash-Command (entrypoint)
         ↓
OrchestratorAgent (the brain)
         ↓
Specialized agents/commands
         ↓
Consolidated results
```

---

## Usage

### Basic Usage

```bash
# Full mode (default): Complete workflow orchestration
/orchestrator task="test message delete functionality"

# Advisory mode: Non-blocking recommendations
/orchestrator task="implement user preferences API" mode=advisory
```

### Common Task Examples

**UI Testing:**
```bash
/orchestrator task="test message delete functionality"
# → Delegates to: data-setup, app-discovery, test-ui
```

**Code Development:**
```bash
/orchestrator task="refactor authentication system"
# → Delegates to: refactor agent with architectural guidance
```

**Architecture Review:**
```bash
/orchestrator task="review system architecture"
# → Delegates to: architect agent for comprehensive analysis
```

**Database Operations:**
```bash
/orchestrator task="analyze database performance"
# → Delegates to: db-manage for performance review
```

---

## Execution

**Claude Code should invoke the OrchestratorAgent with the provided task and mode:**

### Step 1: Parse Arguments

```bash
# Extract task and mode from arguments
TASK="$1"  # Required: task description
MODE="${2:-full}"  # Optional: full (default) or advisory
```

### Step 2: Delegate to OrchestratorAgent

**Claude Code invokes the OrchestratorAgent (not bash):**

The OrchestratorAgent will:
1. Analyze task intent
2. Discover available commands/agents
3. Select optimal delegation pattern
4. Execute workflow (sequential/parallel/conditional)
5. Aggregate results
6. Return consolidated report

### Step 3: Return Results

The OrchestratorAgent returns results in this format:

**Full Mode:**
```markdown
## 🎯 Orchestration Summary

**Session ID**: 1234567890
**Task**: test message delete functionality
**Mode**: full

### Delegated Tasks
1. ✅ /data-setup - Test users validated
2. ✅ /app-discovery - Routes and selectors discovered
3. ✅ /test-ui - Message delete functionality tested

### Overall Status
✅ Task completed successfully

### Details
- All test users exist and authenticated
- Message delete button found and functional
- Delete confirmation modal working correctly
- Message removed from chat after confirmation

### Next Steps
- Consider adding undo functionality
- Test bulk message deletion
```

**Advisory Mode:**
```json
{
  "mode": "advisory",
  "sessionId": "1234567890",
  "task": "implement user preferences API",
  "recommendations": [
    {
      "command": "/arch:review",
      "reason": "New API endpoint - architectural compliance check",
      "priority": "high",
      "blocking": false
    },
    {
      "command": "/dev:create-test",
      "reason": "New feature - test coverage needed",
      "priority": "medium",
      "blocking": false
    }
  ],
  "reasoning": "New feature detected - architecture review and test generation recommended"
}
```

---

## Operating Modes

### Full Mode (Default)
- Complete workflow orchestration
- Blocking execution (wait for all tasks to complete)
- Detailed results for each delegation
- Comprehensive summary report

**When to use:**
- Complex multi-step tasks
- High-risk operations requiring validation
- Tasks requiring sequential execution
- When you need detailed results

### Advisory Mode
- Lightweight recommendations
- Non-blocking (returns immediately)
- Background task suggestions
- Used by other commands for consultation

**When to use:**
- Called from other commands (e.g., `/issue-pickup`)
- Quick task analysis without execution
- Background support task identification
- Non-critical recommendations

---

## Integration Points

### Called by Users
```bash
/orchestrator task="description" [mode=full|advisory]
```

### Called by Commands
```bash
# From issue-pickup.md
SlashCommand("/orchestrator", "task='implement feature X' mode=advisory")

# From debug.md
SlashCommand("/orchestrator", "task='fix authentication bug' mode=full")
```

### Invokes OrchestratorAgent
The OrchestratorAgent (`.claude/agents/orchestrator.md`) handles:
- Task categorization
- Command discovery
- Intelligent routing
- Workflow execution
- Result aggregation

---

## Configuration

Settings in `.claude/config.yml`:

```yaml
orchestrator:
  defaultMode: "full"           # Default mode if not specified
  createSessionId: true         # Generate session ID for logging
  propagateSession: true        # Pass session to delegated commands
  maxParallelDelegations: 5     # Max concurrent delegations
  delegationTimeoutMs: 300000   # 5 minute timeout per delegation
```

---

## Task Categories Recognized

**UI Testing**:
- Keywords: test, UI, message, chat, reaction, profile, delete, click
- Sequence: data-setup → app-discovery → test-ui

**Code Development**:
- Keywords: implement, create, build, refactor, fix
- Delegates to: refactor agent or architect agent

**Architecture Review**:
- Keywords: design, review, structure, architect, VSA, SOLID
- Delegates to: architect agent

**Database Operations**:
- Keywords: database, migration, query, schema
- Delegates to: db-manage

**Testing**:
- Keywords: test, validate, check, verify
- Delegates to: test-all or specific test commands

---

## Error Handling

**If OrchestratorAgent fails:**
```markdown
❌ Orchestration Failed

**Session ID**: 1234567890
**Error**: [error message]
**Attempted Delegations**: [list of commands attempted]

**Fallback Options**:
1. Run individual commands manually
2. Check logs in Seq dashboard: http://localhost:5341
3. Verify services are running: npm run dev
```

**If delegation fails:**
The OrchestratorAgent handles fallback strategies automatically.

---

## Comparison: Before vs After

### Before (Old Orchestrator Slash-Command)
```markdown
# Complex orchestration logic embedded in slash-command
- Intent analysis code
- Command discovery logic
- Routing algorithms
- Workflow coordination
- Result aggregation
= Hard to maintain, test, and extend
```

### After (New Entrypoint Pattern)
```markdown
# Simple entrypoint delegates to OrchestratorAgent
- Parse arguments
- Invoke OrchestratorAgent
- Return results
= Clean, testable, extensible
```

---

## For Developers

**To modify orchestration logic:**
- ✅ Edit `.claude/agents/orchestrator.md` (the agent)
- ❌ Do NOT edit this file (the entrypoint)

**To add new task categories:**
1. Update OrchestratorAgent's task analysis framework
2. Add category detection patterns
3. Define delegation strategy for category
4. Test with `/orchestrator task="new category example"`

**To add new commands/agents:**
1. Create command in `.claude/commands/` or agent in `.claude/agents/`
2. OrchestratorAgent will auto-discover it
3. No changes needed to this entrypoint

---

## Related Documentation

- **Agent Architecture**: `docs/agents-architecture.md`
- **OrchestratorAgent**: `.claude/agents/orchestrator.md`
- **Command Inventory**: `docs/command-inventory.md`
- **Integration Tests**: `docs/integration-tests.md` (pending)

---

## Summary

**This is a simple entrypoint.** All intelligence lives in OrchestratorAgent.

**Users type:** `/orchestrator task="..." mode=...`

**This command does:** Invoke OrchestratorAgent with arguments

**OrchestratorAgent does:** Everything else (analysis, routing, coordination)

**Result:** Clean separation of concerns, maintainable architecture
