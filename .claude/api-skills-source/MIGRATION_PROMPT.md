# TribeVibe API Skills Migration Prompt

**Use this prompt in TribeVibe repo to update agents with API skills.**

---

## Migration Prompt (Copy/Paste into TribeVibe)

```markdown
I need you to update all agents in this repository to use the new Anthropic API Skills for quality validation, testing, and security checks.

## Background

We've created 8 reusable API Skills that provide structured validation results. These skills are already uploaded to Anthropic API and available across all Claude platforms.

## Available API Skills

### Quality & Testing Skills

| Skill Name | Skill ID | Purpose |
|-----------|----------|---------|
| quality-gate | `skill_016qnPYM55EUfzTjTCeL4Zng` | Comprehensive quality validation (all checks) |
| validate-typescript | `skill_01TYxAPLSwWUAJvpiBgaDcfn` | TypeScript type checking |
| validate-lint | `skill_0154reaLWo6CsYUmARtg9aCk` | ESLint/Prettier validation |
| run-comprehensive-tests | `skill_01EfbHCDmLehZ9CNKxxRBMzZ` | Test suite with coverage |
| validate-coverage-threshold | `skill_01KvzeoAq1YbafijP1RiJSJw` | Coverage threshold validation |
| validate-build | `skill_01Ew1QtJeHnYdpwAXj2HhrNw` | Production build validation |

### Security & Maintenance Skills

| Skill Name | Skill ID | Purpose |
|-----------|----------|---------|
| audit-dependencies | `skill_01JvZxokSnKZ7bLwLQMAvKo1` | npm audit + outdated packages |
| validate-git-hygiene | `skill_019bRtByNMx2hjhtnL5uhowG` | Git commit & branch validation |

## Tasks

### 1. Update conductor.md Agent

**Phase 3: Quality Assurance** should recommend using API skills:

Add this section to Phase 3:

```markdown
**🚀 RECOMMENDED: Use Quality Gate API Skills (Faster & More Reliable)**

**Option A: API Skills (Recommended)**

The `quality-gate` API skill runs all quality checks in one execution:

**Describe the need:**
"I need to run comprehensive quality validation using the quality-gate API skill.

Project path: [current project directory]
Coverage threshold: 80

This will run:
- TypeScript type checking
- Linting validation
- Full test suite with coverage
- Production build validation

Return structured results showing pass/fail for each check."

**Expected Output:**
```json
{
  "qualityGate": "pass" | "fail",
  "checks": {
    "typeCheck": {"status": "pass", "errors": 0},
    "lint": {"status": "pass", "errors": 0, "warnings": 2},
    "tests": {"status": "pass", "total": 45, "passed": 45, "coverage": 87.5},
    "build": {"status": "pass", "duration": "12.3s"}
  },
  "blockers": [],
  "warnings": ["2 lint warnings"]
}
```

**Option B: Individual Skills (Granular Control)**

For specific validations:
- validate-typescript (skill_01TYxAPLSwWUAJvpiBgaDcfn)
- validate-lint (skill_0154reaLWo6CsYUmARtg9aCk)
- run-comprehensive-tests (skill_01EfbHCDmLehZ9CNKxxRBMzZ)
- validate-build (skill_01Ew1QtJeHnYdpwAXj2HhrNw)
```

### 2. Update refactor.md Agent

**Pre-Refactor Validation (Step 1):**

Replace manual command steps with:

```markdown
**🚀 RECOMMENDED: Use API Skills for Baseline Validation**

Run baseline quality checks using API skills for structured results:

**Describe the need:**
"I need to establish pre-refactor baseline using:
1. validate-typescript API skill (skill_01TYxAPLSwWUAJvpiBgaDcfn)
2. validate-lint API skill (skill_0154reaLWo6CsYUmARtg9aCk)
3. run-comprehensive-tests API skill (skill_01EfbHCDmLehZ9CNKxxRBMzZ)

Record all results for post-refactor comparison."

**Expected Output:**
- TypeScript: 0 errors
- Lint: 0 errors (warnings acceptable)
- Tests: All passing, coverage ≥80%
```

**Post-Refactor Validation (Step 5):**

Add the same skills for comparison:

```markdown
"Run post-refactor validation using:
1. validate-typescript API skill
2. validate-lint API skill
3. run-comprehensive-tests API skill

Compare with baseline - ensure no regressions."
```

### 3. Update architect.md Agent

**Architecture Validation Section:**

Add API skills for contract-first validation:

```markdown
**Contract-First Validation:**

Use API skills to validate architecture compliance:

**Describe the need:**
"Validate architecture using:
1. validate-typescript API skill - Contract-first type validation
2. validate-build API skill - Build structure validation
3. validate-lint API skill - Code organization patterns

