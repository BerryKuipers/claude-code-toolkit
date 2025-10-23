# Update Dependencies - Safe Dependency Update Workflow

**Arguments:** [--scope=all|security|outdated] [--auto-test]

**Success Criteria:** Dependencies updated successfully with all tests passing, or rolled back on failure

**Description:** Safely update project dependencies with incremental testing and automatic rollback on failure

---

## Purpose

Perform safe, incremental dependency updates with comprehensive testing to prevent breaking changes. Updates can be scoped to security vulnerabilities only, outdated packages, or all dependencies. Includes automatic rollback on test failures and generates detailed update reports.

---

## Important: Workflow Scope

**This command executes a multi-step dependency update workflow:**
- ✅ Identifies and applies dependency updates incrementally
- ✅ Runs tests after each update to validate stability
- ✅ Automatically rolls back failed updates
- ✅ Generates comprehensive update reports
- ❌ Does NOT orchestrate other commands (use orchestrator for complex coordination)
- ❌ Does NOT modify application code (only package files)

---

## Workflow

### **Step 1: Check Current Dependency Status**

```bash
echo "========================================="
echo "Step 1: Checking Current Dependency Status"
echo "========================================="

# Determine package manager
if [ -f "package-lock.json" ]; then
    PKG_MANAGER="npm"
elif [ -f "yarn.lock" ]; then
    PKG_MANAGER="yarn"
elif [ -f "pnpm-lock.yaml" ]; then
    PKG_MANAGER="pnpm"
else
    echo "❌ Error: No package manager lock file found"
    exit 1
fi

echo "✅ Detected package manager: $PKG_MANAGER"

# Create backup directory
mkdir -p .claude/dependency-updates
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=".claude/dependency-updates/backup_${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"

# Backup current state
echo "📦 Creating backup..."
cp package.json "$BACKUP_DIR/package.json"
cp package-lock.json "$BACKUP_DIR/package-lock.json" 2>/dev/null || true
cp yarn.lock "$BACKUP_DIR/yarn.lock" 2>/dev/null || true
cp pnpm-lock.yaml "$BACKUP_DIR/pnpm-lock.yaml" 2>/dev/null || true

echo "✅ Backup created at: $BACKUP_DIR"
```

**Success Criteria:** Package manager identified and current state backed up

---

### **Step 2: Identify Updates Needed**

```bash
echo ""
echo "========================================="
echo "Step 2: Identifying Updates Needed"
echo "========================================="

# Run security audit
echo "🔍 Running security audit..."
if [ "$PKG_MANAGER" = "npm" ]; then
    npm audit --json > .claude/dependency-updates/audit.json 2>&1 || true
    npm outdated --json > .claude/dependency-updates/outdated.json 2>&1 || true
elif [ "$PKG_MANAGER" = "yarn" ]; then
    yarn audit --json > .claude/dependency-updates/audit.json 2>&1 || true
    yarn outdated --json > .claude/dependency-updates/outdated.json 2>&1 || true
elif [ "$PKG_MANAGER" = "pnpm" ]; then
    pnpm audit --json > .claude/dependency-updates/audit.json 2>&1 || true
    pnpm outdated --json > .claude/dependency-updates/outdated.json 2>&1 || true
fi

# Parse vulnerability counts
if [ -f .claude/dependency-updates/audit.json ]; then
    CRITICAL=$(jq '.metadata.vulnerabilities.critical // 0' .claude/dependency-updates/audit.json 2>/dev/null || echo "0")
    HIGH=$(jq '.metadata.vulnerabilities.high // 0' .claude/dependency-updates/audit.json 2>/dev/null || echo "0")
    MODERATE=$(jq '.metadata.vulnerabilities.moderate // 0' .claude/dependency-updates/audit.json 2>/dev/null || echo "0")
    LOW=$(jq '.metadata.vulnerabilities.low // 0' .claude/dependency-updates/audit.json 2>/dev/null || echo "0")
    TOTAL=$(jq '.metadata.vulnerabilities.total // 0' .claude/dependency-updates/audit.json 2>/dev/null || echo "0")

    echo "📊 Vulnerability Summary:"
    echo "   Critical: $CRITICAL"
    echo "   High: $HIGH"
    echo "   Moderate: $MODERATE"
    echo "   Low: $LOW"
    echo "   Total: $TOTAL"
fi

# Parse outdated packages
if [ -f .claude/dependency-updates/outdated.json ]; then
    OUTDATED_COUNT=$(jq 'length' .claude/dependency-updates/outdated.json 2>/dev/null || echo "0")
    echo "📦 Outdated packages: $OUTDATED_COUNT"
fi
```

