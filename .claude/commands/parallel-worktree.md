# Parallel Worktree Command

Create two separate git worktrees for parallel development on compatible issues, with automatic issue selection and branch management.

## Instructions

**Arguments:**
- `issue1` *(optional)*: First issue number
- `issue2` *(optional)*: Second issue number
- `baseBranch` *(optional, default: development)*: Base branch for new branches
- `workdir` *(optional, default: ../)*: Parent directory for worktrees

If no issues provided, automatically selects 2 suitable issues using the smart issue-picker algorithm.

### Step 1: Issue Selection and Conflict Analysis

If both `issue1` and `issue2` are provided, use those. Otherwise:

1. **Fetch all open issues with smart prioritization:**
   ```bash
   gh issue list --state open --limit 100 --json number,title,labels,assignees,createdAt,body
   ```

2. **Apply intelligent issue selection for parallel work:**
   - Use same priority algorithm as `/issue-pickup` command
   - **Additional parallel work criteria:**
     - Issues must be in different areas (`area:backend` vs `area:frontend`)
     - No shared file dependencies (different feature slices)
     - No blocking dependencies between selected issues
     - Both must be unassigned or assignable to current user

3. **Conflict detection algorithm:**
   ```bash
   # For each issue pair candidate, analyze potential conflicts:
   # - Parse issue bodies for mentioned file paths
   # - Check if both touch same architectural layers
   # - Verify no dependency chains exist between them
   # - Ensure both can run independent test suites
   ```

4. **Present selection with parallel work analysis:**
   ```
   🎯 Selected Issues for Parallel Development:

   💼 Worktree 1: Issue #XX - [TITLE]
   📊 Priority: P1 (High) | Area: Backend API
   📁 Expected files: services/api/src/features/profile/
   🔗 Dependencies: None (ready to implement)

   🎨 Worktree 2: Issue #YY - [TITLE]
   📊 Priority: P1 (High) | Area: Frontend UI
   📁 Expected files: apps/web/src/features/auth/
   🔗 Dependencies: None (ready to implement)

   ✅ Conflict Analysis: NO conflicts detected
   - Different architectural areas (API vs UI)
   - No shared file dependencies
   - Independent test suites
   - Can be developed in parallel safely

   Estimated parallel efficiency: 85% (high compatibility)
   ```

5. **Request user confirmation before proceeding**

### Step 2: Worktree Creation and Setup

1. **Validate base branch and working directory:**
   ```bash
   # Ensure base branch exists and is up to date
   git fetch origin $baseBranch
   git checkout $baseBranch
   git pull origin $baseBranch

   # Validate working directory
   WORKDIR=$(realpath "$workdir")
   if [[ ! -d "$WORKDIR" ]]; then
     mkdir -p "$WORKDIR"
   fi
   echo "✅ Base: $baseBranch | Workdir: $WORKDIR"
   ```

2. **Create branches for each issue:**
   ```bash
   # Generate branch names following TribeVibe convention
   ISSUE1_BRANCH="issue/$issue1-$(echo "$issue1_title" | sed 's/[^a-zA-Z0-9]/-/g' | tr '[:upper:]' '[:lower:]' | tr -s '-' | sed 's/^-\|-$//g')"
   ISSUE2_BRANCH="issue/$issue2-$(echo "$issue2_title" | sed 's/[^a-zA-Z0-9]/-/g' | tr '[:upper:]' '[:lower:]' | tr -s '-' | sed 's/^-\|-$//g')"

   # Create branches from base
   git checkout $baseBranch
   git checkout -b "$ISSUE1_BRANCH"
   git checkout -b "$ISSUE2_BRANCH"
   git checkout $baseBranch
   ```

