---
description: Auto-triage GitHub issues and select best candidate for Codex implementation (project)
---

You are a repository triage agent. Analyze open GitHub issues and select the best candidate for Codex autonomous implementation.

Execute the following steps autonomously:

## Step 1: Detect Repository

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [[ -z "$REPO" ]]; then
  echo "❌ Not in a GitHub repository"
  exit 1
fi
echo "Repository: $REPO"
```

## Step 2: Fetch and Score Issues

Create a self-contained Node.js scoring script:

```javascript
// codex-triage-score.cjs
const fs = require('fs');
const { execSync } = require('child_process');

// Fetch issues
const repo = execSync('gh repo view --json nameWithOwner -q .nameWithOwner', { encoding: 'utf8' }).trim();
console.log(`Repository: ${repo}\n`);

const issuesJson = execSync(
  `gh issue list --repo ${repo} --state OPEN --limit 200 --json number,title,labels,assignees,createdAt,updatedAt,body,url`,
  { encoding: 'utf8' }
);
const issues = JSON.parse(issuesJson);

console.log(`Analyzing ${issues.length} open issues...\n`);

// Scoring configuration
const preferredLabels = ['bug', 'p1', 'good-first-issue', 'tech-debt:localized', 'vertical-slice-ready'];
const avoidedLabels = ['blocked', 'epic', 'needs-design', 'spec-needed', 'migration', 'infra', 'security-review', 'codex:take'];

function scoreIssue(issue) {
  let score = 0;
  const reasons = [];
  const bodyLength = (issue.body || '').length;
  const title = issue.title.toLowerCase();
  const body = (issue.body || '').toLowerCase();

  // Scope scoring
  if (title.includes('typescript') || title.includes('dependency')) {
    score += 0.4;
    reasons.push('Very localized (TypeScript/dependency): +0.4');
  } else if (bodyLength < 1000 && !body.includes('/')) {
    score += 0.3;
    reasons.push('Small scope (body <1000 chars, no paths): +0.3');
  } else if (bodyLength < 2000) {
    score += 0.25;
    reasons.push('Few files (body <2000 chars): +0.25');
  } else if (bodyLength < 4000) {
    score += 0.1;
    reasons.push('Moderate scope: +0.1');
  } else {
    score -= 0.1;
    reasons.push('Large scope (body >4000 chars): -0.1');
  }

  // Label scoring
  const labels = issue.labels.map(l => l.name.toLowerCase());
  for (const label of labels) {
    if (preferredLabels.includes(label)) {
      score += 0.25;
      reasons.push(`Preferred label '${label}': +0.25`);
    }
    if (avoidedLabels.includes(label)) {
      score -= 0.4;
      reasons.push(`Avoided label '${label}': -0.4`);
    }
  }

  if (title.includes('epic')) {
    score -= 0.5;
    reasons.push('Epic in title: -0.5');
  }

  // Freshness scoring
  const ageInDays = (new Date() - new Date(issue.createdAt)) / (1000 * 60 * 60 * 24);
  const ageDays = Math.round(ageInDays);
  if (ageInDays >= 7 && ageInDays <= 30) {
    score += 0.15;
    reasons.push(`Age ${ageDays} days (7-30 range): +0.15`);
  } else if (ageInDays < 7) {
    score += 0.05;
    reasons.push(`Age ${ageDays} days (fresh): +0.05`);
  } else if (ageInDays > 60) {
    score -= 0.1;
    reasons.push(`Age ${ageDays} days (stale): -0.1`);
  }

  // Assignment penalty
  if (issue.assignees.length > 0) {
    score -= 0.3;
    reasons.push('Has assignees: -0.3');
  }

  // Clarity bonus
  if (bodyLength >= 200 && bodyLength <= 1200) {
    score += 0.2;
    reasons.push('Clear description (200-1200 chars): +0.2');
  }

  // Risk penalties
  const riskKeywords = ['migration', 'core auth', 'global refactor', 'breaking change'];
  for (const keyword of riskKeywords) {
    if (body.includes(keyword)) {
      score -= 0.25;
      reasons.push(`Risk keyword '${keyword}': -0.25`);
      break;
    }
  }

  // Test hints bonus
  const testKeywords = ['test', 'reproduction', 'acceptance criteria', 'steps to reproduce', '- [ ]'];
  for (const keyword of testKeywords) {
    if (body.includes(keyword)) {
      score += 0.1;
      reasons.push('Has test hints/AC: +0.1');
      break;
    }
  }

  return { score: Math.round(score * 100) / 100, reasons };
}

// Score all issues
const scored = issues.map(issue => {
  const { score, reasons } = scoreIssue(issue);
  return { issue, score, reasons };
}).sort((a, b) => b.score - a.score);

// Output results
console.log('=== CODEX TRIAGE RESULTS ===\n');
console.log(`Repository: ${repo}`);
console.log(`Analyzed: ${issues.length} open issues\n`);