**Success Criteria:** Audit and outdated package analysis completed, vulnerability counts identified

---

### **Step 3: Generate Update Plan**

```bash
echo ""
echo "========================================="
echo "Step 3: Generating Update Plan"
echo "========================================="

# Determine scope (from --scope argument, default to 'security')
SCOPE="${1:-security}"

echo "🎯 Update scope: $SCOPE"

# Generate update list based on scope
UPDATE_LIST=".claude/dependency-updates/update-plan.json"

if [ "$SCOPE" = "security" ]; then
    echo "🔒 Planning security updates only..."
    # Extract vulnerable packages
    if [ "$TOTAL" -gt 0 ]; then
        jq -r '.vulnerabilities | to_entries | map({
            name: .key,
            severity: .value.severity,
            current: .value.range,
            fixAvailable: .value.fixAvailable
        }) | map(select(.severity == "critical" or .severity == "high"))' \
        .claude/dependency-updates/audit.json > "$UPDATE_LIST"
    else
        echo "[]" > "$UPDATE_LIST"
    fi
elif [ "$SCOPE" = "outdated" ]; then
    echo "📅 Planning outdated package updates..."
    # Use outdated.json directly
    cp .claude/dependency-updates/outdated.json "$UPDATE_LIST"
elif [ "$SCOPE" = "all" ]; then
    echo "🚀 Planning all available updates..."
    # Combine security and outdated
    jq -s 'add' .claude/dependency-updates/audit.json .claude/dependency-updates/outdated.json > "$UPDATE_LIST" 2>/dev/null || \
    cp .claude/dependency-updates/outdated.json "$UPDATE_LIST"
fi

UPDATE_COUNT=$(jq 'length' "$UPDATE_LIST" 2>/dev/null || echo "0")
echo "✅ Update plan generated: $UPDATE_COUNT package(s) to update"

# Show preview
if [ "$UPDATE_COUNT" -gt 0 ]; then
    echo ""
    echo "📋 Updates planned:"
    jq -r '.[] | "   - \(.name // .package): \(.current // .from) → \(.latest // .to)"' "$UPDATE_LIST" 2>/dev/null || \
    jq -r 'to_entries | .[] | "   - \(.key): \(.value.current) → \(.value.latest)"' "$UPDATE_LIST" 2>/dev/null || \
    echo "   (See $UPDATE_LIST for details)"
fi
```

**Success Criteria:** Update plan generated based on scope, update count identified

---

### **Step 4: Apply Updates Incrementally**