3. **Create worktrees with proper naming:**
   ```bash
   # Get repository name for worktree directory naming
   REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")

   WORKTREE1_PATH="$WORKDIR/${REPO_NAME}-issue-${issue1}"
   WORKTREE2_PATH="$WORKDIR/${REPO_NAME}-issue-${issue2}"

   # Create worktrees
   echo "🌲 Creating worktree 1: $WORKTREE1_PATH"
   git worktree add "$WORKTREE1_PATH" "$ISSUE1_BRANCH"

   echo "🌲 Creating worktree 2: $WORKTREE2_PATH"
   git worktree add "$WORKTREE2_PATH" "$ISSUE2_BRANCH"

   # Verify worktree creation
   git worktree list
   ```

### Step 3: Worktree Initialization and Issue Tracking

1. **Initialize each worktree with issue context:**
   ```bash
   # Worktree 1 setup
   cd "$WORKTREE1_PATH"
   echo "📝 Initializing worktree 1 for issue #$issue1"

   # Assign issue and add tracking comment
   gh issue edit $issue1 --add-assignee @me
   gh issue comment $issue1 --body "🚀 Starting parallel development in worktree: $WORKTREE1_PATH
   Branch: $ISSUE1_BRANCH
   Parallel with: Issue #$issue2"

   # Create .claude/context file for this worktree
   mkdir -p .claude
   cat > .claude/parallel-context.md << EOF
   # Parallel Development Context

   **Issue:** #$issue1 - $issue1_title
   **Branch:** $ISSUE1_BRANCH
   **Worktree:** $WORKTREE1_PATH
   **Parallel Partner:** Issue #$issue2 in $WORKTREE2_PATH

   ## Available Commands in this Worktree:
   - \`/audit\` - Run code quality audit
   - \`/test-run\` - Execute test suite
   - \`/refactor\` - Apply clean code refactoring
   - \`/debug\` - Debug issues and errors

   ## Parallel Development Notes:
   - Independent development - no shared file conflicts
   - Can run tests and builds independently
   - Coordinate with partner worktree for integration testing
   EOF

   cd -  # Return to original directory

   # Worktree 2 setup
   cd "$WORKTREE2_PATH"
   echo "📝 Initializing worktree 2 for issue #$issue2"

   gh issue edit $issue2 --add-assignee @me
   gh issue comment $issue2 --body "🚀 Starting parallel development in worktree: $WORKTREE2_PATH
   Branch: $ISSUE2_BRANCH
   Parallel with: Issue #$issue1"

   mkdir -p .claude
   cat > .claude/parallel-context.md << EOF
   # Parallel Development Context

   **Issue:** #$issue2 - $issue2_title
   **Branch:** $ISSUE2_BRANCH
   **Worktree:** $WORKTREE2_PATH
   **Parallel Partner:** Issue #$issue1 in $WORKTREE1_PATH

   ## Available Commands in this Worktree:
   - \`/audit\` - Run code quality audit
   - \`/test-run\` - Execute test suite
   - \`/refactor\` - Apply clean code refactoring
   - \`/debug\` - Debug issues and errors

   ## Parallel Development Notes:
   - Independent development - no shared file conflicts
   - Can run tests and builds independently
   - Coordinate with partner worktree for integration testing
   EOF

   cd -  # Return to original directory
   ```

### Step 4: Dependency and Environment Setup

1. **Ensure both worktrees have proper dependencies:**
   ```bash
   echo "📦 Setting up dependencies in worktrees..."

   # Worktree 1 dependency setup
   cd "$WORKTREE1_PATH"
   if [[ -f "package.json" ]]; then
     echo "🔧 Installing dependencies in worktree 1..."
     npm install --frozen-lockfile
   fi
   cd -

   # Worktree 2 dependency setup
   cd "$WORKTREE2_PATH"
   if [[ -f "package.json" ]]; then
     echo "🔧 Installing dependencies in worktree 2..."
     npm install --frozen-lockfile
   fi
   cd -

   echo "✅ Dependencies installed in both worktrees"
   ```

### Step 5: Validation and Testing Setup

