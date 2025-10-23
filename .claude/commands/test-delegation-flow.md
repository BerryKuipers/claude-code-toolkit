---
name: test-delegation-flow
description: Test agentic workflow delegation chain to verify agents properly delegate instead of doing all work themselves
arguments:
  - name: workflow
    description: Which workflow to test (conductor, orchestrator, audit)
    required: true
  - name: trigger
    description: Test trigger phrase to invoke the workflow
    required: false
---

# Delegation Flow Test

**Purpose**: Validate that agents properly delegate work to specialized agents instead of doing everything themselves.

## Problem Statement

Agents (especially conductor) sometimes do all the work themselves instead of delegating:
- ❌ Conductor reads files, implements features, runs tests all itself
- ❌ No delegation to architect, design, implementation agents
- ❌ Single agent "busy for quite a while" doing everything

**Expected behavior:**
- ✅ Conductor delegates to architect for validation
- ✅ Conductor delegates to design for UX improvements
- ✅ Conductor delegates to implementation for code changes
- ✅ Conductor delegates to audit for quality checks
- ✅ Each agent stays focused on its specialty

## Test Approach

### Step 1: Parse Workflow to Test

```bash
WORKFLOW="${workflow:-conductor}"
echo "🧪 Testing delegation flow for: $WORKFLOW"
```

### Step 2: Define Test Trigger

**Default test triggers:**
- **Conductor**: `"Complete dark mode feature workflow for issue #137"`
- **Orchestrator**: `"Implement user settings feature"`
- **Audit**: `"Audit code quality for profile service"`

```bash
if [ -z "$trigger" ]; then
    case $WORKFLOW in
        conductor)
            TRIGGER="Test delegation by implementing a simple settings toggle feature"
            ;;
        orchestrator)
            TRIGGER="Route task: add logging to authentication service"
            ;;
        audit)
            TRIGGER="Audit backend architecture for VSA compliance"
            ;;
    esac
else
    TRIGGER="$trigger"
fi

echo "Trigger phrase: $TRIGGER"
```

### Step 3: Monitor Agent Invocations

**What we're looking for:**

Create a marker file to track delegation:
```bash
mkdir -p .claude/test-results
DELEGATION_LOG=".claude/test-results/delegation-flow-$(date +%s).log"

echo "📊 Delegation Flow Test - $(date)" > "$DELEGATION_LOG"
echo "Workflow: $WORKFLOW" >> "$DELEGATION_LOG"
echo "Trigger: $TRIGGER" >> "$DELEGATION_LOG"
echo "" >> "$DELEGATION_LOG"
echo "Expected Delegations:" >> "$DELEGATION_LOG"

case $WORKFLOW in
    conductor)
        echo "  1. ✅ Should delegate to architect agent for validation" >> "$DELEGATION_LOG"
        echo "  2. ✅ Should delegate to design agent for UX (if applicable)" >> "$DELEGATION_LOG"
        echo "  3. ✅ Should delegate to implementation agent for code" >> "$DELEGATION_LOG"
        echo "  4. ✅ Should delegate to audit agent for quality checks" >> "$DELEGATION_LOG"
        echo "  5. ❌ Should NOT read/write code files directly" >> "$DELEGATION_LOG"
        ;;
    orchestrator)
        echo "  1. ✅ Should route to appropriate agent based on task type" >> "$DELEGATION_LOG"
        echo "  2. ✅ Should aggregate results from delegated agent" >> "$DELEGATION_LOG"
        echo "  3. ❌ Should NOT execute task itself" >> "$DELEGATION_LOG"
        ;;
    audit)
        echo "  1. ✅ Should delegate to architect agent for architecture audit" >> "$DELEGATION_LOG"
        echo "  2. ✅ Should delegate to design agent for design audit" >> "$DELEGATION_LOG"
        echo "  3. ✅ Should run npm scripts for automated checks" >> "$DELEGATION_LOG"
        echo "  4. ❌ Should NOT modify code (analysis only)" >> "$DELEGATION_LOG"
        ;;
esac
```

### Step 4: Invoke Workflow (Instrumented)

**Inform user about the test:**
```
🧪 Delegation Flow Test Started

Testing: ${WORKFLOW} workflow
Trigger: ${TRIGGER}

Expected behavior:
- ${WORKFLOW} should delegate to specialized agents
- Each agent should handle its specific responsibility
- No single agent should do all the work

Monitoring delegation chain...
```

**Invoke the workflow:**

