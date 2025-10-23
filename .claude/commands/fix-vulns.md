# Fix Vulnerabilities - Automated Security Vulnerability Remediation

**Arguments:** [--severity=critical|high|moderate|all]

**Success Criteria:** Vulnerabilities fixed, tests pass, security report generated, PR created with remediation changes

**Description:** Multi-step workflow to detect, categorize, and automatically fix known security vulnerabilities in npm dependencies

---

## Purpose

This command provides automated remediation for npm security vulnerabilities. It detects vulnerabilities via `npm audit`, attempts automatic fixes, researches manual fix paths for complex cases, and generates comprehensive reports with PR creation for review.

---

## Important: Workflow Scope

**This command is a multi-step remediation workflow:**
- Detects vulnerabilities using npm audit
- Attempts automatic fixes with safety validation
- Describes delegation needs for complex breaking changes (uses natural language)
- Does NOT orchestrate other commands directly (hub-and-spoke pattern)
- Does NOT make architectural decisions (delegates to specialists)

---

## Workflow

### **Step 1: Run npm audit to detect vulnerabilities**

```bash
echo "Step 1: Running npm audit to detect vulnerabilities..."
echo ""

# Run npm audit and capture output
npm audit --json > /tmp/npm-audit-results.json

# Extract summary
TOTAL_VULNS=$(jq '.metadata.vulnerabilities.total // 0' /tmp/npm-audit-results.json)
CRITICAL=$(jq '.metadata.vulnerabilities.critical // 0' /tmp/npm-audit-results.json)
HIGH=$(jq '.metadata.vulnerabilities.high // 0' /tmp/npm-audit-results.json)
MODERATE=$(jq '.metadata.vulnerabilities.moderate // 0' /tmp/npm-audit-results.json)
LOW=$(jq '.metadata.vulnerabilities.low // 0' /tmp/npm-audit-results.json)

echo "Vulnerability Summary:"
echo "  Critical: $CRITICAL"
echo "  High: $HIGH"
echo "  Moderate: $MODERATE"
echo "  Low: $LOW"
echo "  Total: $TOTAL_VULNS"
echo ""

if [[ "$TOTAL_VULNS" == "0" ]]; then
    echo "No vulnerabilities found. Exiting."
    exit 0
fi
```

**Success Criteria:** npm audit completes, vulnerabilities detected and categorized by severity

---

### **Step 2: Categorize vulnerabilities by severity**

```bash
echo "Step 2: Categorizing vulnerabilities by severity filter..."
echo ""

# Determine which severity levels to fix based on --severity argument
SEVERITY_FILTER="${1:-high}"

case "$SEVERITY_FILTER" in
    critical)
        echo "Filter: CRITICAL only"
        FIX_COUNT=$CRITICAL
        ;;
    high)
        echo "Filter: CRITICAL + HIGH"
        FIX_COUNT=$((CRITICAL + HIGH))
        ;;
    moderate)
        echo "Filter: CRITICAL + HIGH + MODERATE"
        FIX_COUNT=$((CRITICAL + HIGH + MODERATE))
        ;;
    all)
        echo "Filter: ALL vulnerabilities"
        FIX_COUNT=$TOTAL_VULNS
        ;;
    *)
        echo "Invalid severity filter: $SEVERITY_FILTER"
        echo "Valid options: critical, high, moderate, all"
        exit 1
        ;;
esac

echo "Vulnerabilities to fix: $FIX_COUNT"
echo ""

# Extract vulnerable packages at specified severity
jq -r --arg severity "$SEVERITY_FILTER" '.vulnerabilities | to_entries[] |
    select(.value.severity == "critical" or
           (.value.severity == "high" and ($severity == "high" or $severity == "moderate" or $severity == "all")) or
           (.value.severity == "moderate" and ($severity == "moderate" or $severity == "all")) or
           ($severity == "all")) |
    "\(.value.severity | ascii_upcase): \(.key) - \(.value.via[0].title // "No title")"' \
    /tmp/npm-audit-results.json > /tmp/vulns-to-fix.txt

echo "Vulnerable packages:"
cat /tmp/vulns-to-fix.txt
```

**Success Criteria:** Vulnerabilities filtered by specified severity level, list of packages to fix generated

---

### **Step 3: Attempt automatic fixes (npm audit fix)**