```bash
echo ""
echo "========================================="
echo "Step 4: Applying Updates Incrementally"
echo "========================================="

# Check if auto-test flag is set (from --auto-test argument)
AUTO_TEST="${2:-false}"

if [ "$UPDATE_COUNT" -eq 0 ]; then
    echo "✅ No updates needed - all dependencies are current"
    exit 0
fi

# Initialize update tracking
UPDATE_LOG=".claude/dependency-updates/update-log_${TIMESTAMP}.jsonl"
FAILED_UPDATES=0
SUCCESSFUL_UPDATES=0

echo "🔄 Starting incremental updates..."
echo "   Auto-test enabled: $AUTO_TEST"
echo ""

# Function to apply single update
apply_update() {
    local pkg_name="$1"
    local pkg_version="$2"

    echo "→ Updating $pkg_name..."

    if [ "$PKG_MANAGER" = "npm" ]; then
        npm install "$pkg_name@$pkg_version" --save 2>&1
    elif [ "$PKG_MANAGER" = "yarn" ]; then
        yarn upgrade "$pkg_name@$pkg_version" 2>&1
    elif [ "$PKG_MANAGER" = "pnpm" ]; then
        pnpm update "$pkg_name@$pkg_version" 2>&1
    fi

    return $?
}

# Process each update
jq -c '.[]' "$UPDATE_LIST" | while IFS= read -r update; do
    PKG_NAME=$(echo "$update" | jq -r '.name // .package // empty')
    PKG_VERSION=$(echo "$update" | jq -r '.latest // .to // empty')

    if [ -z "$PKG_NAME" ]; then
        # Try alternative parsing for npm outdated format
        PKG_NAME=$(echo "$update" | jq -r 'keys[0]')
        PKG_VERSION=$(echo "$update" | jq -r '.[keys[0]].latest')
    fi

    if [ -n "$PKG_NAME" ] && [ -n "$PKG_VERSION" ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        if apply_update "$PKG_NAME" "$PKG_VERSION"; then
            echo "✅ Successfully updated $PKG_NAME to $PKG_VERSION"

            # Log success
            echo "{\"timestamp\":\"$(date -Iseconds)\",\"package\":\"$PKG_NAME\",\"version\":\"$PKG_VERSION\",\"status\":\"success\"}" >> "$UPDATE_LOG"

            SUCCESSFUL_UPDATES=$((SUCCESSFUL_UPDATES + 1))
        else
            echo "❌ Failed to update $PKG_NAME"

            # Log failure
            echo "{\"timestamp\":\"$(date -Iseconds)\",\"package\":\"$PKG_NAME\",\"version\":\"$PKG_VERSION\",\"status\":\"failed\"}" >> "$UPDATE_LOG"

            FAILED_UPDATES=$((FAILED_UPDATES + 1))
        fi

        echo ""
    fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Update Summary:"
echo "   ✅ Successful: $SUCCESSFUL_UPDATES"
echo "   ❌ Failed: $FAILED_UPDATES"
```

**Success Criteria:** All planned updates applied, success/failure tracked for each package

---

### **Step 5: Run Tests After Updates**

```bash
echo ""
echo "========================================="
echo "Step 5: Running Tests After Updates"
echo "========================================="

if [ "$AUTO_TEST" != "true" ] && [ "$AUTO_TEST" != "--auto-test" ]; then
    echo "⏭️  Auto-test disabled - skipping test execution"
    echo "   Run tests manually: npm test"
    TEST_RESULT="skipped"
else
    echo "🧪 Running test suite..."

    # Detect test command
    TEST_CMD=$(jq -r '.scripts.test // empty' package.json)

    if [ -z "$TEST_CMD" ]; then
        echo "⚠️  No test script found in package.json"
        echo "   Skipping test execution"
        TEST_RESULT="no-tests"
    else
        echo "   Command: $PKG_MANAGER test"

        # Run tests with timeout
        if timeout 300 $PKG_MANAGER test > .claude/dependency-updates/test-output.log 2>&1; then
            echo "✅ All tests passed"
            TEST_RESULT="passed"
        else
            echo "❌ Tests failed"
            echo "   See logs: .claude/dependency-updates/test-output.log"
            TEST_RESULT="failed"

            # Show last 20 lines of test output
            echo ""
            echo "Last 20 lines of test output:"
            tail -n 20 .claude/dependency-updates/test-output.log
        fi
    fi
fi

# Save test result
echo "{\"timestamp\":\"$(date -Iseconds)\",\"result\":\"$TEST_RESULT\"}" > .claude/dependency-updates/test-result.json
```

