# Audit Command

**Arguments:** [--scope=security|quality|all] [--create-report]

**Description:** User-facing command that delegates to the audit agent for comprehensive code auditing. Thin wrapper providing convenient CLI interface.

---

## ⚠️ Important: Thin Wrapper

**This command delegates all work to:** `.claude/agents/audit.md`

---

## Usage

```bash
/audit                          # Full audit
/audit --scope=security         # Security focus
/audit --scope=quality --create-report
```

---

## Workflow

### Step 1: Parse Arguments
```bash
SCOPE="${1:-all}"
CREATE_REPORT=false

for arg in "$@"; do
  case $arg in
    --scope=*) SCOPE="${arg#*=}" ;;
    --create-report) CREATE_REPORT=true ;;
  esac
done
```

### Step 2: Delegate to Audit Agent

```markdown
"I need a comprehensive audit from the audit specialist.

Audit Request:
- **Scope**: $SCOPE (security / quality / full audit)
- **Create Report**: $CREATE_REPORT
- **Project Root**: $(pwd)

Analyze:
1. Security vulnerabilities and risks
2. Code quality issues
3. Test coverage gaps
4. Performance bottlenecks
5. Documentation completeness
6. Dependency health

Provide:
- Severity-grouped findings
- Actionable recommendations
- Summary statistics
- Report file if requested"
```

### Step 3: Display Results
```bash
echo "✅ Audit complete - review findings above"
```

---

## Notes

**Agent-First Architecture:**
- This command = User interface
- `.claude/agents/audit.md` = Worker (does actual audit)
- Modify the agent, not this command

**Generated**: 2025-10-23 (Modernized thin wrapper)
