# Agent Branch Awareness Pattern

**Version:** 1.0
**Last Updated:** 2025-11-20

---

## Problem Statement

When running multiple agents in parallel on the same feature branch, agents that automatically create new branches can cause conflicts and workflow disruptions. Each agent may try to create its own branch, leading to:

- Work being split across multiple branches
- Merge conflicts between parallel agents
- Lost work when agents switch branches unexpectedly
- Confusion about which branch contains the latest code

## Solution: Branch Awareness Pattern

Agents should check the current branch **before** creating a new one, and only create a new branch if necessary.

### Decision Logic

```bash
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
BASE_BRANCHES="main|master|development|develop"

# 1. Already on a feature branch? → Stay on it
if echo "$CURRENT_BRANCH" | grep -qE "^(feature/|fix/|deps/|chore/|claude/)"; then
  echo "✅ Already on feature branch: $CURRENT_BRANCH"
  BRANCH_NAME="$CURRENT_BRANCH"

# 2. On a base branch? → Create new feature branch
elif echo "$CURRENT_BRANCH" | grep -qE "^($BASE_BRANCHES)$"; then
  BRANCH_NAME="feature/new-feature-$(date +%Y%m%d)"
  git checkout -b "$BRANCH_NAME"

# 3. On unexpected branch? → Stay on it (safe default)
else
  echo "⚠️ On unexpected branch: $CURRENT_BRANCH"
  BRANCH_NAME="$CURRENT_BRANCH"
fi
```

### Key Principles

1. **Check Current Branch First**: Always determine what branch you're on before making decisions
2. **Respect Existing Feature Branches**: If already on a feature branch, stay on it
3. **Only Create When Needed**: Only create new branches when on base branches
4. **Parallel Agent Safety**: Multiple agents can work on the same branch without conflicts

---

## Implementation Examples

### Example 1: Conductor Agent

The conductor agent implements branch awareness when setting up a feature branch:

```bash
# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
BASE_BRANCHES="main|master|development|develop"

# Already on feature branch? Use it
if echo "$CURRENT_BRANCH" | grep -qE "^(feature/|fix/|deps/|chore/|claude/)"; then
  echo "✅ Already on a feature branch: $CURRENT_BRANCH"
  echo "   Using existing branch to avoid conflicts with parallel agents"
  BRANCH_NAME="$CURRENT_BRANCH"

# On base branch? Create new one
elif echo "$CURRENT_BRANCH" | grep -qE "^($BASE_BRANCHES)$"; then
  BRANCH_NAME="feature/issue-$ISSUE_NUMBER-[description]"
  if git rev-parse --verify "$BRANCH_NAME" 2>/dev/null; then
    git checkout "$BRANCH_NAME"
  else
    git checkout development 2>/dev/null || git checkout main
    git pull origin $(git rev-parse --abbrev-ref HEAD)
    git checkout -b "$BRANCH_NAME"
    git push -u origin "$BRANCH_NAME"
  fi

# On other branch? Stay on it
else
  echo "⚠️ On unexpected branch: $CURRENT_BRANCH"
  echo "   Staying on current branch to avoid disruption"
  BRANCH_NAME="$CURRENT_BRANCH"
fi
```

**Location:** `.claude/agents/conductor.md:876-912`

### Example 2: Dependency Manager Agent

The dependency manager checks for existing `deps/` branches:

```bash
# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
BASE_BRANCHES="main|master|development|develop"

# Already on deps branch? Use it
if echo "$CURRENT_BRANCH" | grep -qE "^deps/"; then
  echo "✅ Already on a dependency update branch: $CURRENT_BRANCH"
  echo "   Using existing branch to avoid conflicts with parallel agents"
  BRANCH_NAME="$CURRENT_BRANCH"

# On base branch? Create new deps branch
elif echo "$CURRENT_BRANCH" | grep -qE "^($BASE_BRANCHES)$"; then
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  BRANCH_NAME="deps/automated-updates-${TIMESTAMP}"
  git checkout -b "$BRANCH_NAME"
  echo "✅ Created branch: $BRANCH_NAME"

# On other branch? Stay on it
else
  echo "⚠️ On non-base branch: $CURRENT_BRANCH"
  echo "   Staying on current branch for dependency updates"
  BRANCH_NAME="$CURRENT_BRANCH"
fi
```

**Location:** `.claude/agents/dependency-manager.md:237-266`

---

## Common Scenarios

### Scenario 1: Single Agent Workflow

**User starts on `main` branch:**

```bash
$ git branch
* main
```

**Agent behavior:**
- Detects current branch: `main`
- Recognizes it as a base branch
- Creates new feature branch: `feature/issue-123-new-feature`
- Proceeds with work on new branch

✅ **Result**: New feature branch created as expected

---

### Scenario 2: Parallel Agents on Same Branch

**User creates feature branch and runs multiple agents:**

```bash
$ git checkout -b feature/issue-456-complex-feature
$ # Start Agent 1: Implementation
$ # Start Agent 2: Testing
$ # Start Agent 3: Documentation
```

**Agent 1 (Implementation) behavior:**
- Detects current branch: `feature/issue-456-complex-feature`
- Recognizes it as a feature branch
- Stays on current branch
- Implements code

