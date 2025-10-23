# Skills Integration Guide for WescoBar Agents

This guide shows how to integrate Agent Skills with your existing Conductor and Orchestrator agents.

---

## Integration Patterns

### Pattern 1: Skills for Atomic Operations

When an agent needs to perform an atomic operation (run tests, create PR, commit changes), reference the skill instead of implementing inline.

**Before (Conductor Phase 3):**
```markdown
**Step 1: Run Comprehensive Tests**

Execute full test suite via Bash:
```bash
npm run test
```

Parse results and validate...
```

**After (with Skills):**
```markdown
**Step 1: Run Comprehensive Tests**

Execute comprehensive testing with the `run-comprehensive-tests` skill.

The skill will:
- Run full test suite
- Parse and validate results
- Return structured output with pass/fail status
- Provide detailed failure information if needed

Expected output: Test status, coverage percentage, failed tests list
```

**Benefits:**
- ✅ Skill contains all test execution logic
- ✅ Consistent test execution across workflows
- ✅ Easy to update test patterns (update skill, affects all agents)
- ✅ Cleaner agent code (delegates details to skill)

---

### Pattern 2: Skills for Domain Expertise

When implementing features requiring domain knowledge (Gemini API, React patterns), reference relevant skills.

**Example in Implementation Agent:**

```markdown
## Gemini API Implementation

When implementing features that use the Gemini API:

1. Consult the `gemini-api-rate-limiting` skill for:
   - Sequential queue patterns
   - Rate limit handling
   - Timeout implementation
   - Cache strategy

2. Consult the `gemini-api-error-handling` skill for:
   - Error categorization
   - Retry logic
   - User-facing error messages

3. Implement following skill guidelines
```

**Benefits:**
- ✅ Captures proven patterns from existing code
- ✅ Prevents repeating past mistakes
- ✅ Consistent API usage across features
- ✅ Team knowledge sharing

---

### Pattern 3: Composed Workflows with Skills

Complex workflows can reference multiple skills in sequence.

**Example: Conductor Phase 3 (Quality Assurance)**

```markdown
### Phase 3: Quality Assurance

**Use the `quality-gate` skill for complete validation.**

The quality-gate skill orchestrates:
1. `run-comprehensive-tests` - Test execution
2. `audit-code` - Quality audit
3. `validate-build` - Build validation
4. `check-lint` - Linting
5. `type-check` - TypeScript validation

If quality gate passes → Proceed to Phase 4
If quality gate fails → Identify failing check and route to fix agent

Minimum thresholds:
- Tests: 100% pass rate
- Audit score: ≥ 8.0/10
- Build: Must succeed
- Coverage: ≥ 80% (warning if below)
```

**Benefits:**
- ✅ Single skill call for entire quality validation
- ✅ Consistent quality standards
- ✅ Easy to adjust thresholds (update skill config)
- ✅ Reusable across agents (conductor, orchestrator, CI)

---

## Conductor Agent Integration Examples

### Phase 3: Quality Assurance (Updated)

**Old approach:**
- Inline bash commands for each check
- Manual result parsing
- Repeated validation logic

**New approach with Skills:**

```markdown
### Phase 3: Quality Assurance
**Goal**: Ensure code meets quality standards

**Step 1: Execute Quality Gate**

Use the `quality-gate` skill to validate all quality standards.

The skill will:
- Run all tests and validate pass rate
- Execute code quality audit
- Validate production build
- Check test coverage
- Verify TypeScript compilation
- Validate linting

Minimum thresholds enforced by skill:
- All tests passing
- Audit score ≥ 8.0/10
- Build successful
- Coverage ≥ 80%

**If quality gate passes:**
✅ Proceed to Phase 4 (PR Creation)

**If quality gate fails:**
⚠️ Identify failing check from skill output:
- Tests failed → Delegate to debugger agent
- Audit < 8.0 → Delegate to refactor agent
- Build failed → Investigate build errors
- Type errors → Fix type issues
- Lint errors → Auto-fix or manual fixes

After fixes, re-run quality gate.
Maximum 3 retries before escalating to human.

**OUTPUT TO USER:**
```
✅ Phase 3 Complete - All Quality Gates Passed
   Tests: ✅ 45/45 passing | Coverage: 87.5%
   Audit: ✅ 8.5/10 | Build: ✅ Passing