```bash
echo ""
echo "Step 3: Attempting automatic vulnerability fixes..."
echo ""

# Create backup of package files before attempting fixes
cp package.json package.json.backup
cp package-lock.json package-lock.json.backup 2>/dev/null || true

# Attempt automatic fix based on severity
case "$SEVERITY_FILTER" in
    critical|high)
        echo "Running: npm audit fix --audit-level=$SEVERITY_FILTER"
        npm audit fix --audit-level="$SEVERITY_FILTER" > /tmp/npm-audit-fix-output.txt 2>&1
        FIX_EXIT_CODE=$?
        ;;
    moderate|all)
        echo "Running: npm audit fix (all fixable vulnerabilities)"
        npm audit fix > /tmp/npm-audit-fix-output.txt 2>&1
        FIX_EXIT_CODE=$?
        ;;
esac

echo ""
echo "Automatic fix output:"
cat /tmp/npm-audit-fix-output.txt
echo ""

# Check what was fixed
npm audit --json > /tmp/npm-audit-after-fix.json

REMAINING_VULNS=$(jq '.metadata.vulnerabilities.total // 0' /tmp/npm-audit-after-fix.json)
FIXED_COUNT=$((TOTAL_VULNS - REMAINING_VULNS))

echo "Automatic fix results:"
echo "  Fixed: $FIXED_COUNT vulnerabilities"
echo "  Remaining: $REMAINING_VULNS vulnerabilities"
echo ""

if [[ "$REMAINING_VULNS" -gt 0 ]]; then
    echo "Some vulnerabilities require manual intervention (see Step 4)"
fi
```

**Success Criteria:** npm audit fix executed, changes tracked, remaining vulnerabilities identified

---

### **Step 4: Research manual fix paths for non-auto-fixable vulnerabilities**

```bash
echo ""
echo "Step 4: Researching manual fix paths for remaining vulnerabilities..."
echo ""

if [[ "$REMAINING_VULNS" -eq 0 ]]; then
    echo "All vulnerabilities were automatically fixed. Skipping manual research."
else
    # Extract non-fixable vulnerabilities
    jq -r '.vulnerabilities | to_entries[] |
        select(.value.fixAvailable == false or .value.fixAvailable.isSemVerMajor == true) |
        "Package: \(.key)\nSeverity: \(.value.severity)\nReason: \(.value.via[0].title // "No details")\nFix Available: \(.value.fixAvailable)\n---"' \
        /tmp/npm-audit-after-fix.json > /tmp/manual-fixes-needed.txt

    echo "Vulnerabilities requiring manual intervention:"
    cat /tmp/manual-fixes-needed.txt
    echo ""

    # Identify breaking changes
    BREAKING_CHANGES=$(jq -r '.vulnerabilities | to_entries[] |
        select(.value.fixAvailable.isSemVerMajor == true) |
        .key' /tmp/npm-audit-after-fix.json | wc -l)

    if [[ "$BREAKING_CHANGES" -gt 0 ]]; then
        echo "Breaking changes detected: $BREAKING_CHANGES packages require major version updates"
        echo "These will be handled in Step 5 (delegation to dependency specialist)"
    fi

    # Research alternative fix strategies
    echo ""
    echo "Manual fix strategies to consider:"
    echo "1. Update peer dependencies to compatible versions"
    echo "2. Replace vulnerable packages with secure alternatives"
    echo "3. Apply patches using 'patch-package' for unavoidable dependencies"
    echo "4. Temporarily use 'npm audit fix --force' (risky - requires thorough testing)"
fi
```

**Success Criteria:** Non-auto-fixable vulnerabilities identified, manual fix strategies documented, breaking changes flagged

---

### **Step 5: Delegate to dependency specialist for breaking changes**

```bash
echo ""
echo "Step 5: Handling breaking changes..."
echo ""

if [[ "$BREAKING_CHANGES" -gt 0 ]]; then
    echo "Delegation needed: Complex dependency updates with breaking changes"
    echo ""
    echo "For packages requiring major version updates, consult with a dependency management"
    echo "specialist to assess:"
    echo "  - Breaking API changes and migration paths"
    echo "  - Impact on dependent code across the codebase"
    echo "  - Test coverage requirements for validation"
    echo "  - Rollback strategies if issues are discovered"
    echo ""
    echo "Packages requiring specialist review:"
    jq -r '.vulnerabilities | to_entries[] |
        select(.value.fixAvailable.isSemVerMajor == true) |
        "  - \(.key): \(.value.via[0].range // "unknown version range")"' \
        /tmp/npm-audit-after-fix.json
    echo ""
    echo "Specialist should use the architectural validation patterns to ensure"
    echo "that dependency updates maintain system integrity and follow SOLID principles."
    echo ""
    echo "For now, documenting these in the security report for manual review."
else
    echo "No breaking changes detected - all fixes are backward compatible"
fi
```

