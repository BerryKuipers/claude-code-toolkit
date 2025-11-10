#!/bin/bash
# Security Scan All Repositories
# Cross-platform script to scan all repos for security vulnerabilities
# Usage: ./scripts/security-scan-all.sh [--severity=critical|high|moderate|all]

set -e

GITHUB_USER="${GITHUB_USER:-BerryKuipers}"
WORK_DIR="${WORK_DIR:-/tmp/security-scan}"
SEVERITY="${1:-high}" # Default to high and above
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_DIR="${WORK_DIR}/reports-${TIMESTAMP}"

# Parse severity argument
if [[ "$1" == --severity=* ]]; then
  SEVERITY="${1#*=}"
fi

echo "🔒 Security Scan All Repositories"
echo "=================================="
echo "User: $GITHUB_USER"
echo "Severity: $SEVERITY and above"
echo "Report dir: $REPORT_DIR"
echo ""

# Create report directory
mkdir -p "$REPORT_DIR"

# Get all repos for user
echo "📋 Fetching repository list..."
REPOS=$(~/.local/bin/gh repo list "$GITHUB_USER" --limit 100 --json name --jq '.[].name')
REPO_COUNT=$(echo "$REPOS" | wc -l)
echo "Found $REPO_COUNT repositories"
echo ""

# Initialize counters
TOTAL_VULNS=0
REPOS_WITH_VULNS=0
REPOS_SCANNED=0
REPOS_FAILED=0

# Initialize summary file
SUMMARY_FILE="$REPORT_DIR/SUMMARY.md"
cat > "$SUMMARY_FILE" <<EOF
# Security Scan Summary

**Date**: $(date -Iseconds)
**User**: $GITHUB_USER
**Severity**: $SEVERITY and above
**Total Repos**: $REPO_COUNT

---

## Scan Results

EOF

echo "🔍 Scanning repositories..."
echo ""

# Scan each repository
while IFS= read -r REPO; do
  echo "📦 Scanning: $REPO"
  REPOS_SCANNED=$((REPOS_SCANNED + 1))

  REPO_DIR="$WORK_DIR/$REPO"
  REPORT_FILE="$REPORT_DIR/${REPO}-vulnerabilities.json"

  # Clone or update repo
  if [ -d "$REPO_DIR" ]; then
    echo "  → Updating existing clone..."
    cd "$REPO_DIR"
    git fetch origin --quiet
    git pull origin $(git symbolic-ref --short HEAD) --quiet || true
  else
    echo "  → Cloning repository..."
    ~/.local/bin/gh repo clone "$GITHUB_USER/$REPO" "$REPO_DIR" --quiet 2>/dev/null || {
      echo "  ❌ Failed to clone $REPO"
      REPOS_FAILED=$((REPOS_FAILED + 1))
      echo "### ❌ $REPO - Clone Failed" >> "$SUMMARY_FILE"
      echo "" >> "$SUMMARY_FILE"
      continue
    }
    cd "$REPO_DIR"
  fi

  # Check if it's a Node.js project
  if [ ! -f "package.json" ]; then
    echo "  ℹ️  Not a Node.js project, skipping"
    echo "### ⚪ $REPO - Not Node.js" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    continue
  fi

  # Install dependencies if needed
  if [ ! -d "node_modules" ]; then
    echo "  → Installing dependencies..."
    npm install --silent --no-progress 2>/dev/null || {
      echo "  ⚠️  Install failed, scanning anyway..."
    }
  fi

  # Run npm audit
  echo "  → Running npm audit..."
  npm audit --json > "$REPORT_FILE" 2>/dev/null || {
    # npm audit returns non-zero if vulnerabilities found
    echo "  ⚠️  Vulnerabilities detected"
  }

  # Parse results based on severity
  CRITICAL_COUNT=$(jq -r '.metadata.vulnerabilities.critical // 0' "$REPORT_FILE" 2>/dev/null || echo "0")
  HIGH_COUNT=$(jq -r '.metadata.vulnerabilities.high // 0' "$REPORT_FILE" 2>/dev/null || echo "0")
  MODERATE_COUNT=$(jq -r '.metadata.vulnerabilities.moderate // 0' "$REPORT_FILE" 2>/dev/null || echo "0")
  LOW_COUNT=$(jq -r '.metadata.vulnerabilities.low // 0' "$REPORT_FILE" 2>/dev/null || echo "0")

  TOTAL_COUNT=$((CRITICAL_COUNT + HIGH_COUNT + MODERATE_COUNT + LOW_COUNT))

  # Filter by requested severity
  case "$SEVERITY" in
    critical)
      FILTERED_COUNT=$CRITICAL_COUNT
      ;;
    high)
      FILTERED_COUNT=$((CRITICAL_COUNT + HIGH_COUNT))
      ;;
    moderate)
      FILTERED_COUNT=$((CRITICAL_COUNT + HIGH_COUNT + MODERATE_COUNT))
      ;;
    all|*)
      FILTERED_COUNT=$TOTAL_COUNT
      ;;
  esac

  if [ "$FILTERED_COUNT" -gt 0 ]; then
    REPOS_WITH_VULNS=$((REPOS_WITH_VULNS + 1))
    TOTAL_VULNS=$((TOTAL_VULNS + FILTERED_COUNT))

    echo "  🔴 Found $FILTERED_COUNT vulnerabilities (Critical: $CRITICAL_COUNT, High: $HIGH_COUNT, Moderate: $MODERATE_COUNT, Low: $LOW_COUNT)"

    # Add to summary
    cat >> "$SUMMARY_FILE" <<EOF