```
```

---

### Phase 4: PR Creation (Updated)

**Old approach:**
- Inline gh CLI commands
- Manual PR body construction
- Issue linking format validation inline

**New approach with Skills:**

```markdown
### Phase 4: PR Creation and Documentation
**Goal**: Create PR with proper linking and documentation

**Step 1: Create Pull Request**

Use the `create-pull-request` skill with metadata from previous phases.

Provide to skill:
- Issue number: #[NUMBER]
- Implementation summary: [FROM_PHASE_2]
- Test results: [FROM_PHASE_3_QUALITY_GATE]
- Audit score: [FROM_PHASE_3_QUALITY_GATE]
- Files changed: [FROM_PHASE_2]

The skill will:
- Draft comprehensive PR body
- Validate issue linking format (Fixes #123)
- Create PR with gh CLI
- Verify PR creation successful
- Return PR number and URL

**Expected output:**
- PR #[NUMBER]: [URL]
- Issue linked: ✅
- All checks queued: ✅

**OUTPUT TO USER:**
```
✅ Phase 4 Complete - PR Created Successfully
   PR #45: https://github.com/BerryKuipers/WescoBar-Universe-Storyteller/pull/45
   Issue Link: Fixes #137 ✅
```
```

---

## Orchestrator Agent Integration

The Orchestrator can route simple tasks directly to skills:

```markdown
### Task Routing Logic (Updated)

**Simple Atomic Operations** → Route to Skills (faster than agents)
- "run tests" → `run-comprehensive-tests` skill
- "validate build" → `validate-build` skill
- "create PR" → `create-pull-request` skill

**Complex Workflows** → Route to Agents
- "audit code quality" → audit agent
- "refactor this code" → refactor agent
- "review architecture" → architect agent

**Full Lifecycle** → Route to Conductor
- "implement feature end-to-end" → conductor agent
- "pick up issue #123" → conductor agent

### Example Routing Decision

```json
{
  "task": "run all tests",
  "analysis": "Simple atomic operation - test execution",
  "routing": {
    "target": "skill",
    "skill_name": "run-comprehensive-tests",
    "confidence": "high",
    "reason": "Direct skill match for test execution"
  },
  "fallback": "test-all command if skill unavailable"
}
```
```

---

## Best Practices for Skill Integration

### 1. Reference Skills by Name

```markdown
✅ GOOD: "Use the `quality-gate` skill to validate all standards"
❌ BAD: "Run quality validation" (unclear what executes)
```

### 2. Provide Context to Skills

Skills need context from the workflow:

```markdown
✅ GOOD:
Use `create-pull-request` skill with:
- Issue number: #137
- Audit score: 8.5/10
- Test results: 45/45 passing
- Coverage: 87.5%

❌ BAD:
Use `create-pull-request` skill
(Missing required context)
```

### 3. Handle Skill Outputs

Skills return structured outputs - use them in decisions:

```markdown
✅ GOOD:
Quality gate result: { status: "fail", failingCheck: "audit" }
→ Route to refactor agent to address audit findings

❌ BAD:
Quality gate ran
→ (No decision based on output)
```

### 4. Compose Skills for Complex Workflows

```markdown
✅ GOOD (Composed workflow):
Phase 3:
1. `quality-gate` skill → Complete validation
2. If fail, fix with agent → Re-run quality gate
3. If pass → Proceed to Phase 4

❌ BAD (Monolithic skill):
Create one giant `do-everything` skill
(Hard to maintain, violates single responsibility)
```

---

## Skill Update Propagation