**Success Criteria:** Breaking changes identified and documented for specialist consultation, backward-compatible fixes ready for testing

---

### **Step 6: Run tests to verify fixes**

```bash
echo ""
echo "Step 6: Running tests to verify vulnerability fixes..."
echo ""

# Run test suite
echo "Running test suite..."
npm test > /tmp/test-results.txt 2>&1
TEST_EXIT_CODE=$?

if [[ "$TEST_EXIT_CODE" -eq 0 ]]; then
    echo "Tests PASSED"
    echo ""
    cat /tmp/test-results.txt
else
    echo "Tests FAILED"
    echo ""
    cat /tmp/test-results.txt
    echo ""
    echo "Test failures detected after vulnerability fixes."
    echo "This may indicate:"
    echo "  1. Breaking changes in updated dependencies"
    echo "  2. Test dependencies need updating"
    echo "  3. Tests are flaky (unrelated to changes)"
    echo ""
    echo "Recommendation: Review test failures and determine if changes should be rolled back."
    echo ""

    # Optionally rollback on test failure
    read -p "Rollback changes due to test failures? [y/N]: " ROLLBACK_CHOICE
    if [[ "$ROLLBACK_CHOICE" =~ ^[Yy]$ ]]; then
        echo "Rolling back package.json changes..."
        mv package.json.backup package.json
        mv package-lock.json.backup package-lock.json 2>/dev/null || true
        npm install
        echo "Rollback complete. Original vulnerability state restored."
        exit 1
    else
        echo "Continuing with fixes despite test failures (proceed with caution)..."
    fi
fi

# Cleanup backup files if tests passed
rm -f package.json.backup package-lock.json.backup
```

**Success Criteria:** Tests execute, results captured, rollback option provided if failures detected

---

### **Step 7: Generate security fix report**

```bash
echo ""
echo "Step 7: Generating security fix report..."
echo ""

REPORT_FILE="/tmp/security-fix-report-$(date +%Y%m%d-%H%M%S).md"

cat > "$REPORT_FILE" <<EOF
# Security Vulnerability Fix Report

**Generated**: $(date)
**Severity Filter**: $SEVERITY_FILTER
**Session ID**: fix-vulns-$(date +%Y%m%d-%H%M%S)

---

## Summary

- **Initial vulnerabilities**: $TOTAL_VULNS
- **Automatically fixed**: $FIXED_COUNT
- **Remaining vulnerabilities**: $REMAINING_VULNS
- **Test status**: $([ "$TEST_EXIT_CODE" -eq 0 ] && echo "PASSED" || echo "FAILED")

---

## Vulnerability Breakdown (Initial)

- Critical: $CRITICAL
- High: $HIGH
- Moderate: $MODERATE
- Low: $LOW

---

## Automatically Fixed

$(if [[ "$FIXED_COUNT" -gt 0 ]]; then
    echo "The following vulnerabilities were automatically resolved:"
    echo ""
    git diff package.json package-lock.json | grep -E "^\+|^-" | head -20
else
    echo "No vulnerabilities were automatically fixed."
fi)

---

## Manual Intervention Required

$(if [[ -f /tmp/manual-fixes-needed.txt ]]; then
    cat /tmp/manual-fixes-needed.txt
else
    echo "No manual fixes required - all vulnerabilities resolved automatically!"
fi)

---

## Breaking Changes

$(if [[ "$BREAKING_CHANGES" -gt 0 ]]; then
    echo "The following packages require major version updates and specialist review:"
    echo ""
    jq -r '.vulnerabilities | to_entries[] |
        select(.value.fixAvailable.isSemVerMajor == true) |
        "- **\(.key)**: \(.value.via[0].title // "No details")"' \
        /tmp/npm-audit-after-fix.json
else
    echo "No breaking changes detected."
fi)

---

## Test Results

$(cat /tmp/test-results.txt | tail -20)

---

## Recommendations

$(if [[ "$REMAINING_VULNS" -gt 0 ]]; then
    echo "1. **IMMEDIATE**: Review manual fix strategies for $REMAINING_VULNS remaining vulnerabilities"
    echo "2. **HIGH PRIORITY**: Consult dependency specialist for breaking changes"
    echo "3. **NEXT STEPS**: Run comprehensive integration tests before merging"
else
    echo "1. All vulnerabilities resolved successfully"
    echo "2. Review PR changes and approve for merge"
    echo "3. Deploy with confidence - no remaining security issues at $SEVERITY_FILTER level"
fi)

---

## Next Steps

- [ ] Review this security fix report
- [ ] Verify all tests pass
- [ ] Review PR changes for breaking changes
- [ ] Approve and merge PR
- [ ] Monitor production for any issues

---

**Report Location**: $REPORT_FILE
EOF

echo "Security fix report generated: $REPORT_FILE"
echo ""
cat "$REPORT_FILE"
```

