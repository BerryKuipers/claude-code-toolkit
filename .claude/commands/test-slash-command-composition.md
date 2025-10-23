# SlashCommand Tool Composition Test

**Arguments:** None

**Success Criteria:** Successfully invoke another slash command using the SlashCommand tool, verify composition works

**Description:** Tests whether the SlashCommand tool can invoke other slash commands from within commands/agents. Critical for orchestrator delegation patterns.

## Purpose

This test validates that:
1. SlashCommand tool is available in this Claude Code environment
2. It can successfully invoke other commands
3. Results are returned correctly
4. Fallback handling works if tool is unavailable

## Test Execution

### **Step 1: Environment Check**

```bash
echo "🧪 SLASHCOMMAND TOOL COMPOSITION TEST"
echo "===================================="
echo ""
echo "Testing if SlashCommand tool can invoke other commands..."
```

### **Step 2: Test Simple Command Invocation**

**Attempt to invoke `/help` command via SlashCommand tool:**

The SlashCommand tool should be used by Claude Code (not bash) to invoke the help command.

**Expected behavior:**
- If SlashCommand tool is available: Successfully invokes `/help` and returns its output
- If SlashCommand tool is unavailable: Falls back to prompt-level delegation

**Test code (for Claude Code to execute):**
```typescript
// This is pseudocode showing what Claude Code should do
try {
  const result = await SlashCommand("/help");
  console.log("✅ SlashCommand tool SUCCESS");
  console.log("Result:", result);
  return { ok: true, method: "slash-command-tool", result };
} catch (error) {
  console.log("⚠️  SlashCommand tool UNAVAILABLE");
  console.log("Error:", error.message);
  return { ok: false, method: "unavailable", error: error.message };
}
```

### **Step 3: Test Command with Arguments**

**Attempt to invoke a command with arguments:**

Try invoking `/test:command-architecture` to verify argument passing works.

**Expected behavior:**
- Arguments are properly passed to the invoked command
- Results include output from the invoked command

### **Step 4: Test Fallback Scenario**

**Simulate SlashCommand tool unavailability:**

If SlashCommand tool is not available, test fallback strategy:
1. Log clear warning about degraded mode
2. Use prompt-level delegation (ask main agent to run command)
3. Return results with `degraded: true` flag

**Fallback pseudocode:**
```typescript
// Fallback approach
console.log("⚠️  Using FALLBACK: Prompt-level delegation");
const result = await promptLevelInvocation("/help");
return { ok: true, method: "prompt-fallback", degraded: true, result };
```

### **Step 5: Report Test Results**

**Format test results:**

```markdown
## 🧪 SlashCommand Tool Test Results

### Test 1: Simple Command Invocation
**Command**: `/help`
**Status**: ✅ SUCCESS / ❌ FAILED
**Method**: slash-command-tool / prompt-fallback / unavailable
**Output**: [command output or error message]

### Test 2: Command with Arguments
**Command**: `/test:command-architecture`
**Status**: ✅ SUCCESS / ❌ FAILED
**Method**: slash-command-tool / prompt-fallback / unavailable
**Output**: [command output or error message]

### Test 3: Fallback Handling
**Scenario**: SlashCommand tool unavailable
**Status**: ✅ HANDLED / ❌ FAILED
**Fallback**: prompt-level delegation
**Degraded Mode**: [true/false]

## Summary

**Overall Status**: ✅ PASS / ⚠️  DEGRADED / ❌ FAIL

**SlashCommand Tool**: Available / Unavailable
**Fallback Strategy**: Working / Not Working
**Recommendation**:
- If PASS: SlashCommand tool composition verified, safe to use in orchestrator
- If DEGRADED: Tool unavailable, use fallback mode with degraded flag
- If FAIL: Do not use SlashCommand tool, investigate issue

## Configuration Recommendation

Based on test results, update `.claude/config.yml`:

```yaml
delegation:
  useSlashCommandTool: [true/false]  # Based on test results
  degradedFallback: true              # Always enable fallback
  retryMs: 3000
  maxRetries: 1
```
```

---

## Integration Points

This test is used by:
- **Orchestrator Agent**: Pre-flight check before delegation
- **Phase 3 Migration**: Validates SlashCommand composition before relying on it
- **CI/CD**: Can be run as part of command architecture validation

---

## Expected Outcomes

### ✅ **Best Case**: SlashCommand Tool Available
```
Test 1: ✅ SUCCESS (slash-command-tool)
Test 2: ✅ SUCCESS (slash-command-tool)
Test 3: ✅ HANDLED (fallback works if forced)

Recommendation: Use SlashCommand tool for all delegations
Config: useSlashCommandTool: true
```

### ⚠️  **Degraded Case**: SlashCommand Tool Unavailable
```
Test 1: ⚠️  DEGRADED (prompt-fallback)
Test 2: ⚠️  DEGRADED (prompt-fallback)
Test 3: ✅ HANDLED (fallback strategy working)

Recommendation: Use fallback mode, mark outputs as degraded
Config: useSlashCommandTool: false, degradedFallback: true
```

### ❌ **Failure Case**: No Composition Support
```
Test 1: ❌ FAILED (unavailable)
Test 2: ❌ FAILED (unavailable)
Test 3: ❌ FAILED (no fallback)

Recommendation: Do not use delegation, refactor to direct execution
Config: useSlashCommandTool: false, degradedFallback: false
```

---

## Notes

- This test is **non-destructive** (only reads, never modifies)
- Safe to run multiple times
- Results inform orchestrator delegation strategy
- Critical for Phase 3 migration success
