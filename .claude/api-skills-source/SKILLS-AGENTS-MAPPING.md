# Skills → Agents Mapping

Comprehensive mapping of which API skills are used by which agents and when.

## API Skills Overview

### Quality & Testing Skills

| Skill | ID | Purpose | Primary Users |
|-------|-----|---------|---------------|
| **quality-gate** | `skill_016qnPYM55EUfzTjTCeL4Zng` | Comprehensive validation (all checks) | conductor, audit |
| **validate-typescript** | `skill_01TYxAPLSwWUAJvpiBgaDcfn` | TypeScript type checking | conductor, refactor, architect |
| **validate-lint** | `skill_0154reaLWo6CsYUmARtg9aCk` | ESLint/Prettier validation | conductor, refactor |
| **run-comprehensive-tests** | `skill_01EfbHCDmLehZ9CNKxxRBMzZ` | Test suite with coverage | conductor, refactor |
| **validate-coverage-threshold** | `skill_01KvzeoAq1YbafijP1RiJSJw` | Coverage threshold check | conductor, audit |
| **validate-build** | `skill_01Ew1QtJeHnYdpwAXj2HhrNw` | Production build validation | conductor, architect, audit |

### Security & Maintenance Skills

| Skill | ID | Purpose | Primary Users |
|-------|-----|---------|---------------|
| **audit-dependencies** | `skill_01JvZxokSnKZ7bLwLQMAvKo1` | npm audit + outdated packages | security-pentest, audit |
| **validate-git-hygiene** | `skill_019bRtByNMx2hjhtnL5uhowG` | Git commit & branch validation | conductor, git workflows |

---

## Agent → Skills Mapping

### conductor (Workflow Orchestrator)

**Phase 1: Issue Discovery**
- No skills needed (analysis only)

**Phase 2: Implementation**
- `validate-git-hygiene` - Branch naming validation

**Phase 3: Quality Assurance** ⭐ PRIMARY USE
- **Option A (Recommended):** `quality-gate` - Runs ALL checks
- **Option B (Granular):**
  - `validate-typescript` - Type checking
  - `validate-lint` - Code style
  - `run-comprehensive-tests` - Testing
  - `validate-coverage-threshold` - Coverage
  - `validate-build` - Build validation

**Phase 4: PR Creation**
- `validate-git-hygiene` - Commit message validation

**Phase 5: Gemini Review**
- No skills needed (external process)

**Phase 6: Final Report**
- `audit-dependencies` - Final security check

**Status:** ✅ Fully updated with all API skill references

---

### refactor (Code Refactoring Agent)

**Pre-Refactor Validation:**
- `validate-typescript` - Baseline type safety
- `validate-lint` - Baseline code quality
- `run-comprehensive-tests` - Baseline test coverage

**Post-Refactor Validation:**
- `validate-typescript` - No new type errors
- `validate-lint` - Code quality maintained
- `run-comprehensive-tests` - All tests still pass

**Status:** ⚠️ **NEEDS UPDATE** - Should reference API skills instead of filesystem skills

---

### architect (Architecture Review)

**Architecture Validation:**
- `validate-typescript` - Contract-first type validation
- `validate-build` - Build structure validation
- `validate-lint` - Code organization patterns

**Use Case:**
- Pre-implementation: Validate architecture design compiles
- Post-implementation: Validate pattern compliance

**Status:** ⚠️ **NEEDS UPDATE** - Should add API skill references

---

### audit (Comprehensive Project Audit)

**Security & Quality Audit:**
- `quality-gate` - Overall project quality
- `audit-dependencies` - Security vulnerabilities
- `validate-coverage-threshold` - Test coverage health
- `validate-build` - Build health

**Use Case:**
- Periodic health checks
- Pre-release validation
- Technical debt assessment

**Status:** ⚠️ **NEEDS UPDATE** - Should add API skill references

---

### security-pentest (Security Testing)

**Security Checks:**
- `audit-dependencies` - Vulnerability scanning
- `validate-git-hygiene` - Sensitive file detection

**Use Case:**
- Security audits
- Pre-deployment checks
- Compliance validation

**Status:** ⚠️ **NEEDS UPDATE** - Should add API skill references

---

### database (Database Operations)

**Validation:**
- None currently (database-specific validation needed)

**Future Skills Needed:**
- `validate-migrations` - Migration safety checks
- `validate-schema` - Schema validation

**Status:** ✅ No API skills applicable yet

---

### design (UI/UX Design)

**Validation:**
- None currently (design-specific validation)

**Future Skills Needed:**
- `validate-accessibility` - A11y compliance
- `validate-responsive` - Responsive design checks

**Status:** ✅ No API skills applicable yet

---

### implementation (Feature Implementation)

**Quality Checks:**
- `validate-typescript` - Type safety during development
- `validate-lint` - Code style compliance

**Use Case:**
- Real-time validation during implementation
- Pre-commit checks

**Status:** ⚠️ **NEEDS UPDATE** - Should add API skill references

---

### researcher (Research & Documentation)

**Validation:**
- None (research-focused)

**Status:** ✅ No API skills needed

---

### orchestrator (Task Routing)

**Validation:**
- Routes to conductor which uses skills

**Status:** ✅ Delegates to conductor

---

## Skill Usage Patterns

### Pattern 1: Comprehensive Validation
**Use `quality-gate` for:**
- End-to-end quality checks
- Pre-PR validation
- CI/CD pipelines
- Periodic health checks

**Agents:** conductor, audit

### Pattern 2: Targeted Validation
**Use individual skills for:**
- Specific validation needs
- Incremental checks during development
- Debugging specific issues
- Performance optimization

**Agents:** refactor, architect, implementation

### Pattern 3: Security Focus
**Use security skills for:**
- Dependency audits
- Sensitive file detection
- Pre-deployment security

**Agents:** security-pentest, audit

### Pattern 4: Git Workflow
**Use git-hygiene for:**
- Branch creation
- Commit validation
- PR preparation

**Agents:** conductor, git workflows

---

## Update Priority

### High Priority (Core Workflows)
1. ✅ **conductor** - Already updated
2. ⚠️ **refactor** - Needs API skill references
3. ⚠️ **architect** - Needs API skill references

### Medium Priority (Specialized)
4. ⚠️ **audit** - Needs API skill references
5. ⚠️ **security-pentest** - Needs API skill references
6. ⚠️ **implementation** - Needs API skill references

### Low Priority (Delegating/Specialized)
7. ✅ **orchestrator** - Delegates to conductor
8. ✅ **database** - No applicable skills yet
9. ✅ **design** - No applicable skills yet
10. ✅ **researcher** - No skills needed

---

## Benefits of API Skills

### For Agents:
- ✅ Faster execution (parallel processing)
- ✅ Structured output (easy to parse)
- ✅ Consistent results
- ✅ Available everywhere (not just Claude Code)

### For Users:
- ✅ Predictable validation
- ✅ Clear pass/fail criteria
- ✅ Actionable error messages
- ✅ Reusable across projects

---

## Next Steps

1. **Update refactor agent** - Add API skill references for pre/post validation
2. **Update architect agent** - Add type/build validation
3. **Update audit agent** - Add comprehensive skill usage
4. **Update security-pentest** - Add dependency audit
5. **Update implementation agent** - Add real-time validation
6. **Document skill invocation** - Add examples to each agent