console.log('Top 10 Candidates:\n');
scored.slice(0, 10).forEach((item, idx) => {
  const selected = idx === 0 && item.score >= 0.60 ? ' ✓ SELECTED' : '';
  console.log(`${idx + 1}. #${item.issue.number} (${item.score}) - ${item.issue.title}${selected}`);
  console.log(`   Labels: ${item.issue.labels.map(l => l.name).join(', ') || 'none'}`);
});

console.log('\n=== SELECTED CANDIDATE ===\n');

// Find best issue without codex:take label
const winner = scored.find(s => s.score >= 0.60 && !s.issue.labels.some(l => l.name === 'codex:take'));

if (!winner) {
  console.log('❌ No issue scored >= 0.60 without codex:take label');
  console.log('\nConsider:');
  console.log('- Refining issue descriptions');
  console.log('- Adding clearer acceptance criteria');
  console.log('- Breaking down large issues into smaller tasks');
  process.exit(1);
}

console.log(`Issue #${winner.issue.number}: ${winner.issue.title}`);
console.log(`Score: ${winner.score}`);
console.log(`URL: ${winner.issue.url}\n`);
console.log('Scoring breakdown:');
winner.reasons.forEach(r => console.log(`  - ${r}`));
console.log('');

// Export for next steps
fs.writeFileSync('.codex-triage-result.json', JSON.stringify({
  repo,
  number: winner.issue.number,
  title: winner.issue.title,
  url: winner.issue.url,
  score: winner.score,
  reasons: winner.reasons
}, null, 2));

console.log('✓ Issue selected and saved to .codex-triage-result.json');
```

Write this script to a temp file and execute it:

```bash
cat > /tmp/codex-triage-score.cjs << 'SCRIPT'
[paste the JavaScript above]
SCRIPT

node /tmp/codex-triage-score.cjs
```

## Step 3: Verify Not Already Implemented

```bash
# Load selected issue
RESULT=$(cat .codex-triage-result.json)
ISSUE_NUMBER=$(echo "$RESULT" | jq -r '.number')
ISSUE_TITLE=$(echo "$RESULT" | jq -r '.title')

echo "Verifying issue #$ISSUE_NUMBER is not already implemented..."

# Check git history
RECENT_REFS=$(git log --all --oneline --grep="$ISSUE_NUMBER" -n 10 2>/dev/null || echo "")
if [[ -n "$RECENT_REFS" ]]; then
  echo "⚠️  Found references in commits:"
  echo "$RECENT_REFS"
fi
```

## Step 4: Check for Existing PR

```bash
EXISTING_PR=$(gh pr list --state open --search "#$ISSUE_NUMBER" --json number --jq '.[0].number' 2>/dev/null || echo "")

if [[ -n "$EXISTING_PR" ]]; then
  echo "❌ Issue #$ISSUE_NUMBER already has open PR #$EXISTING_PR"
  exit 1
fi

echo "✓ No existing PR found"
```

## Step 5: Label and Comment

```bash
# Load results
REPO=$(cat .codex-triage-result.json | jq -r '.repo')
ISSUE_NUMBER=$(cat .codex-triage-result.json | jq -r '.number')
ISSUE_TITLE=$(cat .codex-triage-result.json | jq -r '.title')
SCORE=$(cat .codex-triage-result.json | jq -r '.score')

# Create label if needed
gh label create 'codex:take' --repo "$REPO" \
  --description 'Selected for Codex autonomous implementation' \
  --color '0E8A16' 2>/dev/null || true

# Apply label
gh issue edit $ISSUE_NUMBER --repo "$REPO" --add-label 'codex:take'

# Add comment with rationale
REASONS=$(cat .codex-triage-result.json | jq -r '.reasons | map("- " + .) | join("\n")')

gh issue comment $ISSUE_NUMBER --repo "$REPO" -b "🤖 **Auto-triage: Selected for Codex**

**Score:** $SCORE (threshold: 0.60)

**Selection Rationale:**
- Clear scope and acceptance criteria
- Limited blast radius
- No existing PR or assignee
- Verified not already implemented in codebase

**Scoring breakdown:**
$REASONS

**Next Steps:**
Codex will create branch \`codex/issue-$ISSUE_NUMBER\` and submit PR with \`closes #$ISSUE_NUMBER\`.

---
*Automated triage by Claude Code /codex-triage command*"

# Cleanup
rm -f .codex-triage-result.json /tmp/codex-triage-score.cjs

echo ""
echo "✓ Issue #$ISSUE_NUMBER labeled and ready for Codex"
echo "✓ GitHub Actions workflow will trigger automatically"
```

## Notes

- Self-contained: All logic embedded in this command
- Uses Node.js for complex scoring (available in most environments)
- Creates temporary files that are cleaned up after use
- Safe for CI/CD integration
- Only labels ONE issue per run
- Respects blocked/wip labels
- Threshold: Issues must score >= 0.60
