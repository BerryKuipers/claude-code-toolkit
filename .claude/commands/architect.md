# TribeVibe Architecture Review Command

**Arguments:** --scope=<whole|backend|frontend|db> --include-docs=<true|false> --include-db=<true|false> --severity=<critical|all> --create-issues=<true|false>

**Success Criteria:** Comprehensive architectural analysis report with severity-grouped findings

**Description:** Analysis-only architectural review tool that validates TribeVibe's adherence to contract-first, vertical slice, SOLID, and DRY principles. Produces structured reports for actionable improvements.

---

## ⚠️ Important: Analysis Tool Only

**This command performs ANALYSIS ONLY** - it does NOT orchestrate other commands.

**Scope:**
- ✅ Read codebase and documentation
- ✅ Validate architectural principles
- ✅ Generate findings report
- ✅ Optionally create GitHub issues via `/issue-create`
- ❌ Does NOT orchestrate other commands
- ❌ Does NOT modify code

**Intended to be called by:** OrchestratorAgent, workflows, or direct user invocation

---

## Core Capabilities

- **VSA Compliance**: Validate Vertical Slice Architecture patterns
- **SOLID Principles**: Enforce Single Responsibility, Open/Closed, etc.
- **Layer Boundaries**: Check Controller → Service → Repository separation
- **Contract-First**: Validate TypeScript interfaces defined before implementation
- **DRY Analysis**: Identify code duplication
- **Documentation Cross-Check**: Compare docs vs. actual implementation
- **Database Review**: Migration safety, schema consistency

---

## Usage

```bash
# Full architectural review
/architect

# Backend-only review
/architect --scope=backend

# Critical findings only with GitHub issue creation
/architect --severity=critical --create-issues=true

# Database-focused review
/architect --scope=db --include-db=true
```

---

## Analysis Workflow

### Step 1: Load Architectural Context

Read TribeVibe's architectural principles:
```bash
cat .claude/context/architectural-principles.json
cat .claude/context/environment-rules.md
```

Reference implementation:
```bash
ls -R services/api/src/features/profile/
```

### Step 2: Determine Analysis Scope

Based on `--scope` argument:

**--scope=whole** (default): Analyze entire codebase
```bash
find services/api/src/features -type f -name "*.ts"
find packages -type f -name "*.ts"
```

**--scope=backend**: API services only
```bash
find services/api -type f -name "*.ts"
find packages/types packages/database packages/logger -type f -name "*.ts"
```

**--scope=frontend**: Frontend apps only
```bash
find apps/web -type f -name "*.ts" -o -name "*.tsx"
find packages/sdk -type f -name "*.ts"
```

**--scope=db**: Database and migrations only
```bash
find packages/database -type f -name "*.ts"
find packages/database/migrations -type f -name "*.sql"
```

### Step 3: Run Architectural Checks

#### Check 1: VSA Structure Validation

For each feature in `services/api/src/features/`:
```bash
FEATURE="profile"
ls services/api/src/features/$FEATURE/controllers/*.ts
ls services/api/src/features/$FEATURE/services/I*.ts
ls services/api/src/features/$FEATURE/repositories/I*.ts
```

**Report findings:**
- ✅ Complete VSA structure
- ⚠️  Missing service interface
- ❌ Missing repository implementation

#### Check 2: Layer Boundary Violations

```bash
# Controllers directly accessing database (FORBIDDEN)
grep -r "db\." services/api/src/features/*/controllers/

# Services bypassing repositories (FORBIDDEN)
grep -r "db\." services/api/src/features/*/services/ | grep -v "Repository"
```

**Report example:**
```markdown
### ❌ Layer Violation
**File**: `MatchController.ts:45`
**Issue**: Controller directly accessing database
**Severity**: CRITICAL
**Fix**: Create MatchRepository and delegate data access
```

#### Check 3: Contract-First Validation

```bash
# Find all interface definitions
grep -r "^export interface" packages/types/src/

# Check if services implement interfaces
grep -r "implements I.*Service" services/api/src/features/*/services/
```

#### Check 4: SOLID Principles

**Single Responsibility**:
```bash
# Find large classes (potential SRP violations)
find services/api/src/features -type f -name "*.ts" -exec wc -l {} \; | sort -rn | head -10
```

**Dependency Inversion**:
```bash
# Check constructor injection patterns
grep -r "constructor(" services/api/src/features/*/controllers/ -A 5
```

#### Check 5: DRY Violations

```bash
# Find similar patterns
grep -r "function validateEmail" services/api/src/
```

### Step 4: Documentation Analysis (if --include-docs=true)

```bash
cat docs/ARCHITECTURAL_ENFORCEMENT.md
grep -r "Contract-first" services/api/src/
```

Compare documentation claims vs. actual implementation.

