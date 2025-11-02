---
description: Auto-triage GitHub issues and select best candidate for Codex implementation
---

You are a repository triage agent. Analyze open GitHub issues and select the best candidate for Codex autonomous implementation.

## Process

Execute the following steps autonomously:

### 1. Detect Repository

```bash
# Auto-detect current repo from git remote
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [[ -z "$REPO" ]]; then
  echo "❌ Not in a GitHub repository or gh CLI not configured"
  exit 1
fi
echo "Repository: $REPO"
```

### 2. Fetch and Score Issues

```bash
# Fetch all open issues
gh issue list --repo "$REPO" --state OPEN --limit 200 \
  --json number,title,labels,assignees,createdAt,updatedAt,body,url > /tmp/issues.json

# Count issues
ISSUE_COUNT=$(jq 'length' /tmp/issues.json)
echo "Analyzing $ISSUE_COUNT open issues..."
```

### 3. Score Each Issue

For each issue, calculate a score based on these criteria:

**Scoring Algorithm:**
- **Scope** (+0.4 very localized, +0.3 small, +0.25 few files, +0.1 moderate, -0.1 large)
  - TypeScript/dependency updates: very localized
  - Body length <1000 chars, no file paths: small
  - 1-3 distinct file extensions: few files
  - 4-10 files: moderate
  - >10 files: large

- **Labels** (+0.25 if preferred, -0.4 if avoided, -0.5 if "epic" in title)
  - Preferred: bug, p1, good-first-issue, tech-debt:localized, vertical-slice-ready
  - Avoided: blocked, epic, needs-design, spec-needed, migration, infra, security-review

- **Freshness** (+0.15 for 7-30 days, +0.05 for <7 days, -0.1 for >60 days)

- **Assignment** (-0.3 if has assignees)

- **Clarity** (+0.2 if body 200-1200 chars)

- **Risk** (-0.25 if mentions migration, core auth, global refactor, breaking change)

- **Test Hints** (+0.1 if mentions tests, reproduction steps, AC, checkboxes)

**Threshold:** Issue must score ≥ 0.60 to be selected

### 4. Verify Issue Not Already Implemented

For the top-scoring issue, verify it's not already done:

```bash
# Extract key terms from issue title
ISSUE_TITLE="[title of top issue]"
ISSUE_NUMBER="[number]"

# Search codebase for evidence of implementation
echo "Verifying issue #$ISSUE_NUMBER is not already implemented..."

# Search for keywords from title in recent commits
RECENT_REFS=$(git log --all --oneline --grep="$ISSUE_NUMBER\|$(echo $ISSUE_TITLE | cut -d' ' -f1-3)" -n 20 2>/dev/null || echo "")

if [[ -n "$RECENT_REFS" ]]; then
  echo "⚠️  Found references in commits:"
  echo "$RECENT_REFS"
  echo ""
  echo "Checking if issue should be closed..."
fi

# Search codebase for key functionality mentioned in issue
# Extract main keywords from title (remove common words)
KEYWORDS=$(echo "$ISSUE_TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/\b\(add\|implement\|create\|update\|fix\|feature\|bug\)\b//g' | tr -s ' ')

# Search for these keywords in source files
FOUND_IN_CODE=$(rg -i "$KEYWORDS" --type-list | head -5 2>/dev/null || echo "")

if [[ -n "$FOUND_IN_CODE" ]]; then
  echo "⚠️  Found similar functionality already in codebase:"
  echo "$FOUND_IN_CODE"
  echo ""
  echo "Manual review needed - may already be implemented"
fi
```

### 5. Check for Existing PR

```bash
# Check if there's already a PR for this issue
EXISTING_PR=$(gh pr list --repo "$REPO" --state open --search "in:title #$ISSUE_NUMBER in:body #$ISSUE_NUMBER" --json number,title --jq '.[0].number' 2>/dev/null || echo "")

if [[ -n "$EXISTING_PR" ]]; then
  echo "❌ Issue #$ISSUE_NUMBER already has open PR #$EXISTING_PR"
  echo "Skipping to next candidate..."
  # Move to next highest-scoring issue
fi
```

### 6. Label and Comment

If all checks pass:

```bash
# Create label if doesn't exist
gh label create 'codex:take' --repo "$REPO" \
  --description 'Selected for Codex autonomous implementation' \
  --color '0E8A16' 2>/dev/null || true

# Apply label
gh issue edit $ISSUE_NUMBER --repo "$REPO" --add-label 'codex:take'

# Add rationale comment
gh issue comment $ISSUE_NUMBER --repo "$REPO" -b "🤖 **Auto-triage: Selected for Codex**

**Score:** $SCORE (threshold: 0.60)

**Selection Rationale:**
- Clear scope and acceptance criteria
- Limited blast radius
- No existing PR or assignee
- Verified not already implemented in codebase
- Low risk, high value for incremental improvement

**Next Steps:**
Codex will create branch \`codex/issue-$ISSUE_NUMBER\` and submit PR with \`closes #$ISSUE_NUMBER\`.

---
*Automated triage by Claude Code /codex-triage command*"
```

## Output Format

Present results to user:

```
=== CODEX TRIAGE RESULTS ===

Repository: [owner/repo]
Analyzed: [N] open issues
Selected: Issue #XX (score: 0.XX)

Title: [issue title]
URL: https://github.com/[owner]/[repo]/issues/XX

✓ No existing PR found
✓ Verified not already implemented
✓ Clear acceptance criteria
✓ Localized scope

Top 5 Candidates:
1. #XX (0.XX) - [title] [✓ selected]
2. #XX (0.XX) - [title]
3. #XX (0.XX) - [title]
4. #XX (0.XX) - [title]
5. #XX (0.XX) - [title]

Status: ✓ Issue labeled and ready for Codex
```

## Special Cases

**No suitable candidate:**
```
No issue scored ≥ 0.60
Consider:
- Refining issue descriptions
- Adding clearer acceptance criteria
- Breaking down large issues into smaller tasks
```

**Issue already implemented:**
```
Top candidate #XX appears already implemented
Evidence: [commit refs or code matches]
Recommend: Close issue or verify implementation
Moving to next candidate...
```

## Configuration

You can customize scoring by checking for project-specific labels in the repository. Adjust weights based on the project's workflow.

## Notes

- Only ONE issue labeled per run
- Fully autonomous - no user input needed
- Safe for CI/CD integration
- Respects blocked/wip labels
- Prioritizes clear, testable issues