**Success Criteria:** Comprehensive security report generated with all findings, fixes, and recommendations

---

### **Step 8: Create PR with vulnerability fixes**

```bash
echo ""
echo "Step 8: Creating pull request with vulnerability fixes..."
echo ""

# Check if on a branch or need to create one
CURRENT_BRANCH=$(git branch --show-current)

if [[ "$CURRENT_BRANCH" == "main" ]] || [[ "$CURRENT_BRANCH" == "master" ]]; then
    # Create new branch for fixes
    FIX_BRANCH="security/fix-vulnerabilities-$(date +%Y%m%d-%H%M%S)"
    echo "Creating new branch: $FIX_BRANCH"
    git checkout -b "$FIX_BRANCH"
else
    FIX_BRANCH="$CURRENT_BRANCH"
    echo "Using existing branch: $FIX_BRANCH"
fi

# Stage changes
git add package.json package-lock.json

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "No changes to commit. All vulnerabilities may have been previously fixed."
    exit 0
fi

# Commit changes
git commit -m "$(cat <<'EOF'
fix: Resolve npm security vulnerabilities

Automated security vulnerability remediation via /fix-vulns workflow.

Summary:
- Fixed: $FIXED_COUNT vulnerabilities
- Remaining: $REMAINING_VULNS vulnerabilities
- Severity filter: $SEVERITY_FILTER
- Test status: $([ "$TEST_EXIT_CODE" -eq 0 ] && echo "PASSED" || echo "REQUIRES REVIEW")

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push branch
git push -u origin "$FIX_BRANCH"

# Create PR using gh cli
gh pr create \
    --title "fix: Resolve $SEVERITY_FILTER npm security vulnerabilities" \
    --body "$(cat <<EOF
## Summary

Automated security vulnerability remediation for **$SEVERITY_FILTER** severity vulnerabilities.

- **Initial vulnerabilities**: $TOTAL_VULNS
- **Fixed**: $FIXED_COUNT
- **Remaining**: $REMAINING_VULNS
- **Test status**: $([ "$TEST_EXIT_CODE" -eq 0 ] && echo "PASSED" || echo "FAILED - REVIEW REQUIRED")

---

## Changes

This PR includes:
- Updated dependencies to resolve known security vulnerabilities
- Automated fixes via \`npm audit fix\`
- Test validation to ensure no regressions

---

## Vulnerability Details

### Severity Breakdown (Initial)
- Critical: $CRITICAL
- High: $HIGH
- Moderate: $MODERATE
- Low: $LOW

### Remaining Vulnerabilities
$(if [[ "$REMAINING_VULNS" -gt 0 ]]; then
    echo "$REMAINING_VULNS vulnerabilities require manual intervention or specialist review."
    echo "See security report for details."
else
    echo "All vulnerabilities at $SEVERITY_FILTER level have been resolved!"
fi)

---

## Test Results

$(if [[ "$TEST_EXIT_CODE" -eq 0 ]]; then
    echo "All tests passed - changes are safe to merge."
else
    echo "CAUTION: Some tests failed. Review required before merging."
fi)

---

## Review Checklist

- [ ] Verify npm audit shows reduced vulnerability count
- [ ] All tests pass (CI/CD)
- [ ] No breaking changes in application behavior
- [ ] Dependencies are compatible with existing code
- [ ] Security report reviewed

---

## Security Report

Full security report available at: $REPORT_FILE

---

Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"

echo ""
echo "Pull request created successfully!"
echo "Branch: $FIX_BRANCH"
echo "Review the PR and merge once CI passes."
```