### Step 5: Database Analysis (if --include-db=true)

```bash
ls -ltr packages/database/migrations/*.sql
grep -r "DROP TABLE\|ALTER TABLE DROP" packages/database/migrations/
```

### Step 6: Generate Report

Format findings by severity:

```markdown
# 🏗️ Architectural Review Report

**Scope**: ${scope}
**Date**: ${timestamp}

## Executive Summary
- **Total Findings**: 12
- **Critical**: 2
- **High**: 4
- **Medium**: 5
- **Low**: 1

## Critical Findings

### 1. ❌ Layer Boundary Violation
**File**: `MatchController.ts:45`
**Severity**: CRITICAL
**Issue**: Controller directly accessing database
**Fix**: Create MatchRepository and delegate

### 2. ❌ Missing Contract
**Feature**: notification
**Severity**: CRITICAL
**Issue**: Service implemented without interface
**Fix**: Define INotificationService in @tribevibe/types

## High Priority Findings
[...]

## Medium Priority Findings
[...]

## Low Priority Findings
[...]

## Recommendations
1. **Immediate**: Fix 2 critical violations
2. **This Sprint**: Address 4 high-priority findings
3. **Next Sprint**: Resolve medium-priority tech debt

## Reference Implementation
✅ **Perfect Example**: `services/api/src/features/profile/`
Use as template for all features.
```

### Step 7: Create Issues (if --create-issues=true and critical findings exist)

For each critical finding, invoke `/issue-create`:

```bash
# Claude Code uses SlashCommand tool to create issues
SlashCommand("/issue-create", {
  title: "[Architecture] ${finding.issue}",
  body: formatIssueBody(finding),
  labels: "architecture,tech-debt,critical"
})
```

---

## Output Formats

### Markdown (Default)
Human-readable report with severity sections, findings, and recommendations.

### JSON (if --output-format=json)
```json
{
  "scope": "whole",
  "timestamp": "2025-09-30T12:00:00Z",
  "summary": {
    "totalFindings": 12,
    "critical": 2,
    "high": 4,
    "medium": 5,
    "low": 1
  },
  "findings": [
    {
      "id": "VSA-001",
      "severity": "critical",
      "category": "layer-violation",
      "file": "MatchController.ts",
      "line": 45,
      "issue": "Controller directly accessing database",
      "fix": "Create MatchRepository"
    }
  ]
}
```

---

## Success Criteria

An architectural review is successful when:
1. ✅ All specified scopes analyzed
2. ✅ Violations identified with severity levels
3. ✅ Concrete fix recommendations provided
4. ✅ Reference implementations highlighted
5. ✅ Report formatted for developer action

---

## Critical Rules

### ❌ NEVER Do These:
1. Modify code (analysis only)
2. Orchestrate other commands (let OrchestratorAgent handle that)
3. Make assumptions (always grep/read actual code)
4. Provide generic advice (give specific, actionable fixes)

### ✅ ALWAYS Do These:
1. Read architectural docs first
2. Use grep for pattern detection
3. Provide file paths and line numbers
4. Suggest concrete fixes
5. Highlight reference implementations

---

## Integration Points

### Called by OrchestratorAgent
```typescript
// OrchestratorAgent invokes this for architecture tasks
await delegate("/architect", { scope: "backend", severity: "critical" });
```

### Called by Users
```bash
/architect --scope=whole --create-issues=true
```

### Invokes (for issue creation only)
```bash
# Only if --create-issues=true and critical findings exist
/issue-create --title="..." --body="..." --labels="architecture,tech-debt"
```

---

## Configuration

Settings in `.claude/config.yml`:

```yaml
validation:
  requireArchitectReview: true  # Require review before major changes
  autoCreateIssues: false        # Default for --create-issues flag
  severityThreshold: "high"      # Minimum severity to report
```

---

## Examples

### Example 1: Full Review
```bash
/architect
# Output: Comprehensive report covering all scopes
```

### Example 2: Critical Issues with Auto-Issue Creation
```bash
/architect --severity=critical --create-issues=true
# Output: Report + GitHub issues created for critical findings
```

### Example 3: Backend-Only
```bash
/architect --scope=backend --include-docs=false
# Output: Backend analysis only, skip documentation cross-check
```

---

## Related Documentation

- **Architectural Principles**: `.claude/context/architectural-principles.json`
- **Environment Rules**: `.claude/context/environment-rules.md`
- **Reference Implementation**: `services/api/src/features/profile/`
- **Agent Architecture**: `docs/agents-architecture.md`

---

## Summary

**This is an analysis tool.** It reads code, validates principles, and generates reports.

**It does NOT:** Orchestrate workflows, modify code, or coordinate other commands.

**For orchestration:** Use OrchestratorAgent or invoke this command as part of a workflow.
