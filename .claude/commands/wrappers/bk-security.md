# bk-security - Toolkit Security Review Wrapper

**Arguments:** [--scope=all|api|auth|deps] [--create-issues]

**Description:** Toolkit wrapper that DELEGATES security review via Task tool.

---

## CRITICAL: This is a DELEGATION command

**DO NOT perform the security review yourself. You MUST delegate via Task tool.**

This command spawns a security agent - keeping your context clean.

---

## Instructions

### Step 1: Quick Dependency Check (inline)

```bash
npm audit --json 2>/dev/null | head -50 || echo "No npm audit"
```

### Step 2: IMMEDIATELY Spawn Security Agent

**YOU MUST CALL THE TASK TOOL NOW.**

```
Task(
  subagent_type: "everything-claude-code:security-reviewer",
  description: "Security audit",
  prompt: "Security audit with scope: [SCOPE]

Check for:
- OWASP Top 10 vulnerabilities
- Hardcoded secrets/credentials
- SQL/NoSQL injection risks
- XSS vulnerabilities
- Authentication/authorization flaws
- Insecure direct object references
- Missing input validation"
)
```

### Step 3: Format Output

```markdown
## Security Audit Report

### Summary
**Posture**: [CRITICAL ❌ | HIGH ⚠️ | MEDIUM | LOW ✅]

### Critical Findings (P0)
| Finding | Location | OWASP | Fix |
|---------|----------|-------|-----|

### High Severity (P1)
[Table]

### Dependency Vulnerabilities
| Package | Severity | CVE | Fix Version |
|---------|----------|-----|-------------|

### Secrets Scan
- [PASS ✅ / FAIL ❌] Hardcoded secrets

### Recommendations
1. [Priority actions]
```

### Step 4: Create Issues (if --create-issues)

For Critical/High findings:
```bash
gh issue create --title "[SECURITY] [Finding]" --label "security"
```

---

## Fallback

If upstream unavailable:
```
Task(subagent_type: "security-pentest", prompt: "[same]")
```

**NEVER perform security review inline.**