Check that:
- All TypeScript interfaces defined before implementation
- Build succeeds with proper layer boundaries
- Code follows architectural patterns"
```

### 4. Update audit.md Agent

**Comprehensive Audit Section:**

Add all relevant skills:

```markdown
**🚀 Comprehensive Quality & Security Audit**

Use API skills for structured audit:

**Describe the need:**
"Run comprehensive audit using:
1. quality-gate API skill - Overall project quality
2. audit-dependencies API skill - Security vulnerabilities
3. validate-coverage-threshold API skill - Test coverage health
4. validate-build API skill - Build health

Provide detailed report on project health."
```

### 5. Update security-pentest.md Agent

**Security Checks Section:**

```markdown
**Security Validation:**

Use security-focused API skills:

**Describe the need:**
"Run security checks using:
1. audit-dependencies API skill (skill_01JvZxokSnKZ7bLwLQMAvKo1)
   - Scan for vulnerabilities
   - Check for outdated packages
   - Classify by severity (critical/high/moderate/low)

2. validate-git-hygiene API skill (skill_019bRtByNMx2hjhtnL5uhowG)
   - Detect sensitive files (.env, credentials, .pem, .key)
   - Check commit message patterns
   - Validate branch hygiene

Return structured security report."
```

### 6. Update implementation.md Agent

**Quality Checks During Development:**

```markdown
**Real-Time Validation:**

During implementation, use API skills for quick checks:

**Describe the need:**
"Run quick validation using:
1. validate-typescript API skill - Type safety
2. validate-lint API skill - Code style

These run fast and provide immediate feedback."
```

## Execution Instructions

1. **Read each agent file** (conductor.md, refactor.md, architect.md, etc.)
2. **Find the validation/quality check sections** in each agent
3. **Add API skill references** as shown above (use "Describe the need" pattern)
4. **Keep fallback manual commands** as "Option B" for compatibility
5. **Commit changes** with descriptive messages

## Expected Outcome

After migration:
- ✅ conductor uses quality-gate or individual skills in Phase 3
- ✅ refactor uses API skills for pre/post validation
- ✅ architect uses API skills for architecture validation
- ✅ audit uses API skills for comprehensive audits
- ✅ security-pentest uses audit-dependencies + validate-git-hygiene
- ✅ implementation uses TypeScript + lint skills for quick checks

All agents will have:
- Faster execution (skills run in parallel)
- Structured results (JSON output)
- Consistent validation across workflows
- Availability across all Claude platforms

## Reference Documentation

For complete details, see:
- SKILLS-AGENTS-MAPPING.md - Full skills→agents mapping
- .claude/api-skills-source/README.md - All skill IDs and versions
- .claude/api-skills-source/*/SKILL.md - Individual skill documentation

## Testing After Migration

After updating agents, test with:

1. **conductor Phase 3**: Should use quality-gate or individual skills
2. **refactor workflow**: Should establish baseline with API skills
3. **architect review**: Should validate with TypeScript + build skills
4. **audit command**: Should run comprehensive audit with API skills

All validations should return structured JSON with `canProceed` flag.
```

---

## Additional Notes for TribeVibe

### Project-Specific Considerations

1. **TribeVibe Uses Different Tech Stack**
   - These skills work with ANY TypeScript/JavaScript project
   - Skills detect tools automatically (npm scripts, npx, direct commands)
   - No configuration needed

2. **Backend vs Frontend**
   - Skills work for both monorepo and individual services
   - Can validate entire TribeVibe monorepo or specific packages

3. **Coverage Thresholds**
   - Default: 80% overall, 80% statements, 75% branches, 80% functions
   - Can customize per project needs

### Migration Strategy

**Recommended Order:**
1. ✅ Update conductor first (most critical)
2. ✅ Update refactor (high usage)
3. ✅ Update architect (architecture validation)
4. Update audit (comprehensive checks)
5. Update security-pentest (security focus)
6. Update implementation (developer experience)

### Fallback Plan

Keep manual commands as "Option B" so if API skills are unavailable:
- Agent can fall back to direct npm commands
- No workflow disruption
- Graceful degradation

### Verification

After migration, verify:
```bash
# Check agent files updated
git diff .claude/agents/

# Test conductor Phase 3
# (trigger conductor workflow and verify it uses API skills)

# Test refactor baseline
# (trigger refactor and verify baseline uses API skills)
```

---

## Need Help?

If you encounter issues during migration:
1. Check SKILLS-AGENTS-MAPPING.md for correct skill IDs
2. Verify skill invocation pattern: "Describe the need: ..."
3. Ensure fallback commands are preserved
4. Test one agent at a time

Generic skills, reusable everywhere! 🚀
