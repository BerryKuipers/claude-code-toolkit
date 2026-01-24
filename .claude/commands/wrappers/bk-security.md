# bk-security - Toolkit Security Review Wrapper

**Arguments:** [--scope=all|api|auth|deps] [--create-issues]

**Description:** Toolkit wrapper around upstream security-reviewer agent. Adds OWASP checklist and severity enforcement.

---

## Instructions

You are executing the toolkit security review wrapper.

### Step 1: Scope Determination

Based on --scope:
- `all`: Full security audit
- `api`: Focus on API endpoints, input validation
- `auth`: Authentication/authorization flows
- `deps`: Dependency vulnerabilities only

### Step 2: Delegate to Upstream Security Reviewer

```
Task(
  subagent_type: "everything-claude-code:security-reviewer",
  prompt: "Security audit with scope: [SCOPE]\n\nCheck for:\n- OWASP Top 10\n- Secrets in code\n- Injection vulnerabilities\n- Auth/authz issues"
)
```

### Step 3: Run Dependency Audit

```bash
npm audit --json 2>/dev/null
# or
pnpm audit --json 2>/dev/null
```

### Step 4: Enforce Output Contract

```markdown
## Security Audit Report

### Executive Summary
[Overall security posture: CRITICAL | HIGH | MEDIUM | LOW]

### Critical Findings (P0 - Immediate Action)
| Finding | Location | OWASP Category | Remediation |
|---------|----------|----------------|-------------|
| [Issue] | file:line | [A01-A10] | [Fix] |

### High Severity (P1)
[Table format]

### Medium Severity (P2)
[Table format]

### Low Severity (P3)
[Table format]

### Dependency Vulnerabilities
| Package | Severity | CVE | Fix Version |
|---------|----------|-----|-------------|

### Secrets Scan
- [PASS/FAIL] No hardcoded secrets found
- [Files checked]

### Recommendations
1. [Priority action items]
```

### Step 5: Create Issues (if --create-issues)

For each Critical/High finding:
```bash
gh issue create --title "[SECURITY] [Finding title]" --body "[Details]" --label "security,priority:high"
```

---

## Fallback

If upstream unavailable, use toolkit's `security-pentest` agent.