1. **Run initial validation in each worktree:**
   ```bash
   echo "🧪 Running initial validation in both worktrees..."

   # Test worktree 1
   cd "$WORKTREE1_PATH"
   echo "📋 Validating worktree 1..."
   npm run build 2>/dev/null && echo "✅ Build: OK" || echo "⚠️ Build: Issues detected"
   npm run lint 2>/dev/null && echo "✅ Lint: OK" || echo "⚠️ Lint: Issues detected"
   cd -

   # Test worktree 2
   cd "$WORKTREE2_PATH"
   echo "📋 Validating worktree 2..."
   npm run build 2>/dev/null && echo "✅ Build: OK" || echo "⚠️ Build: Issues detected"
   npm run lint 2>/dev/null && echo "✅ Lint: OK" || echo "⚠️ Lint: Issues detected"
   cd -

   echo "✅ Initial validation complete"
   ```

### Step 6: Create Coordination Script

1. **Generate helper script for parallel development:**
   ```bash
   # Create coordination script in original repository
   SCRIPT_PATH="scripts/parallel-worktree-coordination.sh"

   cat > "$SCRIPT_PATH" << 'EOF'
   #!/bin/bash

   # Parallel Worktree Coordination Script
   # Auto-generated by /parallel-worktree command

   WORKTREE1_PATH="$WORKTREE1_PATH"
   WORKTREE2_PATH="$WORKTREE2_PATH"
   ISSUE1="$issue1"
   ISSUE2="$issue2"

   case "${1:-help}" in
     "status")
       echo "🌲 Parallel Worktree Status:"
       echo "Worktree 1: $WORKTREE1_PATH (Issue #$ISSUE1)"
       echo "Worktree 2: $WORKTREE2_PATH (Issue #$ISSUE2)"
       echo ""
       git worktree list | grep -E "(issue-$ISSUE1|issue-$ISSUE2)"
       ;;

     "test-both")
       echo "🧪 Running tests in both worktrees..."
       (cd "$WORKTREE1_PATH" && echo "Testing worktree 1..." && npm run test)
       (cd "$WORKTREE2_PATH" && echo "Testing worktree 2..." && npm run test)
       ;;

     "build-both")
       echo "🔨 Building both worktrees..."
       (cd "$WORKTREE1_PATH" && echo "Building worktree 1..." && npm run build)
       (cd "$WORKTREE2_PATH" && echo "Building worktree 2..." && npm run build)
       ;;

     "sync-deps")
       echo "📦 Syncing dependencies in both worktrees..."
       (cd "$WORKTREE1_PATH" && npm install)
       (cd "$WORKTREE2_PATH" && npm install)
       ;;

     "cleanup")
       echo "🧹 Cleaning up parallel worktrees..."
       git worktree remove "$WORKTREE1_PATH" --force
       git worktree remove "$WORKTREE2_PATH" --force
       git branch -D "$ISSUE1_BRANCH" 2>/dev/null
       git branch -D "$ISSUE2_BRANCH" 2>/dev/null
       rm -f "$0"
       echo "✅ Parallel worktrees cleaned up"
       ;;

     "help"|*)
       echo "Parallel Worktree Coordination Commands:"
       echo "  status     - Show worktree status"
       echo "  test-both  - Run tests in both worktrees"
       echo "  build-both - Build both worktrees"
       echo "  sync-deps  - Sync dependencies in both worktrees"
       echo "  cleanup    - Remove worktrees and branches"
       ;;
   esac
   EOF

   chmod +x "$SCRIPT_PATH"
   echo "✅ Coordination script created: $SCRIPT_PATH"
   ```

### Step 7: Integration Testing Setup