**Success Criteria:** Git branch created (if needed), changes committed, PR created with comprehensive security details

---

## Arguments

### `--severity=<value>` (optional, default: "high")

Minimum severity level to fix:
- **critical**: Fix only critical vulnerabilities
- **high**: Fix critical and high vulnerabilities (default)
- **moderate**: Fix critical, high, and moderate vulnerabilities
- **all**: Fix all vulnerabilities regardless of severity

---

## Usage Examples

```bash
# Fix critical and high vulnerabilities (default)
/fix-vulns

# Fix only critical vulnerabilities
/fix-vulns --severity=critical

# Fix critical, high, and moderate vulnerabilities
/fix-vulns --severity=moderate

# Fix all vulnerabilities
/fix-vulns --severity=all
```

---

## Expected Outcomes

### Success

All vulnerabilities at specified severity level are fixed, tests pass, comprehensive security report generated, PR created for review.

### Partial Success

Some vulnerabilities fixed automatically, others require manual intervention or breaking changes that need specialist review. Report documents what was fixed and what needs attention.

### Failure

- npm audit fails to run (missing dependencies, network issues)
- Automatic fixes cause test failures requiring rollback
- No vulnerabilities found at specified severity level
- Git/GitHub operations fail (branch conflicts, authentication issues)

---

## Integration Points

### OrchestratorAgent

Can be called by orchestrator for:
- Scheduled security maintenance workflows
- Pre-deployment security checks
- Post-dependency-update validation
- Automated security remediation pipelines

### Related Commands

Works in conjunction with:
- `/audit` - For comprehensive security analysis before fixes
- `/pr-process` - For PR review and merge workflow
- `/test-all` - For comprehensive test validation after fixes

---

## Safety

- Creates backup of package files before modifications
- Provides rollback option if tests fail
- Never forces breaking changes without documentation
- Always creates PR for review (no direct commits to main)
- Documents all changes in security report
- Delegates complex decisions to specialists

---

## Success Criteria

- [x] npm audit executed successfully
- [x] Vulnerabilities categorized by severity
- [x] Automatic fixes attempted
- [x] Manual fix paths researched
- [x] Breaking changes identified and documented
- [x] Tests executed and validated
- [x] Security report generated
- [x] PR created with comprehensive details

---

## Related Commands & Agents

**Commands:**
- `/audit` - Comprehensive code audit (includes security analysis)
- `/pr-process` - PR creation and merge workflow
- `/test-all` - Run comprehensive test suite
- `/issue-create` - Create GitHub issues for manual fixes

**Agents:**
- AuditAgent - Can include security vulnerability analysis
- ImplementationAgent - Can handle breaking changes and refactoring
- ArchitectAgent - Can validate architectural impact of dependency updates

---

## Notes

### Best Practices

1. **Run /audit first**: Get comprehensive security overview before fixing
2. **Start conservative**: Use `--severity=critical` for first pass
3. **Test thoroughly**: Always run full test suite after fixes
4. **Review breaking changes**: Never merge major version updates without specialist review
5. **Schedule regularly**: Run weekly or bi-weekly for proactive security

### Limitations

- Only works with npm projects (package.json required)
- Cannot fix vulnerabilities in transitive dependencies with no update path
- Breaking changes require manual review and testing
- Some vulnerabilities may require code changes beyond dependency updates

### Troubleshooting

**Issue**: Tests fail after automatic fixes
- **Solution**: Use rollback option, review test failures, fix compatibility issues

**Issue**: Remaining vulnerabilities after automatic fixes
- **Solution**: Review manual fix strategies in report, consult dependency specialist

**Issue**: PR creation fails
- **Solution**: Ensure `gh` CLI is authenticated, check branch permissions

### Integration with CI/CD

Can be integrated into automated pipelines:
```yaml
# .github/workflows/security-maintenance.yml
name: Weekly Security Updates
on:
  schedule:
    - cron: '0 0 * * 1'  # Every Monday
jobs:
  fix-vulnerabilities:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Fix vulnerabilities
        run: /fix-vulns --severity=high
```

---

**Remember**: Security is not a one-time task - make vulnerability remediation part of your regular development workflow.
