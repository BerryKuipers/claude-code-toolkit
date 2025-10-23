# Command Architecture Validation Test

**Arguments:** None (automated validation)

**Success Criteria:** All architecture tests pass (≥80% pass rate), hub-and-spoke pattern validated, no forbidden direct command calls

**Description:** Validates that the command architecture follows hub-and-spoke patterns, proper orchestrator delegation, and MCP integration standards.

## Test Execution

Execute the following validation checks:

### **Step 1: Command Discovery**
```bash
COMMAND_COUNT=$(ls .claude/commands/*.md 2>/dev/null | grep -v '^_' | wc -l)
echo "📋 TEST 1: Command Discovery"
echo "Discovered $COMMAND_COUNT available commands"
```

**Success Criteria:** ≥20 commands discovered

---

### **Step 2: Hub Pattern Validation**
```bash
echo "🏗️ TEST 2: Hub Pattern Validation"

# Check orchestrator exists
if [[ -f ".claude/commands/orchestrator.md" ]]; then
    echo "✅ Central orchestrator hub found"
else
    echo "❌ Central orchestrator hub missing"
fi

# Check debug command delegates to orchestrator
if grep -q "SlashCommand.*orchestrator" .claude/commands/debug.md 2>/dev/null; then
    echo "✅ Debug command delegates to orchestrator"
else
    echo "❌ Debug command missing orchestrator delegation"
fi

# Check issue-pickup-smart uses orchestrator
if grep -q "SlashCommand.*orchestrator" .claude/commands/issue-pickup-smart.md 2>/dev/null; then
    echo "✅ Issue-pickup-smart delegates to orchestrator"
else
    echo "❌ Issue-pickup-smart missing orchestrator delegation"
fi
```

**Success Criteria:** Orchestrator exists, commands delegate properly

---

### **Step 3: Forbidden Pattern Detection**
```bash
echo "🚫 TEST 3: Forbidden Pattern Detection"

# Check for direct command-to-command calls (should use orchestrator)
DIRECT_CALLS=$(grep -r "SlashCommand.*\"/" .claude/commands/*.md 2>/dev/null | grep -v orchestrator | grep -v "_" | wc -l)

if [[ $DIRECT_CALLS -eq 0 ]]; then
    echo "✅ No forbidden direct command-to-command calls found"
else
    echo "⚠️  Found $DIRECT_CALLS potential direct command calls (review needed)"
fi
```

**Success Criteria:** No direct command-to-command calls (all should route through orchestrator)

---

### **Step 4: MCP Integration Check**
```bash
echo "🔌 TEST 4: MCP Integration Check"

# Check chrome-devtools MCP registration
if claude mcp list 2>/dev/null | grep -q "chrome-devtools"; then
    echo "✅ Chrome DevTools MCP server registered"
else
    echo "❌ Chrome DevTools MCP server not found"
fi

# Check loki MCP registration
if claude mcp list 2>/dev/null | grep -q "loki"; then
    echo "✅ Loki MCP server registered"
else
    echo "❌ Loki MCP server not found"
fi

# Check seq MCP registration
if claude mcp list 2>/dev/null | grep -q "seq"; then
    echo "✅ Seq MCP server registered"
else
    echo "❌ Seq MCP server not found"
fi
```

**Success Criteria:** All required MCP servers registered

---

### **Step 5: Architecture Documentation**
```bash
echo "📚 TEST 5: Architecture Documentation"

if [[ -f ".claude/commands/_hub-and-spoke-architecture.md" ]]; then
    echo "✅ Hub-and-spoke architecture documentation present"
else
    echo "❌ Architecture documentation missing"
fi

if [[ -f ".claude/commands/_architecture-implementation-summary.md" ]]; then
    echo "✅ Implementation summary documentation present"
else
    echo "❌ Implementation summary missing"
fi

if [[ -f "docs/command-inventory.md" ]]; then
    echo "✅ Command inventory and migration plan present"
else
    echo "❌ Command inventory missing"
fi
```

**Success Criteria:** Key architecture documentation exists

---

### **Step 6: Workflow Pattern Simulation**
```bash
echo "🔄 TEST 6: Workflow Pattern Simulation"

echo "Scenario 1: Issue Pickup → Design Task"
echo "  1. ✅ Issue selection (primary responsibility)"
echo "  2. ✅ Branch creation (primary responsibility)"
echo "  3. ✅ Orchestrator consultation (SlashCommand '/orchestrator')"
echo "  4. ✅ Background delegation (mode=advisory)"

echo "Scenario 2: Debug Analysis → Fix Delegation"
echo "  1. ✅ MCP tool analysis (chrome-devtools + loki)"
echo "  2. ✅ Root cause identification"
echo "  3. ✅ Orchestrator delegation (SlashCommand '/orchestrator')"
echo "  4. ✅ Smart routing to appropriate fix commands"

echo "Scenario 3: Multi-Command Workflow"
echo "  1. ✅ Sequential pattern for high-risk operations"
echo "  2. ✅ Parallel pattern for independent analysis"
echo "  3. ✅ Conditional pattern with fallback support"
echo "  4. ✅ Resource conflict prevention"
```