**Agent 2 (Testing) behavior:**
- Detects current branch: `feature/issue-456-complex-feature`
- Recognizes it as a feature branch
- Stays on current branch
- Adds tests

**Agent 3 (Documentation) behavior:**
- Detects current branch: `feature/issue-456-complex-feature`
- Recognizes it as a feature branch
- Stays on current branch
- Updates docs

✅ **Result**: All agents work on the same branch, no conflicts

---

### Scenario 3: Agent Resumption

**User starts agent, it creates branch, then user resumes agent later:**

```bash
# First run
$ git branch
* main

# Agent creates feature/issue-789-api-endpoint
# Work in progress...

# Later, user resumes agent
$ git branch
* feature/issue-789-api-endpoint
```

**Agent behavior on resumption:**
- Detects current branch: `feature/issue-789-api-endpoint`
- Recognizes it as a feature branch (matches pattern)
- Stays on current branch
- Continues work

✅ **Result**: Agent resumes work on same branch, no duplication

---

## Branch Naming Conventions

The pattern recognizes these prefixes as feature branches:

- `feature/` - New features
- `fix/` - Bug fixes
- `deps/` - Dependency updates
- `chore/` - Maintenance tasks
- `claude/` - Claude Code web session branches

**Base branches** (should NOT stay on these):
- `main`
- `master`
- `development`
- `develop`

### Adding New Prefixes

To support additional branch prefixes, update the grep pattern:

```bash
# Current pattern (includes claude/ for web sessions)
if echo "$CURRENT_BRANCH" | grep -qE "^(feature/|fix/|deps/|chore/|claude/)"; then

# To add more prefixes (example: refactor/ and docs/)
if echo "$CURRENT_BRANCH" | grep -qE "^(feature/|fix/|deps/|chore/|claude/|refactor/|docs/)"; then
```

---

## Benefits

1. **Parallel Agent Safety**: Multiple agents can work on the same branch without stepping on each other
2. **Resumption Support**: Agents can resume work on existing branches without creating duplicates
3. **User Control**: Users can pre-create branches and agents will respect them
4. **Predictable Behavior**: Agents follow a consistent, logical pattern
5. **Reduced Confusion**: Clear decision logic for when to create vs. use existing branches

---

## Testing the Pattern

### Test 1: Single Agent from Main

```bash
# Setup
git checkout main

# Run agent
# → Should create new feature branch

# Verify
git branch | grep feature/
```

### Test 2: Parallel Agents

```bash
# Setup
git checkout -b feature/test-parallel-agents

# Run multiple agents in parallel
# Agent 1: Implementation
# Agent 2: Testing

# Verify
git log --oneline
# → Should see commits from both agents on same branch
```

### Test 3: Agent Resumption

```bash
# Setup
git checkout main

# Run agent (creates feature/issue-123)
# Stop agent mid-work

# Resume agent
# → Should continue on feature/issue-123, not create new branch

# Verify
git branch
# → Only one feature/issue-123 branch exists
```

---

## Migrating Existing Agents

To add branch awareness to an existing agent:

1. **Identify branch creation code**:
   ```bash
   grep -n "git checkout -b" .claude/agents/your-agent.md
   ```

2. **Replace with branch awareness pattern**:
   ```bash
   # Old code
   git checkout -b "$BRANCH_NAME"

   # New code (see examples above)
   CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
   # ... decision logic ...
   ```

3. **Test the changes**:
   - Test from main branch (should create new)
   - Test from feature branch (should stay on it)
   - Test parallel agents (should work together)

---

## Future Enhancements

### Potential Improvements

1. **Branch Validation**: Check if branch matches issue/ticket number
2. **Stale Branch Detection**: Warn if branch is far behind base branch
3. **Branch Cleanup**: Automatically clean up merged/abandoned branches
4. **Branch Context Sharing**: Share branch info between parallel agents

### Configuration Options

Consider adding user-configurable settings:

```json
{
  "branchAwareness": {
    "enabled": true,
    "featureBranchPatterns": ["feature/", "fix/", "deps/"],
    "baseBranches": ["main", "master", "development"],
    "alwaysCreateNew": false
  }
}
```

---

## Troubleshooting

### Issue: Agent creates new branch despite being on feature branch

**Cause**: Branch name doesn't match recognized patterns

**Solution**: Update the branch prefix pattern or rename your branch

```bash
# Check current branch
git branch --show-current

# Rename to match pattern
git branch -m feature/your-feature-name
```

### Issue: Agent stays on wrong branch

**Cause**: Branch detection logic doesn't recognize base branch

**Solution**: Add your base branch name to the pattern

```bash
BASE_BRANCHES="main|master|development|develop|trunk"
```

### Issue: Parallel agents create separate branches

**Cause**: Each agent starts from base branch independently

**Solution**: Create feature branch first, then start agents

```bash
git checkout -b feature/issue-123
# Now start agents - they'll all use this branch
```

---

## References

- **Conductor Agent**: `.claude/agents/conductor.md:866-912`
- **Dependency Manager**: `.claude/agents/dependency-manager.md:231-266`
- **Git Branch Docs**: https://git-scm.com/docs/git-branch
- **Parallel Agent Pattern**: `.claude/prompts/coordination/parallel-agents.md`

---

**Last Updated:** 2025-11-20
**Maintained By:** Claude Code Toolkit Team
