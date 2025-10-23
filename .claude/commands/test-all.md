# Test All Command

**AI-Powered Testing Orchestrator** that intelligently prioritizes, executes, and analyzes all available test and audit commands with smart filtering, adaptive execution, and AI-driven result analysis.

## Usage

```bash
/test-all [suite|category] [options]
```

## Test Suites

- `core` - Unit tests, lint, types, audit, contracts (default)
- `full` - All available tests including user flows and integration
- `quick` - Fast subset for development (unit + lint)
- `pre-commit` - Pre-commit validation (unit + lint + audit)
- `ci-ready` - Everything needed for CI/CD pipeline
- `parallel` - Run core tests in parallel for speed

## Test Categories

- `unit` - Unit tests via nx test framework
- `lint` - ESLint and code quality checks
- `types` - TypeScript validation and type audits
- `audit` - Code audits and security analysis
- `contracts` - API contract and schema validation
- `build` - Build verification and compilation
- `user-flow` - User flow and E2E tests
- `integration` - Integration and system tests

## Options

- `--parallel` - Run tests in parallel where possible
- `--verbose` - Show detailed output and logs
- `--continue-on-error` - Don't stop on first failure
- `--report` - Generate comprehensive test report
- `--dashboard` - Open relevant dashboards after testing

## Examples

```bash
/test-all                           # Run core suite (default)
/test-all full --verbose            # Run all tests with detailed output
/test-all unit                      # Run only unit tests
/test-all parallel                  # Run core tests in parallel
/test-all quick --continue-on-error # Fast development check
/test-all pre-commit                # Pre-commit validation
/test-all ci-ready --report         # Full CI pipeline validation
```

## 🧠 AI-Driven Execution Strategy

### **Phase 1: Intelligent Priority Analysis**
1. **Parse Arguments**: Determine test scope and user intent
2. **Environment Assessment**: Check system state, recent changes, CI context
3. **Priority Calculation**: AI determines execution order based on:
   - **Critical Path Analysis**: Tests that block other tests if they fail
   - **Recent Changes**: Git diff analysis - test areas that changed first
   - **Historical Failure Patterns**: Learn from past failures to predict issues
   - **Dependency Mapping**: Tests that validate foundations (types → unit → integration)
   - **Time Constraints**: Fast tests first if `--quick` context detected