For conductor:
```bash
if [ "$WORKFLOW" = "conductor" ]; then
    echo "" >> "$DELEGATION_LOG"
    echo "=== INVOKING CONDUCTOR ===" >> "$DELEGATION_LOG"
    echo "Command: conductor(${TRIGGER})" >> "$DELEGATION_LOG"
    echo "" >> "$DELEGATION_LOG"

    # User should manually invoke: conductor full-cycle issue=137
    # We can't directly invoke agents from commands, so we instruct
    echo "▶️  Please invoke manually: conductor full-cycle issue=137"
    echo "   (or your test trigger phrase)"
fi
```

### Step 5: Analyze Delegation Pattern

**After workflow completes, user reports back what happened:**

Create analysis template:
```bash
cat << 'EOF' >> "$DELEGATION_LOG"

=== DELEGATION ANALYSIS ===

Instructions for user:
After running the workflow, fill in this section:

1. Which agents were invoked? (List all)
   - [ ] architect
   - [ ] design
   - [ ] implementation
   - [ ] audit
   - [ ] researcher
   - [ ] debugger
   - [ ] refactor

2. Did the primary agent delegate or do work itself?
   - [ ] Properly delegated to specialized agents
   - [ ] Did most/all work itself (VIOLATION)

3. Evidence of delegation:
   - Look for phrases like "I need the [agent] agent to..."
   - Look for agent-to-agent communication
   - Check if conductor/orchestrator just ran tools directly

4. Validation:
   - [ ] Each agent stayed in its specialty
   - [ ] No single agent did everything
   - [ ] Proper delegation chain observed

5. Issues found:
   - List any violations or unexpected behavior

EOF

echo "📋 Delegation analysis template created: $DELEGATION_LOG"
```

### Step 6: Report Results

```bash
echo ""
echo "✅ Delegation Flow Test Setup Complete"
echo ""
echo "📊 Test Log: $DELEGATION_LOG"
echo ""
echo "🎯 Next Steps:"
echo "  1. Run the workflow with your trigger"
echo "  2. Observe which agents are invoked"
echo "  3. Fill in the analysis template"
echo "  4. Review for proper delegation patterns"
echo ""
echo "💡 Proper Delegation Indicators:"
echo "  ✅ See 'I need the [agent] agent to...' in output"
echo "  ✅ Multiple agents involved, each handling specialty"
echo "  ✅ Primary agent orchestrates, doesn't execute"
echo ""
echo "❌ Delegation Violations:"
echo "  ⚠️  Primary agent reads/writes files directly"
echo "  ⚠️  Only one agent active for long periods"
echo "  ⚠️  No agent-to-agent delegation visible"
echo ""
```

## Expected Output Format

**Good Delegation Chain (Example):**
```
🎯 Phase 1: Architecture Validation
→ Consulting architect agent...
● architect(Validate architecture for issue #137)
  ✓ VSA compliance: PASS
  ✓ Layer boundaries: PASS

🎯 Phase 2: Implementation
→ Delegating to implementation agent...
● implementation(Implement user settings toggle)
  ✓ Backend changes: 3 files
  ✓ Frontend changes: 2 files

🎯 Phase 3: Quality Assurance
→ Consulting audit agent...
● audit(Quality check for issue #137)
  ✓ Audit score: 8.5/10
```

**Bad Pattern (Violation):**
```
🎯 Phase 1: Architecture Validation
→ Validating architecture...
● conductor(busy)
  ⎿ Read(services/api/src/features/user/UserController.ts)
  ⎿ Read(services/api/src/features/user/UserService.ts)
  ⎿ Grep(pattern="class.*Controller")
  ⎿ [Conductor doing all the work itself - VIOLATION]
```

## Validation Criteria

### ✅ PASS Criteria:
1. At least 2 different agents invoked for multi-step workflows
2. Primary agent (conductor/orchestrator) delegates, doesn't execute
3. Each agent handles only its specialty (architect=architecture, design=UX, etc.)
4. Clear delegation language visible: "I need the [agent] agent to..."

### ❌ FAIL Criteria:
1. Only one agent active for entire workflow
2. Primary agent reads/writes files directly instead of delegating
3. No delegation phrases visible in output
4. Single agent "busy for quite a while" doing everything

## Integration with CI/CD

Future enhancement: Automated delegation flow testing in CI pipeline:
```bash
# Could parse agent logs to detect delegation patterns
# Fail PR if conductor/orchestrator does work itself
# Validate agent specialization boundaries
```

## Related Documentation

- **Agent Delegation Pattern**: `.claude/commands/docs/agent-delegation-pattern.md`
- **Conductor Agent**: `.claude/agents/conductor.md`
- **Orchestrator Agent**: `.claude/agents/orchestrator.md`

---

**Usage:**
```bash
/test-delegation-flow workflow=conductor
/test-delegation-flow workflow=orchestrator trigger="implement user preferences"
/test-delegation-flow workflow=audit
```