**Success Criteria:** Tests executed (if enabled), results logged, test failures identified

---

### **Step 6: Rollback if Tests Fail**

```bash
echo ""
echo "========================================="
echo "Step 6: Rollback Check"
echo "========================================="

if [ "$TEST_RESULT" = "failed" ]; then
    echo "⚠️  Tests failed - initiating rollback..."

    # Restore from backup
    echo "🔄 Restoring package files from backup..."
    cp "$BACKUP_DIR/package.json" package.json
    cp "$BACKUP_DIR/package-lock.json" package-lock.json 2>/dev/null || true
    cp "$BACKUP_DIR/yarn.lock" yarn.lock 2>/dev/null || true
    cp "$BACKUP_DIR/pnpm-lock.yaml" pnpm-lock.yaml 2>/dev/null || true

    # Reinstall from restored lock file
    echo "📦 Reinstalling dependencies..."
    if [ "$PKG_MANAGER" = "npm" ]; then
        npm ci
    elif [ "$PKG_MANAGER" = "yarn" ]; then
        yarn install --frozen-lockfile
    elif [ "$PKG_MANAGER" = "pnpm" ]; then
        pnpm install --frozen-lockfile
    fi

    echo "✅ Rollback complete - restored to pre-update state"
    echo "   Review test failures in: .claude/dependency-updates/test-output.log"

    ROLLBACK_PERFORMED="true"
else
    echo "✅ No rollback needed"
    if [ "$TEST_RESULT" = "passed" ]; then
        echo "   Tests passed - updates are stable"
    elif [ "$TEST_RESULT" = "skipped" ] || [ "$TEST_RESULT" = "no-tests" ]; then
        echo "   Tests were not run - verify manually"
    fi

    ROLLBACK_PERFORMED="false"
fi
```

**Success Criteria:** Rollback executed successfully if tests failed, or confirmed not needed

---

### **Step 7: Generate Update Report**

```bash
echo ""
echo "========================================="
echo "Step 7: Generating Update Report"
echo "========================================="

REPORT_FILE=".claude/dependency-updates/report_${TIMESTAMP}.md"

cat > "$REPORT_FILE" << EOF
# Dependency Update Report

**Timestamp**: $(date -Iseconds)
**Scope**: $SCOPE
**Package Manager**: $PKG_MANAGER
**Auto-Test**: $AUTO_TEST

---

## Summary

- **Updates Planned**: $UPDATE_COUNT
- **Successful Updates**: $SUCCESSFUL_UPDATES
- **Failed Updates**: $FAILED_UPDATES
- **Test Result**: $TEST_RESULT
- **Rollback Performed**: $ROLLBACK_PERFORMED

---

## Vulnerability Status (Before Updates)

- **Critical**: $CRITICAL
- **High**: $HIGH
- **Moderate**: $MODERATE
- **Low**: $LOW
- **Total**: $TOTAL

---

## Updates Applied

EOF

if [ -f "$UPDATE_LOG" ]; then
    echo "### Successful Updates" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    jq -r 'select(.status == "success") | "- ✅ \(.package)@\(.version) at \(.timestamp)"' "$UPDATE_LOG" >> "$REPORT_FILE" 2>/dev/null || echo "None" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    echo "### Failed Updates" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    jq -r 'select(.status == "failed") | "- ❌ \(.package)@\(.version) at \(.timestamp)"' "$UPDATE_LOG" >> "$REPORT_FILE" 2>/dev/null || echo "None" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

---

## Test Results

**Status**: $TEST_RESULT

EOF

if [ "$TEST_RESULT" = "failed" ]; then
    echo "### Test Output (Last 50 lines)" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"
    tail -n 50 .claude/dependency-updates/test-output.log >> "$REPORT_FILE" 2>/dev/null || echo "No output available" >> "$REPORT_FILE"
    echo "\`\`\`" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << EOF

---

## Backup Location

\`$BACKUP_DIR\`

---

## Next Steps

EOF

if [ "$ROLLBACK_PERFORMED" = "true" ]; then
    cat >> "$REPORT_FILE" << EOF
⚠️  **Rollback was performed due to test failures**

1. Review test failures in: \`.claude/dependency-updates/test-output.log\`
2. Investigate which update caused the failure
3. Fix application code or update dependencies individually
4. Re-run with: \`/update-deps --scope=$SCOPE --auto-test\`
EOF
elif [ "$FAILED_UPDATES" -gt 0 ]; then
    cat >> "$REPORT_FILE" << EOF
⚠️  **Some updates failed to apply**

1. Review failed updates above
2. Check for dependency conflicts
3. May need to update manually or resolve conflicts
EOF
elif [ "$TEST_RESULT" = "skipped" ] || [ "$TEST_RESULT" = "no-tests" ]; then
    cat >> "$REPORT_FILE" << EOF
✅ **Updates applied successfully**

⚠️  Tests were not run - please verify manually:

1. Run test suite: \`$PKG_MANAGER test\`
2. Verify application behavior
3. If tests pass, consider creating a PR
EOF
else
    cat >> "$REPORT_FILE" << EOF
✅ **Updates completed successfully with all tests passing**

1. Review changes: \`git diff package.json\`
2. Commit changes: \`git add package.json package-lock.json && git commit -m "chore: update dependencies"\`
3. Consider creating PR with: \`/pr-process\`
EOF
fi

echo "✅ Report generated: $REPORT_FILE"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$REPORT_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

**Success Criteria:** Comprehensive update report generated with all results, next steps, and recommendations

---

### **Step 8: Optionally Create PR**

```bash
echo ""
echo "========================================="
echo "Step 8: PR Creation (Optional)"
echo "========================================="