### **Phase 2: Adaptive Execution with AI Thinking**
4. **Execute Priority Tier 1 (CRITICAL - Block everything if fail)**:
   - **Build Validation**: `npm run build:packages` (if code doesn't compile, stop)
   - **Type Safety**: `npm run validate-types` (type errors block everything)
   - **Unit Tests**: `npm test` (core logic must work)

5. **AI Analysis Checkpoint**:
   - **Think about results**: What failed? Why? Should we continue?
   - **Pattern Recognition**: Does this failure match known issue patterns?
   - **Decision Making**: Skip non-critical tests if critical foundation is broken
   - **Context Awareness**: Consider if this is CI, development, or pre-commit

6. **Execute Priority Tier 2 (HIGH - Important but not blocking)**:
   - **Code Quality**: `npm run lint` (style issues shouldn't block functionality)
   - **Security Audits**: `npm run audit` (important but can be addressed later)
   - **Contract Validation**: `npm run validate-contracts` (API consistency)

7. **Execute Priority Tier 3 (MEDIUM - Nice to have)**:
   - **Extended Type Audits**: `npm run audit:types` (cleanup tasks)
   - **Pre-commit Hooks**: `npm run audit:pre-commit` (process validation)
   - **Build Verification**: `npm run build:services`, `npm run build:apps`

8. **Execute Priority Tier 4 (LOW - Integration & E2E)**:
   - **Basic User Flows**: `npm run test:user-flow` (requires working system)
   - **Specific Flows**: `npm run test:user-flow:login`, `npm run test:user-flow:admin` (targeted E2E)
   - **Enhanced E2E**: `npm run test:user-flow:enhanced` (full Playwright integration)
   - **Complete Suite**: `npm run test:full` (everything including user flows)
   - **Integration Scripts**: Custom integration tests (expensive operations)

### **Phase 3: AI-Powered Result Analysis & Recommendations**
9. **Intelligent Result Synthesis**:
   - **Failure Analysis**: AI categorizes failures (syntax, logic, environment, flaky)
   - **Root Cause Analysis**: Correlate failures across test types
   - **Impact Assessment**: Understand blast radius of failures
   - **Priority Ranking**: Order fixes by impact and effort

10. **Smart Recommendations**:
    - **Immediate Actions**: "Fix TypeScript errors in ProfileService first"
    - **Parallel Work**: "Lint issues can be fixed while investigating unit test failures"
    - **Skip Suggestions**: "Skip E2E tests - unit tests show core logic broken"
    - **Next Steps**: "Run `/debug --trace-errors` to investigate ProfileService issues"

## Test Command Mapping

### Core Commands
- `npm test` - Unit tests via nx
- `npm run lint` - ESLint and code quality
- `npm run validate-types` - TypeScript validation
- `npm run audit` - General code audit
- `npm run validate-contracts` - API contract validation

### Extended Commands
- `npm run audit:types` - Type audit for any usage
- `npm run audit:pre-commit` - Pre-commit checks
- `npm run audit:full` - Full audit with build verification
- `npm run sync-types` - Type synchronization
- `npm run build:packages` - Package builds
- `npm run build:services` - Service builds
- `npm run build:apps` - Application builds
- `npm run test:user-flow` - User flow tests
- `npm run test:user-flow:enhanced` - Enhanced E2E tests with Playwright
- `npm run test:user-flow:login` - Login flow specific tests
- `npm run test:user-flow:admin` - Admin flow specific tests
- `npm run test:full` - Complete test suite including user flows

### Integration Scripts
- `node scripts/integration-test.js` - Integration test suite
- `node scripts/test-api-connection.js` - API connectivity
- `node scripts/test-unified-config.js` - Configuration validation

## Success Criteria

- ✅ All unit tests pass (0 failures)
- ✅ No linting errors or warnings
- ✅ TypeScript compiles without errors
- ✅ No security audit findings
- ✅ All contracts validate successfully
- ✅ Build completes successfully
- ✅ User flow tests pass
- ✅ Integration tests pass

## Parallel Execution Strategy

When `--parallel` is specified:
1. Group independent test categories
2. Run unit, lint, types, and audit commands simultaneously
3. Run build verification after core tests complete
4. Run user flow and integration tests sequentially (they may have dependencies)

## Error Handling

- **Critical Failures**: Unit tests, build failures stop execution
- **Non-Critical**: Type audits, some integration tests continue with warnings
- **Continue Mode**: With `--continue-on-error`, collect all failures and report at end

## Output Format

```
🧪 TribeVibe Test Suite: [suite-name]
📋 [Category Name]
🔄 [Test Description]... ✅ (123ms)
⏱️ Test Summary (12345ms total)
Total: 15 | Passed: 13 | Failed: 2
```

## Integration with Other Commands

- Use with `/test-user-flow` for comprehensive E2E validation
- Combine with `/debug` for issue analysis
- Follow with `/pr-process` for pull request preparation

## 🤖 AI Thinking Process

The command uses structured thinking prompts to make intelligent decisions:

### **Before Execution:**
```
Think: What is the user trying to achieve?
- Development validation? → Prioritize unit tests + lint
- CI pipeline? → Run everything systematically
- Quick check? → Fast tests only
- Pre-commit? → Focus on blockers

Think: What has changed recently?
- Check git diff to identify risk areas
- Has ProfileService changed? Prioritize profile tests
- New dependencies? Run security audits first
- Config changes? Test environment setup

Think: What context clues do I have?
- Time of day (quick check vs thorough validation)
- Branch name (feature vs hotfix vs main)
- Recent CI failures (focus on known problem areas)
```

### **During Execution:**
```
Think: Should I continue after this failure?
- TypeScript errors? STOP - nothing else will work
- Unit test failures? STOP - core logic broken
- Lint errors? CONTINUE - style issues don't break functionality
- E2E failures? CONTINUE - might be environment issues

Think: What does this failure pattern tell me?
- Multiple ProfileService failures → Focus on profile logic
- Build errors + type errors → Dependency issues
- Intermittent E2E failures → Environment instability
```

### **After Execution:**
```
Think: What should the developer do next?
- Prioritize fixes by impact (blockers first)
- Suggest parallel work (lint fixes while debugging logic)
- Recommend tools (/debug for error analysis)
- Identify patterns (same type of errors repeatedly)

Think: How can I help prevent these issues?
- Suggest better pre-commit hooks
- Recommend additional tests for failure-prone areas
- Propose architectural improvements
```

## 🎯 Smart Execution Examples

### **Example 1: Development Context**
```
User runs: /test-all quick
AI thinks: "Development context, need fast feedback"
Priority: Unit tests → Lint → Types (skip slow E2E)
Decision: If unit tests fail, show error details and skip everything else
Output: "❌ 3 unit tests failed in ProfileService. Focus on fixing these first before other checks."
```

### **Example 2: CI Context**
```
User runs: /test-all ci-ready
AI thinks: "CI context, need comprehensive validation"
Priority: Types → Build → Unit → Integration → E2E
Decision: Continue through all tiers, collect all failures
Output: "⚠️ 15 total issues found across 4 categories. Critical: Fix 3 TypeScript errors. Medium: 12 lint issues can be batch-fixed."
```

### **Example 3: Pre-commit Context**
```
User runs: /test-all pre-commit
AI thinks: "About to commit, what could break main branch?"
Priority: Check changed files → Unit tests for affected areas → Lint staged files
Decision: Focus only on changes that could break others
Output: "✅ Your ProfileService changes pass all critical tests. 2 minor lint issues in files you didn't touch - safe to commit."
```

### **Example 4: Smart User Flow Selection**
```
User runs: /test-all user-flow
AI thinks: "Which user flows are most relevant?"
Analysis: Recent changes in AuthController → Prioritize login flow
Priority: test:user-flow:login → test:user-flow → test:user-flow:admin → test:user-flow:enhanced
Decision: Run login tests first since auth code changed
Output: "🔍 Auth code changes detected. Running login flow tests first... ✅ Login flows pass. Running general user flows..."
```

## Benefits

- 🧠 **AI-Driven Intelligence** - Thinks about results and adapts execution
- 🎯 **Priority-Based Execution** - Critical tests first, smart stopping points
- 🔍 **Context Awareness** - Understands development vs CI vs pre-commit needs
- ⚡ **Adaptive Speed** - Skips irrelevant tests when critical ones fail
- 📊 **Intelligent Analysis** - Correlates failures and suggests fixes
- 🚀 **Smart Recommendations** - Next steps based on actual results
- 🎛️ **Flexible Scope** - From quick checks to comprehensive validation
- 🔄 **Learning System** - Gets smarter about your codebase over time