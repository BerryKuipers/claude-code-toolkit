# Audit - Comprehensive Code Audit Orchestration

**Arguments:** [--scope=whole|backend|frontend|db|<feature>] [--severity=critical|high|medium|low] [--skip=<types>] [--create-issues] [--output-format=markdown|json|both] [--verify-fixes]

**Success Criteria**: All audit types complete (or skipped), findings aggregated with severity prioritization, consolidated report generated

**Description:** Orchestrates comprehensive code audits (architecture, security, quality, design, tests, performance) by delegating to AuditAgent

---

## Purpose

This command provides a single entrypoint for comprehensive code quality audits across the TribeVibe codebase. It delegates to the AuditAgent for stateful orchestration and aggregation.

---

## ⚠️ Important: Workflow Scope

**This command is a workflow entrypoint that delegates to the AuditAgent:**
- ✅ Parses arguments and invokes AuditAgent
- ✅ Provides user-friendly interface for audit operations
- ❌ Does NOT perform audits inline (delegates to agent)
- ❌ Does NOT orchestrate other commands (agent responsibility)

---

## Workflow

### **Step 1: Parse Arguments**

```bash
# Extract audit configuration from arguments
AUDIT_SCOPE="${1:-whole}"
AUDIT_SEVERITY="${2:-high}"
AUDIT_SKIP="${3:-}"
CREATE_ISSUES="${4:-false}"
OUTPUT_FORMAT="${5:-markdown}"
VERIFY_FIXES="${6:-false}"

echo "🔍 Audit Configuration:"
echo "   Scope: $AUDIT_SCOPE"
echo "   Severity: $AUDIT_SEVERITY"
echo "   Skip: ${AUDIT_SKIP:-none}"
echo "   Create Issues: $CREATE_ISSUES"
echo "   Output Format: $OUTPUT_FORMAT"
echo "   Verify Fixes: $VERIFY_FIXES"
```

**Success Criteria**: Arguments parsed and validated

---

### **Step 2: Delegate to AuditAgent**

```typescript
console.log("✅ Delegating to AuditAgent [mode=full] via Task tool");
console.log("   Reason: Comprehensive audit orchestration requires stateful agent with multi-delegation");

// Delegate to audit agent
const auditResult = await Task({
  agent: "audit",
  context: {
    scope: AUDIT_SCOPE,
    severity: AUDIT_SEVERITY,
    skip: AUDIT_SKIP,
    createIssues: CREATE_ISSUES,
    outputFormat: OUTPUT_FORMAT,
    verifyFixes: VERIFY_FIXES
  }
});

console.log("   Result: Audit complete - " + auditResult.summary.totalFindings + " findings");
```

**Success Criteria**: AuditAgent completes orchestration, returns aggregated results

---

### **Step 3: Display Summary**

```bash
echo ""
echo "🔍 Comprehensive Audit Complete"
echo ""
echo "Session ID: ${auditResult.sessionId}"
echo "Scope: ${auditResult.scope}"
echo ""
echo "📊 Severity Breakdown:"
echo "  🔴 Critical: ${auditResult.summary.critical}"
echo "  🟠 High: ${auditResult.summary.high}"
echo "  🟡 Medium: ${auditResult.summary.medium}"
echo "  🟢 Low: ${auditResult.summary.low}"
echo ""
echo "💡 Recommendations:"
echo "  1. IMMEDIATE: Fix ${auditResult.summary.critical} critical findings"
echo "  2. THIS SPRINT: Resolve ${auditResult.summary.high} high-priority findings"
echo "  3. NEXT SPRINT: Address ${auditResult.summary.medium} medium-priority items"
echo ""
echo "📄 Full report: ${auditResult.reportPath}"

if [[ "${CREATE_ISSUES}" == "true" ]]; then
  echo ""
  echo "✅ GitHub issues created: ${auditResult.issuesCreated}"
fi
```

**Success Criteria**: User-friendly summary displayed with actionable next steps

---

## Arguments

### `--scope=<value>` (optional, default: "whole")
Scope of audit analysis (whole, backend, frontend, db, or specific feature)

### `--severity=<value>` (optional, default: "high")
Minimum severity level to report (critical, high, medium, low)

### `--skip=<types>` (optional)
Comma-separated list of audit types to skip (architecture, security, quality, tests, design, performance)

### `--create-issues` (optional, default: false)
Create GitHub issues for critical/high findings

### `--output-format=<value>` (optional, default: "markdown")
Output format for report (markdown, json, both)

### `--verify-fixes` (optional, default: false)
Compare with previous audit to verify fixes

---

## Usage Examples

```bash
# Comprehensive audit of entire codebase
/audit

# Backend-only audit
/audit --scope=backend

# Only critical findings
/audit --severity=critical

# Skip performance audit
/audit --skip=performance

# Create GitHub issues for findings
/audit --create-issues

# Pre-deployment audit
/audit --scope=whole --severity=high --create-issues --output-format=both

# Verify fixes after refactoring
/audit --verify-fixes
```

---

## Expected Outcomes

### ✅ Success
All audit types complete (or explicitly skipped), findings aggregated with severity breakdown, comprehensive report generated with actionable recommendations.

### ⚠️ Partial Success
Some audits fail or are skipped, but remaining audits provide useful findings. Report indicates which audits failed and why.

### ❌ Failure
Unable to run any audits due to system issues (packages not built, services not running, etc.). Error message indicates remediation steps.

---

## Integration Points

### OrchestratorAgent
Can be called by orchestrator for:
- Pre-deployment workflows
- PR review automation
- Post-refactoring validation
- Scheduled system health checks

### GitHub Workflows
CI/CD integration for automated audits:
```yaml
- name: Run Comprehensive Audit
  run: /audit --scope=whole --severity=high --output-format=json
```

### Pre-Commit Hooks
Quick audit before commits:
```bash
npm run audit:pre-commit  # Uses /audit with focused scope
```

---

## Safety

- ⚠️ Analysis ONLY - no code modifications
- ✅ Safe to run on any branch
- ✅ Safe to run multiple times
- ✅ Session-based - results tracked for comparison

---

## Success Criteria

- [x] Arguments parsed correctly
- [x] AuditAgent invoked with proper context
- [x] Findings aggregated with severity prioritization
- [x] Comprehensive report generated
- [x] User-friendly summary displayed
- [x] GitHub issues created (if enabled)

---

## Related Commands & Agents

**Commands:**
- `/architect` - Architecture-only audit
- `/design-review` - Design system audit
- `/issue-create` - GitHub issue creation

**Agents:**
- AuditAgent - Comprehensive audit orchestration
- ArchitectAgent - Architectural validation
- DesignAgent - Design system analysis

---

## Notes

- **Session State**: Each audit creates a session in `.claude/audit-results/` for tracking and comparison
- **Incremental Audits**: Use `--scope` to focus on specific areas for faster feedback
- **Verification**: Use `--verify-fixes` to compare with previous audit and track improvements
- **CI/CD Integration**: Use `--output-format=json` for automated processing in pipelines
- **Issue Tracking**: Use `--create-issues` to automatically create GitHub issues for critical/high findings

**Best Practice**: Run `/audit` before creating PRs, after major refactoring, and as part of pre-deployment checks.