1. **Create integration test coordination:**
   ```bash
   echo "🔧 Setting up integration testing coordination..."

   # Create integration test script
   INTEGRATION_SCRIPT="scripts/test-parallel-integration.sh"

   cat > "$INTEGRATION_SCRIPT" << 'EOF'
   #!/bin/bash

   # Integration testing for parallel worktrees
   # Tests both worktrees individually then together

   WORKTREE1_PATH="$WORKTREE1_PATH"
   WORKTREE2_PATH="$WORKTREE2_PATH"

   echo "🧪 Running parallel integration tests..."

   # Test worktree 1 independently
   echo "1️⃣ Testing worktree 1 independently..."
   (cd "$WORKTREE1_PATH" && npm run test && npm run build)
   WORKTREE1_STATUS=$?

   # Test worktree 2 independently
   echo "2️⃣ Testing worktree 2 independently..."
   (cd "$WORKTREE2_PATH" && npm run test && npm run build)
   WORKTREE2_STATUS=$?

   # Create temporary merge for integration testing
   echo "🔄 Testing integration compatibility..."
   TEMP_BRANCH="temp/parallel-integration-$(date +%s)"

   git checkout -b "$TEMP_BRANCH" "$baseBranch"

   # Handle merge conflicts properly - don't mask errors
   MERGE_CONFLICTS=false

   if ! git merge --no-commit --no-ff "$ISSUE1_BRANCH"; then
     echo "⚠️ Merge conflicts detected with $ISSUE1_BRANCH"
     MERGE_CONFLICTS=true
   fi

   if ! git merge --no-commit --no-ff "$ISSUE2_BRANCH"; then
     echo "⚠️ Merge conflicts detected with $ISSUE2_BRANCH"
     MERGE_CONFLICTS=true
   fi

   # Only run tests if no merge conflicts
   if [ "$MERGE_CONFLICTS" = true ]; then
     echo "❌ Cannot run integration tests due to merge conflicts"
     echo "🔄 Aborting integration test and cleaning up..."
     git reset --hard HEAD
     INTEGRATION_STATUS=1
   else
     echo "✅ No merge conflicts - proceeding with integration tests"
     # Test integrated changes
     npm run build && npm run test
     INTEGRATION_STATUS=$?
   fi

   # Cleanup temporary branch
   git reset --hard HEAD
   git checkout "$baseBranch"
   git branch -D "$TEMP_BRANCH"

   # Report results
   echo ""
   echo "🏁 Integration Test Results:"
   [[ $WORKTREE1_STATUS -eq 0 ]] && echo "✅ Worktree 1: PASS" || echo "❌ Worktree 1: FAIL"
   [[ $WORKTREE2_STATUS -eq 0 ]] && echo "✅ Worktree 2: PASS" || echo "❌ Worktree 2: FAIL"
   [[ $INTEGRATION_STATUS -eq 0 ]] && echo "✅ Integration: PASS" || echo "❌ Integration: FAIL"

   if [[ $WORKTREE1_STATUS -eq 0 && $WORKTREE2_STATUS -eq 0 && $INTEGRATION_STATUS -eq 0 ]]; then
     echo "🎉 All tests passed - parallel development successful!"
     exit 0
   else
     echo "🚨 Some tests failed - review before merging"
     exit 1
   fi
   EOF

   chmod +x "$INTEGRATION_SCRIPT"
   echo "✅ Integration test script created: $INTEGRATION_SCRIPT"
   ```

### Step 8: Documentation and Usage Instructions