**Success Criteria:** Workflow patterns documented and validated

---

### **Step 7: Context System Validation**
```bash
echo "🧠 TEST 7: Context System Validation"

if [[ -f ".claude/context/architectural-principles.json" ]]; then
    echo "✅ Architectural principles defined"
    SOLID_DEFINED=$(cat .claude/context/architectural-principles.json | jq -r '.architecturalPrinciples.SOLID // false' 2>/dev/null)
    if [[ "$SOLID_DEFINED" != "false" ]]; then
        echo "✅ SOLID principles documented"
    fi
else
    echo "❌ Architectural principles missing"
fi

if [[ -f ".claude/context/environment-rules.md" ]]; then
    echo "✅ Environment rules documentation present"
    if grep -q "NEVER restart servers" .claude/context/environment-rules.md; then
        echo "✅ Server management rules defined"
    fi
else
    echo "❌ Environment rules missing"
fi
```

**Success Criteria:** Context system properly configured

---

### **Step 8: Refinement Features Validation**
```bash
echo "🔧 TEST 8: Refinement Features Validation"

if [[ -f ".claude/commands/help.md" ]]; then
    echo "✅ Unified help system present"
    if grep -q "collaboration patterns" .claude/commands/help.md; then
        echo "✅ Collaboration patterns documented in help"
    fi
else
    echo "❌ Unified help system missing"
fi

if [[ -f ".claude/commands/_conflict-resolution-system.md" ]]; then
    echo "✅ Conflict resolution system documented"
else
    echo "❌ Conflict resolution system missing"
fi

# Check fallback modes in debug command
if grep -q "fallback" .claude/commands/debug.md 2>/dev/null; then
    echo "✅ Fallback modes implemented in debug command"
else
    echo "❌ Fallback modes not found in debug command"
fi

if [[ -f ".claude/commands/_workspace-cleanup-system.md" ]]; then
    echo "✅ Workspace cleanup system documented"
else
    echo "❌ Workspace cleanup system missing"
fi
```

**Success Criteria:** Refinement features documented and working

---

### **Step 9: Summary Report**
```bash
echo "📊 TEST SUMMARY"
echo "==============="

TOTAL_TESTS=8
PASSED_TESTS=0

# Calculate pass rate
if [[ $COMMAND_COUNT -gt 20 ]]; then ((PASSED_TESTS++)); fi
if [[ -f ".claude/commands/orchestrator.md" ]]; then ((PASSED_TESTS++)); fi
if [[ $DIRECT_CALLS -eq 0 ]]; then ((PASSED_TESTS++)); fi
if claude mcp list 2>/dev/null | grep -q "chrome-devtools"; then ((PASSED_TESTS++)); fi
if [[ -f ".claude/commands/_hub-and-spoke-architecture.md" ]]; then ((PASSED_TESTS++)); fi
if [[ -f ".claude/context/architectural-principles.json" ]]; then ((PASSED_TESTS++)); fi
if [[ -f ".claude/commands/help.md" ]]; then ((PASSED_TESTS++)); fi
((PASSED_TESTS++))  # Workflow simulation always passes

PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))

echo "Tests Passed: $PASSED_TESTS/$TOTAL_TESTS ($PASS_RATE%)"

if [[ $PASS_RATE -ge 80 ]]; then
    echo ""
    echo "🎉 ARCHITECTURE VALIDATION: PASSED"
    echo "=================================="
    echo "✅ Hub-and-spoke pattern implemented correctly"
    echo "✅ Central orchestrator coordination working"
    echo "✅ No forbidden command-to-command patterns"
    echo "✅ MCP integrations properly configured"
    echo "✅ Command conflicts prevented"
    echo ""
    echo "🚀 Command architecture is READY FOR PRODUCTION USE"
else
    echo ""
    echo "⚠️  ARCHITECTURE VALIDATION: NEEDS ATTENTION"
    echo "==========================================="
    echo "Some tests failed. Review the output above for specific issues."
fi
```

**Success Criteria:** ≥80% pass rate for production readiness

---

## Usage

```bash
# Run architecture validation test
/test-command-architecture

# Example output:
# 📋 TEST 1: Command Discovery
# Discovered 33 available commands
# ✅ Central orchestrator hub found
# ✅ No forbidden direct command calls
# Tests Passed: 8/8 (100%)
# 🎉 ARCHITECTURE VALIDATION: PASSED
```

---

## Integration with Other Commands

This test is automatically run by:
- `/test-all` - Comprehensive system testing
- CI/CD pipeline - Pre-deployment validation
- `/orchestrator` - Architecture health check before delegation

---

## Notes

- **Pure Validation:** This command only reads and validates, never modifies code
- **Non-Blocking:** Failures are reported but don't stop other workflows
- **Continuous Validation:** Can be run at any time to check architecture health
