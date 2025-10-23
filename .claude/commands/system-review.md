# System Review - Agentic Workflow Meta-Validator

**Arguments:** [--scope=all|commands|agents|architecture|workflows] [--output=markdown|json] [--dry-run]

**Success Criteria:** Comprehensive validation report with ≥80% alignment score, actionable recommendations, no critical architecture violations

**Description:** Meta-validation entrypoint that delegates to SystemValidatorAgent for comprehensive agentic workflow system health checks.

---

## Purpose

Simple entrypoint command that delegates to the specialized **SystemValidatorAgent** for comprehensive meta-validation of the entire agentic workflow system.

Validates:
- ✅ Seamless development workflow (GitHub Issues → Branch → Debug → Test → Merge)
- ✅ Hub-and-spoke architecture (all coordination through orchestrator)
- ✅ Clean separation of concerns (commands are tools, agents are specialists)
- ✅ Standards compliance (DRY/SOLID, ≤10 steps per workflow)
- ✅ MCP integration consistency (Loki, Chrome DevTools, Seq)

---

## ⚠️ Important: Entrypoint Only

**This command is a simple entrypoint that delegates to SystemValidatorAgent:**
- ✅ Parses user arguments
- ✅ Delegates to SystemValidatorAgent via orchestrator
- ✅ Returns formatted report
- ❌ Does NOT contain validation logic (that's in the agent)
- ❌ Does NOT orchestrate other commands

**All validation intelligence lives in `.claude/agents/system-validator.md`**

---

## Workflow

### **Step 1: Parse Arguments**

```bash
# Default values
SCOPE="${1:-all}"
OUTPUT="${2:-markdown}"
DRY_RUN="${3:-false}"

echo "🔍 SYSTEM REVIEW - Meta-Validator"
echo "=================================="
echo ""
echo "Scope: $SCOPE"
echo "Output: $OUTPUT"
echo "Dry-Run: $DRY_RUN"
echo ""
```

### **Step 2: Delegate to SystemValidatorAgent**

**Use orchestrator to invoke SystemValidatorAgent:**

```bash
echo "Delegating to SystemValidatorAgent via orchestrator..."
echo ""

# Build task description
TASK="Perform comprehensive system validation with scope=$SCOPE, output=$OUTPUT"

if [[ "$DRY_RUN" == "true" ]]; then
    TASK="$TASK (dry-run mode - show what would be checked)"
fi

# Delegate to orchestrator which routes to SystemValidatorAgent
# Orchestrator will recognize this as a validation task and route appropriately
```

**Delegation call:**
```
SlashCommand "/orchestrator" "task='$TASK' mode=full agent=system-validator"
```

### **Step 3: Return Results**

The SystemValidatorAgent returns a comprehensive report which this command passes through to the user.

**Expected output:**
- Markdown report with alignment score
- Sections: ✅ Aligned, ⚠️ Misaligned, 💡 Recommendations
- Action items for improvement
- OR JSON report for CI integration

---

## Arguments

### `--scope` (optional)
Limit validation to specific area:
- `all` - Full system review (default)
- `commands` - Only validate slash commands
- `agents` - Only validate Agent SDK agents
- `architecture` - Only check architectural patterns
- `workflows` - Only simulate workflow patterns

### `--output` (optional)
Output format:
- `markdown` - Human-readable report (default)
- `json` - Machine-parseable JSON for CI integration

### `--dry-run` (optional)
Preview what would be checked without running validation:
- `false` - Run full validation (default)
- `true` - Show validation plan only

---

## Usage Examples

```bash
# Full system review (most common)
/system-review

# Quick architecture check
/system-review --scope=architecture

# Generate JSON for CI pipeline
/system-review --output=json

# Preview what will be checked
/system-review --dry-run

# Focus on command validation only
/system-review --scope=commands

# Validate agents only
/system-review --scope=agents
```

---

## Expected Outcomes

### ✅ **Excellent Alignment (≥80%)**
```
✅ SYSTEM ALIGNMENT: EXCELLENT
Alignment Score: 85% (17/20 checks passed)

All architectural patterns validated
No forbidden patterns detected
Complete documentation suite
MCP integration ready
Workflow simulations passed

Recommendation: System ready for production use
```

### ⚠️ **Good Alignment (60-79%)**
```
⚠️ SYSTEM ALIGNMENT: GOOD
Alignment Score: 72% (14/20 checks passed)

Most patterns validated
Minor documentation gaps
Some scope creep detected
MCP integration ready

Recommendation: Address medium-priority items before production
```

### ❌ **Needs Work (<60%)**
```
❌ SYSTEM ALIGNMENT: NEEDS WORK
Alignment Score: 45% (9/20 checks passed)

Significant architectural violations
Direct command-to-command calls found
Documentation incomplete
Separation of concerns unclear

Recommendation: Review and refactor before production
```

---

## Integration Points

This command is used by:
- **Developers** - Manual health checks (`/system-review`)
- **CI/CD Pipeline** - Automated validation (`/system-review --output=json`)
- **Post-Migration** - Validate Agent SDK migration success
- **Continuous Monitoring** - Detect architectural drift

**Orchestrator can also consult SystemValidatorAgent directly:**
- Before risky operations (pre-flight check)
- After major refactoring (validation)
- During issue pickup (health check)

---

## Relationship to SystemValidatorAgent

```
User: /system-review --scope=architecture
          ↓
This Command (entrypoint)
          ↓
/orchestrator (routing)
          ↓
SystemValidatorAgent (intelligence)
          ↓
Validation Report
```

**Division of Responsibility:**
- **This Command:** Argument parsing, user-facing interface
- **SystemValidatorAgent:** All validation logic, scoring, recommendations
- **Orchestrator:** Routing and session management

---

## Related Commands & Agents

**Commands:**
- `/test-command-architecture` - Validates specific architectural patterns
- `/test-slash-command-composition` - Tests SlashCommand tool functionality
- `/orchestrator` - Central hub for delegation

**Agents:**
- `SystemValidatorAgent` - The intelligence behind this command
- `OrchestratorAgent` - Routes validation requests
- `ArchitectAgent` - Validates VSA/SOLID compliance (complementary)

---

## Safety

- ⚠️ **Read-Only:** Never modifies code, commands, or configuration
- ✅ **Analysis Only:** Only reads, validates, and reports
- ✅ **Dry-Run Safe:** Can preview without execution
- ✅ **Non-Destructive:** Safe to run repeatedly

---

## Success Criteria

- [x] Simple entrypoint that delegates to agent
- [x] Clear argument parsing
- [x] Proper orchestrator delegation
- [x] Returns formatted report
- [x] No embedded validation logic (lives in agent)
- [x] Follows hub-and-spoke pattern

---

## Notes

- **Entrypoint Pattern:** Command → Orchestrator → Agent (proper delegation)
- **User-Facing:** Direct invocation via `/system-review`
- **Reusable:** Orchestrator can also consult SystemValidatorAgent directly
- **Separation:** UI (command) vs Intelligence (agent)

---

## Version History

- **v2.0** (2025-09-30): Refactored to hybrid approach (command + agent)
  - Simplified command to entrypoint only
  - Created SystemValidatorAgent with all validation logic
  - Follows hub-and-spoke pattern properly
- **v1.0** (2025-09-30): Initial monolithic implementation
  - All logic embedded in command (not scalable)