# Only offer PR creation if updates were successful and not rolled back
if [ "$ROLLBACK_PERFORMED" = "false" ] && [ "$SUCCESSFUL_UPDATES" -gt 0 ]; then
    echo "📝 Updates were successful!"
    echo ""
    echo "To create a PR with these changes, run:"
    echo "   /pr-process"
    echo ""
    echo "Or manually:"
    echo "   git add package.json package-lock.json"
    echo "   git commit -m 'chore: update dependencies ($SCOPE scope)'"
    echo "   git push"
    echo "   gh pr create --title 'chore: Update dependencies' --body \"\$(cat $REPORT_FILE)\""
else
    echo "⏭️  Skipping PR creation"
    if [ "$ROLLBACK_PERFORMED" = "true" ]; then
        echo "   Reason: Rollback was performed"
    elif [ "$SUCCESSFUL_UPDATES" -eq 0 ]; then
        echo "   Reason: No updates were applied"
    fi
fi

echo ""
echo "✅ Dependency update workflow complete"
```

**Success Criteria:** PR creation guidance provided, or skipped with clear reasoning

---

## Arguments

### `--scope` (optional)

Defines which dependencies to update:

- **`security`** (default): Only update packages with critical or high severity vulnerabilities
- **`outdated`**: Update all outdated packages (patch and minor versions preferred)
- **`all`**: Update all dependencies including security and outdated packages

**Example:**
```bash
/update-deps --scope=security
/update-deps --scope=outdated
/update-deps --scope=all
```

### `--auto-test` (optional)

When provided, automatically runs the test suite after applying updates:

- **Not provided** (default): Skip test execution, manual verification required
- **Provided**: Run `npm test` (or equivalent) after updates, rollback on failure

**Example:**
```bash
/update-deps --auto-test
/update-deps --scope=all --auto-test
```

---

## Usage Examples

### Example 1: Security Updates Only (Safe Default)

```bash
/update-deps
# or explicitly
/update-deps --scope=security
```

**Use when:**
- Critical security vulnerabilities need immediate patching
- Minimal risk tolerance
- Production environments

**Expected outcome:**
- Only critical/high severity vulnerabilities updated
- No major version changes
- Minimal breaking change risk

---

### Example 2: Security Updates with Automatic Testing

```bash
/update-deps --scope=security --auto-test
```

**Use when:**
- You have comprehensive test coverage
- Want automated validation
- Prefer automatic rollback on test failures

**Expected outcome:**
- Security updates applied incrementally
- Tests run after all updates
- Automatic rollback if any test fails
- Detailed report of results

---

### Example 3: Update All Outdated Packages

```bash
/update-deps --scope=outdated --auto-test
```

**Use when:**
- Regular maintenance window
- Keeping dependencies current
- Have good test coverage

**Expected outcome:**
- All outdated packages updated to latest
- May include major version updates (review breaking changes)
- Tests validate stability
- Rollback on failure

---

### Example 4: Comprehensive Update (All Dependencies)

```bash
/update-deps --scope=all --auto-test
```

**Use when:**
- Major maintenance sprint
- Starting new development cycle
- Maximum currency desired

**Expected outcome:**
- Security vulnerabilities fixed
- All outdated packages updated
- Comprehensive testing
- Detailed report with recommendations

---

## Expected Outcomes

### Success (No Rollback)

```markdown
✅ Dependency update workflow complete

