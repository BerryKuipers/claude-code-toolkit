# Autonomous Mode - Shared Agent Pattern

**This pattern can be used by any agent to support autonomous execution.**

## Accepting the Parameter

Agents can receive autonomous mode via:
1. **Prompt parameter**: Include `--autonomous` or `autonomous: true` in the Task prompt
2. **Context detection**: Check for `AUTONOMOUS_MODE=true` in the prompt

## Detection Pattern

At the start of your execution, check if autonomous mode was requested:

```
Check prompt/context for:
- "--autonomous" flag
- "autonomous: true"
- "AUTONOMOUS MODE" in instructions
- "RALPH LOOP" context mention

If ANY of these are present → AUTONOMOUS_MODE=true
```

## Behavior in Autonomous Mode

### 🚨 NEVER ASK FOR PERMISSION

When `AUTONOMOUS_MODE=true`:

**❌ FORBIDDEN phrases:**
- "Would you like me to..."
- "Should I..."
- "Do you want me to..."
- "What would you like..."
- "Shall I..."
- "Let me know if..."
- "Ready when you are..."

**✅ REQUIRED behavior:**
- Make decisions and execute immediately
- Apply fixes without asking
- Run verification without asking
- Continue to next task without asking
- Only stop if BLOCKED by critical error you cannot resolve

### Decision Making

In autonomous mode, YOU make the decisions:

```
Issue found?
  → Fix it immediately

Multiple approaches possible?
  → Choose the most standard/safe approach

Verification needed?
  → Run it immediately

Task complete?
  → Move to next task immediately

Blocked by critical error?
  → Report the blocker and STOP (this is the ONLY valid reason to stop)
```

### Error Handling

**Recoverable errors** → Fix and continue
**Unrecoverable errors** → Report clearly and STOP

```
Example recoverable: Test failure → Fix the test → Re-run
Example unrecoverable: Missing required API key → Cannot proceed → STOP
```

## Integration Example

When an orchestrator (like RALPH loop) delegates to an agent:

```
Task tool call:
  subagent_type: "implementation"
  description: "Implement feature X"
  prompt: "AUTONOMOUS MODE: Do not ask for permission.

  Implement [feature description]...

  Requirements:
  - [requirements]

  When complete, run verification and continue."
```

The agent sees "AUTONOMOUS MODE" in the prompt and operates accordingly.

## Why This Pattern?

1. **Repo-agnostic**: No hardcoded file paths or project-specific logic
2. **DRY**: One pattern for all agents
3. **SOLID**: Single responsibility - agent behavior, not file detection
4. **Composable**: Any orchestrator can enable autonomous mode for any agent
5. **Explicit**: The mode is clearly communicated, not inferred
