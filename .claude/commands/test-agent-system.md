# Test Agent System - Simple Agent Invocation Test

**Arguments:** [agent=orchestrator|architect|agent-creator|system-validator]

**Success Criteria:** Successfully invokes specified agent and receives structured response

**Description:** Simple test command to verify agent system is working by invoking an agent with a test task.

---

## Purpose

Quick smoke test to verify:
- ✅ Agent SDK is properly loaded
- ✅ Agents can be invoked via SlashCommand tool
- ✅ Agents return structured responses
- ✅ Integration between command → orchestrator → agent works

---

## Usage

```bash
# Test orchestrator agent (default)
/test-agent-system

# Test specific agent
/test-agent-system agent=architect
/test-agent-system agent=agent-creator
/test-agent-system agent=system-validator
```

---

## Workflow

### **Step 1: Parse Arguments**

```bash
AGENT="${1:-orchestrator}"

echo "🧪 AGENT SYSTEM TEST"
echo "==================="
echo ""
echo "Testing agent: $AGENT"
echo ""
```

---

### **Step 2: Prepare Test Task**

Different test tasks for each agent:

```bash
case "$AGENT" in
  orchestrator)
    TASK="Analyze this simple test task: 'check if package.json exists and list its dependencies'. Categorize the task type and recommend which command should handle it."
    ;;
  architect)
    TASK="Perform a quick architectural review of the logger package at packages/logger/src/index.ts. Check if it follows SOLID principles and report any findings."
    ;;
  agent-creator)
    TASK="Classify this capability: 'list all running docker containers'. Should this be a tool, workflow, or agent? Provide reasoning."
    ;;
  system-validator)
    TASK="Perform Phase 1 only (System Discovery): inventory commands and agents, report counts."
    ;;
  *)
    echo "❌ Unknown agent: $AGENT"
    echo "Valid options: orchestrator, architect, agent-creator, system-validator"
    exit 1
    ;;
esac

echo "📋 Test Task:"
echo "$TASK"
echo ""
```

---

### **Step 3: Invoke Agent via Orchestrator**

```bash
echo "🚀 Invoking ${AGENT} agent..."
echo ""

# Use SlashCommand tool to invoke orchestrator with specific agent
SlashCommand "/orchestrator" "task='$TASK' mode=full agent=$AGENT"
```

---

### **Step 4: Report Results**

```bash
echo ""
echo "✅ Agent invocation completed"
echo ""
echo "📊 Expected Response:"
case "$AGENT" in
  orchestrator)
    echo "  - Task categorization"
    echo "  - Recommended command/agent"
    echo "  - Routing logic explanation"
    ;;
  architect)
    echo "  - Architectural findings (if any)"
    echo "  - SOLID principle violations (if any)"
    echo "  - Recommendations"
    ;;
  agent-creator)
    echo "  - Classification: TOOL/WORKFLOW/AGENT"
    echo "  - Reasoning for classification"
    echo "  - Recommended structure"
    ;;
  system-validator)
    echo "  - Command count"
    echo "  - Agent count"
    echo "  - Discovery summary"
    ;;
esac

echo ""
echo "🎯 If you see structured output above, the agent system is working!"
```

---

## Expected Output Examples

### Orchestrator Test
```
Task Analysis:
- Category: SYSTEM_INSPECTION
- Complexity: Low
- Recommended: File inspection tool or simple bash command
- Routing: No agent needed, direct bash execution sufficient
```

### Architect Test
```
Architectural Review: packages/logger/src/index.ts

✅ Aligned:
- Single Responsibility: Logger handles only logging concerns
- Dependency Inversion: Uses interfaces for PropertyEntity

⚠️ Potential Issues:
- None found (small, focused module)

Recommendations:
- Structure is sound
- Follows TribeVibe patterns
```

### Agent-Creator Test
```
Classification: TOOL

Reasoning:
- Narrow scope (single check)
- Atomic operation (one command)
- No multi-step coordination needed
- No stateful orchestration

Recommended Structure:
- Type: Command (.md file)
- Location: .claude/commands/list-docker-containers.md
- Implementation: Single bash command: docker ps
```

### System-Validator Test
```
Phase 1: System Discovery

Commands: 45 discovered
Agents: 7 discovered
Config: .claude/config.yml present

Summary:
✅ System properly structured
✅ Hub-and-spoke architecture detected
✅ No forbidden patterns found
```

---

## Success Criteria

**✅ PASS if:**
- Agent invoked successfully
- Structured response received
- Response matches expected format
- No errors or timeouts

**❌ FAIL if:**
- Command not recognized
- Agent not found
- SlashCommand tool fails
- Timeout or error

---

## Troubleshooting

### "Unknown slash command: test-agent-system"
- **Cause**: Command not discovered yet
- **Fix**: Restart Claude Code session

### "Unknown slash command: orchestrator"
- **Cause**: Orchestrator command not loaded
- **Fix**: Verify `.claude/commands/orchestrator.md` exists, restart session

### "Agent not found: [agent-name]"
- **Cause**: Agent file missing or malformed
- **Fix**: Check `.claude/agents/[agent-name].md` has proper YAML frontmatter

### "SlashCommand tool not available"
- **Cause**: Tool not enabled or version issue
- **Fix**: Check `.claude/config.yml` has `useSlashCommandTool: true`

---

## Integration with Test Plan

This command is referenced in:
- **temp/agent-system-test-plan.md** - Test Suite 3: Agent System Validation
- Run this before comprehensive testing to ensure basic agent invocation works

---

**Quick Test:** Just run `/test-agent-system` - if you get structured output, the system works! 🎉