Summary:
- Updates Planned: 12
- Successful Updates: 12
- Failed Updates: 0
- Test Result: passed
- Rollback Performed: false

Next Steps:
1. Review changes: git diff package.json
2. Commit changes
3. Create PR with: /pr-process
```

### Partial Success (Some Updates Failed)

```markdown
⚠️  Partial success

Summary:
- Updates Planned: 12
- Successful Updates: 10
- Failed Updates: 2
- Test Result: passed
- Rollback Performed: false

Next Steps:
1. Review failed updates in report
2. Investigate dependency conflicts
3. May need manual resolution
```

### Failure with Rollback

```markdown
❌ Tests failed - rollback performed

Summary:
- Updates Planned: 12
- Successful Updates: 12
- Failed Updates: 0
- Test Result: failed
- Rollback Performed: true

Next Steps:
1. Review test failures in log
2. Identify breaking update
3. Fix application code or update individually
4. Re-run with: /update-deps --scope=security --auto-test
```

### No Updates Needed

```markdown
✅ No updates needed

Summary:
- Updates Planned: 0
- All dependencies are current
- No security vulnerabilities

Next Steps:
- None required - dependencies are up to date
```

---

## Integration Points

### Commands this workflow can invoke:

- `/pr-process` - To create pull request with dependency updates (suggested in output)

### Skills this workflow uses:

- `audit-dependencies` - Conceptually similar (this workflow includes that functionality)

### When orchestrator might invoke this:

- Security maintenance tasks requiring dependency updates
- Pre-deployment security validation workflows
- Automated maintenance schedules
- When security vulnerabilities are detected by audit agents

---

## Safety

### Automatic Backups

- All package files backed up before any changes
- Backup location: `.claude/dependency-updates/backup_TIMESTAMP/`
- Backups preserved even after successful updates

### Incremental Updates

- Each package updated individually (not all at once)
- Failures isolated to single packages
- Continue processing remaining updates on individual failures

### Automatic Rollback

- Triggered only on test failures (when `--auto-test` enabled)
- Restores exact pre-update state from backup
- Uses `npm ci` / `yarn install --frozen-lockfile` for deterministic restore

### Test Isolation

- 5-minute timeout prevents hanging tests
- Test output logged for review
- Tests skipped by default (opt-in with `--auto-test`)

### What is Safe

- ✅ Running with `--scope=security` (minimal changes)
- ✅ Running without `--auto-test` (manual verification)
- ✅ Reviewing update plan before applying (shown in Step 3)
- ✅ All operations are reversible (backups preserved)

### What to Avoid

- ❌ Running `--scope=all` without review on production
- ❌ Ignoring failed updates (investigate before retry)
- ❌ Deleting backup directories (keep until verified)
- ❌ Force-pushing update commits without team review

---

## Success Criteria

- [x] Package manager detected correctly
- [x] Current state backed up successfully
- [x] Audit and outdated analysis completed
- [x] Update plan generated based on scope
- [x] Updates applied incrementally with tracking
- [x] Tests executed (if auto-test enabled) or skipped with notification
- [x] Rollback performed on test failure (if applicable)
- [x] Comprehensive report generated
- [x] Next steps clearly communicated
- [x] PR creation guidance provided

---

## Related Commands & Agents

### Commands

- `/pr-process` - Create pull request with dependency updates
- `/issue-create` - Create issue for failed updates requiring investigation
- `/test-all` - Manually run comprehensive test suite

### Agents

- **Security Agent** (security-pentest.md) - May invoke this for vulnerability remediation
- **Infrastructure Agent** - May invoke this for dependency conflict resolution
- **Orchestrator Agent** - May invoke this as part of security maintenance workflows

### Skills

- `audit-dependencies` - Security audit functionality (similar to Steps 1-2)

---

## Notes

### Package Manager Support

This workflow supports:
- **npm** - `package-lock.json` detection
- **yarn** - `yarn.lock` detection
- **pnpm** - `pnpm-lock.yaml` detection

Auto-detects based on lock file presence.

### Scope Recommendations

- **Development**: Use `--scope=outdated` regularly
- **Staging**: Use `--scope=security` before deployments
- **Production**: Use `--scope=security` only, with manual review
- **Maintenance**: Use `--scope=all` during designated windows

### Test Strategy

- **With tests**: Always use `--auto-test` for safety
- **Without tests**: Skip auto-test, verify manually thoroughly
- **Partial coverage**: Use `--auto-test`, but also manual verification

### Handling Major Updates

Major version updates may include breaking changes:

1. Review changelog for breaking changes
2. Update application code if needed
3. Run with `--auto-test` to validate
4. Consider separate PR for major updates

### Files Generated

All outputs saved to `.claude/dependency-updates/`:

- `backup_TIMESTAMP/` - Backup of package files
- `audit.json` - Security audit results
- `outdated.json` - Outdated package list
- `update-plan.json` - Generated update plan
- `update-log_TIMESTAMP.jsonl` - Update execution log
- `test-result.json` - Test execution result
- `test-output.log` - Full test output (if tests run)
- `report_TIMESTAMP.md` - Human-readable report

### Cleanup

Backups are preserved indefinitely. To clean old backups:

```bash
# Remove backups older than 30 days
find .claude/dependency-updates/backup_* -type d -mtime +30 -exec rm -rf {} +
```

---

## Troubleshooting

### "No package manager lock file found"

**Cause**: No `package-lock.json`, `yarn.lock`, or `pnpm-lock.yaml` found

**Solution**: Run package manager install first:
```bash
npm install  # or yarn install / pnpm install
```

### Updates fail with dependency conflicts

**Cause**: Incompatible version requirements between packages

**Solution**:
1. Review error messages in update log
2. Update conflicting packages manually
3. Use `npm ls <package>` to see dependency tree
4. Consider updating parent dependencies first

### Tests timeout after 5 minutes

**Cause**: Test suite takes longer than 5-minute limit

**Solution**:
1. Run without `--auto-test`
2. Manually run tests after updates
3. Or optimize test suite performance

### Rollback fails

**Cause**: Backup files missing or corrupted

**Solution**:
1. Check backup directory exists: `.claude/dependency-updates/backup_TIMESTAMP/`
2. Manually restore from backup
3. Or restore from git: `git checkout package.json package-lock.json`

---

**Remember**: This workflow prioritizes safety over speed. Always review the update plan, use backups, and validate with tests before committing dependency changes.
