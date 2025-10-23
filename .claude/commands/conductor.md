# Conductor Command - Complete Workflow Orchestration

**Arguments:** [mode=full-cycle|implementation-only|quality-gate] [issue=<number>] [branch=<name>]

**Description:** High-level workflow conductor that manages complete feature development from issue selection to PR merge. Orchestrates all specialized agents (architect, refactor, debugger, design, audit) through the orchestrator.

## Instructions

This command delegates to the Conductor Agent for complete workflow management.

### Parse Arguments

```bash
# Default mode
MODE="${1:-full-cycle}"
ISSUE_NUMBER="${2:-}"
BRANCH_NAME="${3:-}"

echo "🎼 CONDUCTOR WORKFLOW"
echo "===================="
echo "Mode: $MODE"
echo "Issue: ${ISSUE_NUMBER:-auto-select}"
echo "Branch: ${BRANCH_NAME:-auto-create}"
echo ""
```

### Validate Mode

```bash
case "$MODE" in
  full-cycle|implementation-only|quality-gate)
    echo "✅ Valid mode: $MODE"
    ;;
  *)
    echo "❌ Invalid mode: $MODE"
    echo "Valid modes: full-cycle, implementation-only, quality-gate"
    exit 1
    ;;
esac
```

### Build Conductor Prompt

```bash
CONDUCTOR_PROMPT="Execute $MODE workflow"

if [[ -n "$ISSUE_NUMBER" ]]; then
  CONDUCTOR_PROMPT="$CONDUCTOR_PROMPT for issue #$ISSUE_NUMBER"
fi

if [[ -n "$BRANCH_NAME" ]]; then
  CONDUCTOR_PROMPT="$CONDUCTOR_PROMPT using branch $BRANCH_NAME"
fi

echo "📋 Prompt: $CONDUCTOR_PROMPT"
echo ""
```

### Delegate to Conductor Agent

```bash
echo "🚀 Launching Conductor Agent..."
echo ""

# Use Task tool to invoke the Conductor Agent
# The agent will handle the complete workflow orchestration
```

Delegate to the Conductor Agent using the Task tool:

**Agent**: conductor
**Mode**: $MODE
**Context**:
- Issue number: $ISSUE_NUMBER (if provided)
- Branch name: $BRANCH_NAME (if provided)

**Prompt**:
```
$CONDUCTOR_PROMPT

You are conducting a complete development workflow. Follow your phase sequence:

1. **Planning Phase**: Issue selection, architecture review, research
2. **Implementation Phase**: Branch setup, coding, design review
3. **Quality Phase**: Testing, audit, refactoring, build validation
4. **Delivery Phase**: PR creation with proper issue linking, CI monitoring
5. **Reporting Phase**: Consolidated results and metrics

Use orchestrator for task routing, specialized agents for domain work, and commands for atomic operations.

Maintain workflow state and provide comprehensive final report.

Context:
- Mode: $MODE
- Issue: ${ISSUE_NUMBER:-auto-select from backlog}
- Branch: ${BRANCH_NAME:-auto-create from issue}
- Architecture: TribeVibe VSA, SOLID, contract-first
- Quality gates: Tests + Audit (≥8.0) + Build + Design (if UI)
- PR format: Use "Fixes #ISSUE_NUMBER" for auto-close

Begin conductor workflow now.
```

## Usage Examples

### Full Cycle Development

```bash
# Auto-select issue and run complete workflow
/conductor

# Specific issue with full workflow
/conductor full-cycle 123

# Full workflow with custom branch name
/conductor full-cycle 123 feature/user-preferences
```

### Implementation Only

```bash
# Continue work on existing branch
/conductor implementation-only "" feature/existing-work

# Implement specific issue on current branch
/conductor implementation-only 123
```

### Quality Gate Only

```bash
# Run quality validation on current branch
/conductor quality-gate

# Validate specific branch
/conductor quality-gate "" feature/to-validate
```

## Expected Outcomes

### Full Cycle Mode
- ✅ Issue selected from backlog
- ✅ Architecture plan validated
- ✅ Feature branch created
- ✅ Implementation complete
- ✅ All tests passing
- ✅ Audit score ≥ 8.0
- ✅ Build successful
- ✅ PR created with `Fixes #ISSUE` link
- ✅ CI passing
- ✅ Comprehensive report

### Implementation Only Mode
- ✅ Architecture reviewed
- ✅ Implementation complete on existing branch
- ✅ Quality gates passed
- ✅ PR created

### Quality Gate Mode
- ✅ Architecture audit complete
- ✅ Test coverage validated
- ✅ Audit score reported
- ✅ Build validated
- ✅ Design review (if UI changes)
- ✅ Quality report

## Integration with Agent System

**Architecture Position**:
```
User → /conductor command
         ↓
     Conductor Agent (workflow management)
         ↓
     Orchestrator Agent (task routing)
         ↓
   ┌──────────┬──────────┬──────────┬──────────┐
   ↓          ↓          ↓          ↓          ↓
Architect  Refactor  Debugger   Design     Audit
  Agent     Agent      Agent     Agent     Agent
```

**Key Benefits**:
- 🎯 **Single entry point** for complete workflows
- 🤖 **Intelligent coordination** via orchestrator
- 🔧 **Specialized expertise** from domain agents
- 📊 **Consolidated reporting** across all phases
- ⚡ **Efficient execution** with parallel operations
- 🛡️ **Quality assurance** at every phase

## Notes

- The conductor maintains workflow state for resumption
- All quality gates are mandatory and blocking
- PR body uses proper `Fixes #ISSUE` format for auto-close
- CI failures trigger automatic debugging and retry
- Final report includes metrics from all phases
- Failed workflows provide detailed error context

---

**Related Documentation**:
- Agent: `.claude/agents/conductor.md`
- Architecture: `docs/agents-architecture.md`
- Orchestrator: `.claude/agents/orchestrator.md`