When you update a skill:

1. **Edit skill file** (e.g., `.claude/skills/quality/quality-gate/SKILL.md`)
2. **Commit to git** (shares with team)
3. **Restart Claude Code** (loads updated skill)
4. **All agents** using that skill now use the updated version

Example:

```bash
# Update quality gate threshold
# Edit .claude/skills/quality/quality-gate/SKILL.md
# Change: minimumAuditScore from 8.0 to 8.5

# Commit
git add .claude/skills/quality/quality-gate/
git commit -m "Update quality gate: increase audit threshold to 8.5"

# Restart Claude Code
# Now conductor, orchestrator, and any agent using quality-gate
# will enforce the new 8.5 threshold
```

---

## Migration Strategy

### Phase 1: Add Skills (Completed ✅)
- Created 4 foundational skills
- Documented structure and usage
- No agent changes yet

### Phase 2: Update Conductor Phase 3 (Next)
- Replace inline quality checks with `quality-gate` skill
- Simplify validation logic
- Test with real workflow

### Phase 3: Update Conductor Phase 4 (Next)
- Replace inline PR creation with `create-pull-request` skill
- Standardize PR formatting
- Test PR creation flow

### Phase 4: Update Orchestrator (Future)
- Add skill routing for simple tasks
- Keep agent routing for complex tasks
- Document routing decisions

### Phase 5: Expand Skills (Ongoing)
- Add more domain expertise skills (React patterns, backend APIs)
- Add more atomic operation skills (commit, push, merge)
- Capture team knowledge in skills

---

## Testing Skills

### Manual Test

```bash
# 1. Restart Claude Code to load skills

# 2. Ask Claude to use a skill:
"Use the run-comprehensive-tests skill to validate all tests"

# 3. Verify skill is loaded:
- Check if Claude references skill name
- Check if skill instructions are followed
- Check if skill outputs are used
```

### Automated Test (Future)

Create test command:

```markdown
# .claude/commands/test-skills.md

Test all skills in `.claude/skills/` directory.

For each skill:
1. Verify SKILL.md exists
2. Verify YAML frontmatter is valid
3. Verify name and description present
4. Verify skill body is under 500 lines
5. Try invoking skill with sample context

Report: Skills that pass/fail validation
```

---

## Troubleshooting

### Skill not being used?

**Check:**
1. Is SKILL.md present in skill directory?
2. Is YAML frontmatter valid (name + description)?
3. Did you restart Claude Code after adding skill?
4. Is skill description clear and searchable?

**Fix:**
```bash
# Verify YAML frontmatter
head -5 .claude/skills/quality/quality-gate/SKILL.md

# Should show:
# ---
# name: quality-gate
# description: Complete quality validation...
# ---

# Restart Claude Code to reload
```

### Agent not referencing skill?

**Check:**
1. Is agent workflow mentioning skill by name?
2. Is context provided to skill?
3. Is skill actually needed for this task?

**Fix:**
Update agent file to explicitly reference skill:
```markdown
Use the `quality-gate` skill to validate all standards.
```

---

## Summary

**Skills enhance agents, not replace them:**
- **Agents**: Orchestrate workflows, delegate tasks
- **Skills**: Provide domain expertise, execute atomic operations

**Integration approach:**
- Reference skills by name in agent workflows
- Provide context from workflow to skills
- Use skill outputs in routing decisions
- Compose skills for complex workflows

**Benefits:**
- Consistent operations across agents
- Team knowledge captured in skills
- Easy to update (change skill, affects all agents)
- Cleaner agent code (delegate details to skills)

**Next steps:**
1. Test skills with current conductor workflow
2. Refine skill descriptions based on usage
3. Add more skills as patterns emerge
4. Share skills with team via git

---

**Created**: 2025-10-21
**Purpose**: Guide for integrating Agent Skills with existing Conductor/Orchestrator agents
**Status**: Phase 1 complete (4 skills created), Phase 2-3 ready to begin