### 🔴 $REPO - $FILTERED_COUNT Vulnerabilities

- **Critical**: $CRITICAL_COUNT
- **High**: $HIGH_COUNT
- **Moderate**: $MODERATE_COUNT
- **Low**: $LOW_COUNT
- **Report**: [${REPO}-vulnerabilities.json](${REPO}-vulnerabilities.json)

**Fix command**:
\`\`\`bash
cd $REPO
/fix-vulns --severity=$SEVERITY
\`\`\`

---

EOF
  else
    echo "  ✅ No vulnerabilities found"
    echo "### ✅ $REPO - Clean" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
  fi

  echo ""

done <<< "$REPOS"

# Generate final summary
cat >> "$SUMMARY_FILE" <<EOF

---

## Overall Statistics

- **Repositories Scanned**: $REPOS_SCANNED
- **Repositories with Vulnerabilities**: $REPOS_WITH_VULNS
- **Clean Repositories**: $((REPOS_SCANNED - REPOS_WITH_VULNS - REPOS_FAILED))
- **Failed Scans**: $REPOS_FAILED
- **Total Vulnerabilities**: $TOTAL_VULNS

## Recommendations

EOF

if [ "$REPOS_WITH_VULNS" -gt 0 ]; then
  cat >> "$SUMMARY_FILE" <<EOF
### High Priority

1. **Review repositories with critical vulnerabilities first**
2. **Run /fix-vulns on each repository** with vulnerabilities
3. **Create tracking issues** for complex vulnerabilities requiring manual intervention

### Commands to Fix

\`\`\`bash
# For each repository with vulnerabilities:
cd <repo-name>
/fix-vulns --severity=critical  # Fix critical first
/fix-vulns --severity=high      # Then high
# Review and test
# Create PR
\`\`\`

### Automation Options

Consider setting up:
- **Dependabot**: Automated dependency updates
- **GitHub Advanced Security**: Continuous vulnerability scanning
- **Scheduled workflows**: Weekly security scans with /fix-vulns
EOF
else
  cat >> "$SUMMARY_FILE" <<EOF
### All Clear! ✅

No vulnerabilities found at **$SEVERITY** severity level and above.

**Next Steps**:
- Run scan at lower severity levels to catch moderate/low issues
- Set up automated dependency updates (Dependabot)
- Schedule regular security scans
EOF
fi

cat >> "$SUMMARY_FILE" <<EOF

---

**Generated**: $(date -Iseconds)
**Script**: security-scan-all.sh
**Severity Filter**: $SEVERITY and above

EOF

# Display summary
echo ""
echo "=========================================="
echo "📊 Security Scan Complete"
echo "=========================================="
echo ""
echo "Repositories Scanned: $REPOS_SCANNED"
echo "Repositories with Vulnerabilities: $REPOS_WITH_VULNS"
echo "Total Vulnerabilities ($SEVERITY+): $TOTAL_VULNS"
echo "Failed Scans: $REPOS_FAILED"
echo ""
echo "📄 Full report: $SUMMARY_FILE"
echo ""

# Open summary in default viewer if available
if command -v cat >/dev/null 2>&1; then
  echo "📋 Summary Preview:"
  echo "===================="
  head -50 "$SUMMARY_FILE"
  echo ""
  echo "Full report at: $SUMMARY_FILE"
fi

# Exit with appropriate code
if [ "$REPOS_WITH_VULNS" -gt 0 ]; then
  echo "⚠️  Action required: $REPOS_WITH_VULNS repositories have vulnerabilities"
  exit 1
else
  echo "✅ All repositories clean!"
  exit 0
fi