1. **Generate comprehensive usage documentation:**
   ```bash
   USAGE_DOC=".claude/parallel-worktree-usage.md"

   cat > "$USAGE_DOC" << EOF
   # Parallel Worktree Development Guide

   ## Created Worktrees

   ### Worktree 1: Issue #$issue1
   - **Path:** $WORKTREE1_PATH
   - **Branch:** $ISSUE1_BRANCH
   - **Issue:** $issue1_title
   - **Area:** [Detected from issue analysis]

   ### Worktree 2: Issue #$issue2
   - **Path:** $WORKTREE2_PATH
   - **Branch:** $ISSUE2_BRANCH
   - **Issue:** $issue2_title
   - **Area:** [Detected from issue analysis]

   ## Working with Parallel Worktrees

   ### Development Commands in Each Worktree:
   \`\`\`bash
   # Navigate to worktree
   cd $WORKTREE1_PATH  # or $WORKTREE2_PATH

   # Run standard TribeVibe development commands
   /audit                    # Code quality audit
   /test-run                # Execute test suite
   /refactor <target>       # Clean code refactoring
   /debug                   # Debug issues

   # Standard npm scripts
   npm run dev              # Start development server
   npm run build            # Build the project
   npm run test             # Run tests
   npm run lint             # Code linting
   \`\`\`

   ### Coordination Commands:
   \`\`\`bash
   # From main repository directory
   ./scripts/parallel-worktree-coordination.sh status      # Check status
   ./scripts/parallel-worktree-coordination.sh test-both   # Test both
   ./scripts/parallel-worktree-coordination.sh build-both  # Build both
   ./scripts/parallel-worktree-coordination.sh sync-deps   # Sync dependencies
   ./scripts/parallel-worktree-coordination.sh cleanup     # Remove worktrees

   # Integration testing
   ./scripts/test-parallel-integration.sh                  # Test integration
   \`\`\`

   ## Development Workflow

   1. **Work independently** in each worktree
   2. **Regular testing** using coordination scripts
   3. **Integration testing** before merging
   4. **Create PRs** for each branch when ready
   5. **Merge coordination** after both PRs approved

   ## Safety Guidelines

   - ✅ Each worktree operates independently
   - ✅ No shared file conflicts detected
   - ✅ Independent test suites
   - ✅ Safe parallel development

   ## Cleanup When Done

   \`\`\`bash
   # Automatic cleanup (removes worktrees and branches)
   ./scripts/parallel-worktree-coordination.sh cleanup
   \`\`\`

   ## Troubleshooting

   **Issue:** Worktree build fails
   **Solution:** \`cd <worktree> && npm install && npm run build\`

   **Issue:** Integration conflicts
   **Solution:** Use \`./scripts/test-parallel-integration.sh\` to identify conflicts

   **Issue:** Lost worktree context
   **Solution:** Check \`.claude/parallel-context.md\` in each worktree
   EOF

   echo "✅ Usage documentation created: $USAGE_DOC"
   ```

### Step 9: Final Validation and Report

1. **Comprehensive final validation:**
   ```bash
   echo "🔍 Running final validation of parallel worktree setup..."

   # Verify worktrees exist and are accessible
   [[ -d "$WORKTREE1_PATH" ]] && echo "✅ Worktree 1: Accessible" || echo "❌ Worktree 1: Missing"
   [[ -d "$WORKTREE2_PATH" ]] && echo "✅ Worktree 2: Accessible" || echo "❌ Worktree 2: Missing"

   # Verify branches exist
   git branch --list "$ISSUE1_BRANCH" | grep -q "$ISSUE1_BRANCH" && echo "✅ Branch 1: Created" || echo "❌ Branch 1: Missing"
   git branch --list "$ISSUE2_BRANCH" | grep -q "$ISSUE2_BRANCH" && echo "✅ Branch 2: Created" || echo "❌ Branch 2: Missing"

   # Verify git worktree tracking
   git worktree list | grep -q "$WORKTREE1_PATH" && echo "✅ Worktree 1: Git tracking" || echo "❌ Worktree 1: Not tracked"
   git worktree list | grep -q "$WORKTREE2_PATH" && echo "✅ Worktree 2: Git tracking" || echo "❌ Worktree 2: Not tracked"

   # Verify coordination scripts
   [[ -x "scripts/parallel-worktree-coordination.sh" ]] && echo "✅ Coordination script: Executable" || echo "❌ Coordination script: Missing"
   [[ -x "scripts/test-parallel-integration.sh" ]] && echo "✅ Integration script: Executable" || echo "❌ Integration script: Missing"

   echo "✅ Final validation complete"
   ```

### Final Success Report

Display comprehensive success message:

```
🎉 Parallel Worktree Setup Complete!

🌲 Created Worktrees:
├── Worktree 1: $WORKTREE1_PATH
│   ├── Issue: #$issue1 - $issue1_title
│   ├── Branch: $ISSUE1_BRANCH
│   └── Area: [Backend/Frontend/etc]
│
└── Worktree 2: $WORKTREE2_PATH
    ├── Issue: #$issue2 - $issue2_title
    ├── Branch: $ISSUE2_BRANCH
    └── Area: [Backend/Frontend/etc]

✅ Ready for Parallel Development:
- Both worktrees initialized and validated
- Dependencies installed in both environments
- Issues assigned and tracking comments added
- Coordination scripts created for management
- Integration testing framework ready
- No conflicts detected between selected issues

🛠️ Available Commands in Each Worktree:
- /audit     - Code quality audit
- /test-run  - Execute test suite
- /refactor  - Clean code refactoring
- /debug     - Debug issues and errors

📋 Coordination Commands:
- ./scripts/parallel-worktree-coordination.sh status
- ./scripts/parallel-worktree-coordination.sh test-both
- ./scripts/test-parallel-integration.sh

📖 Documentation: .claude/parallel-worktree-usage.md

🚀 Next Steps:
1. cd $WORKTREE1_PATH  # Start working on issue #$issue1
2. cd $WORKTREE2_PATH  # Start working on issue #$issue2
3. Use coordination scripts for testing and integration
4. Create PRs when issues are complete
5. Run cleanup script when both issues merged
```

## Conflict Detection Algorithm Details

### File Path Analysis:
- Parse issue descriptions for mentioned file paths
- Check `packages/`, `services/`, `apps/` directory conflicts
- Identify shared utility/common file dependencies
- Flag issues touching same architectural layers

### Dependency Chain Detection:
- Scan issue bodies for "Depends on #XX" or "Blocked by #XX"
- Build dependency graph from issue references
- Ensure selected issues have no direct or indirect dependencies
- Verify both issues can be implemented independently

### Area Compatibility Matrix:
```
Compatible Combinations:
✅ area:backend + area:frontend
✅ area:infra + area:backend
✅ area:infra + area:frontend
✅ Different feature slices (auth + profile)

Incompatible Combinations:
❌ Same area labels (area:backend + area:backend)
❌ Same feature slice (both touching auth system)
❌ Shared architectural components
❌ Database migration dependencies
```

## Error Handling and Recovery

### Worktree Creation Failures:
```bash
# If worktree creation fails
if ! git worktree add "$WORKTREE_PATH" "$BRANCH"; then
  echo "❌ Failed to create worktree: $WORKTREE_PATH"
  echo "🔧 Cleanup and retry..."
  git worktree remove "$WORKTREE_PATH" --force 2>/dev/null
  git branch -D "$BRANCH" 2>/dev/null
  exit 1
fi
```

### Branch Conflicts:
```bash
# Handle existing branch names
if git branch --list "$BRANCH_NAME" | grep -q "$BRANCH_NAME"; then
  BRANCH_NAME="${BRANCH_NAME}-$(date +%s)"
  echo "⚠️ Branch exists, using: $BRANCH_NAME"
fi
```

### Dependency Installation Failures:
```bash
# Graceful handling of npm install failures
if ! npm install --frozen-lockfile; then
  echo "⚠️ Dependency installation failed in worktree"
  echo "💡 You may need to run 'npm install' manually in worktree"
  echo "🔧 Continuing with worktree setup..."
fi
```

This command provides a comprehensive parallel development environment with proper conflict detection, coordination tools, and safety measures for efficient multi-issue development.