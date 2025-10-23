#!/bin/bash
# Repository Health Check
# Cross-platform script to check health status of all repositories
# Usage: ./scripts/repo-health-check.sh [--format=text|json|markdown]

set -e

GITHUB_USER="${GITHUB_USER:-BerryKuipers}"
WORK_DIR="${WORK_DIR:-/tmp/repo-health-check}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_DIR="${WORK_DIR}/reports-${TIMESTAMP}"
OUTPUT_FORMAT="${1:-markdown}"

# Parse format argument
if [[ "$1" == --format=* ]]; then
  OUTPUT_FORMAT="${1#*=}"
fi

echo "🏥 Repository Health Check"
echo "=========================="
echo "User: $GITHUB_USER"
echo "Format: $OUTPUT_FORMAT"
echo "Report dir: $REPORT_DIR"
echo ""

# Create report directory
mkdir -p "$REPORT_DIR"

# Initialize report file
REPORT_FILE="$REPORT_DIR/health-report.$OUTPUT_FORMAT"

# Health check metrics
TOTAL_REPOS=0
HEALTHY_REPOS=0
WARNING_REPOS=0
CRITICAL_REPOS=0

# Temporary data storage
declare -A REPO_DATA

echo "📋 Fetching repository list..."
REPOS=$(~/.local/bin/gh repo list "$GITHUB_USER" --limit 100 --json name,isPrivate,pushedAt,updatedAt,diskUsage,stargazerCount,forkCount --jq '.[]')
TOTAL_REPOS=$(echo "$REPOS" | jq -s 'length')
echo "Found $TOTAL_REPOS repositories"
echo ""

# Initialize report based on format
case "$OUTPUT_FORMAT" in
  json)
    echo '{"timestamp":"'$(date -Iseconds)'","user":"'$GITHUB_USER'","repositories":[' > "$REPORT_FILE"
    ;;
  markdown)
    cat > "$REPORT_FILE" <<EOF
# Repository Health Report

**Date**: $(date -Iseconds)
**User**: $GITHUB_USER
**Total Repositories**: $TOTAL_REPOS

---

## Health Summary

EOF
    ;;
  text)
    cat > "$REPORT_FILE" <<EOF
REPOSITORY HEALTH REPORT
========================

Date: $(date -Iseconds)
User: $GITHUB_USER
Total Repositories: $TOTAL_REPOS

EOF
    ;;
esac

echo "🔍 Analyzing repositories..."
echo ""

FIRST_REPO=true

# Analyze each repository
echo "$REPOS" | jq -c '.' | while IFS= read -r REPO_JSON; do
  REPO=$(echo "$REPO_JSON" | jq -r '.name')
  echo "📦 Checking: $REPO"

  # Extract metadata
  IS_PRIVATE=$(echo "$REPO_JSON" | jq -r '.isPrivate')
  PUSHED_AT=$(echo "$REPO_JSON" | jq -r '.pushedAt')
  UPDATED_AT=$(echo "$REPO_JSON" | jq -r '.updatedAt')
  DISK_USAGE=$(echo "$REPO_JSON" | jq -r '.diskUsage')
  STARS=$(echo "$REPO_JSON" | jq -r '.stargazerCount')
  FORKS=$(echo "$REPO_JSON" | jq -r '.forkCount')

  # Calculate days since last push
  if [ -n "$PUSHED_AT" ] && [ "$PUSHED_AT" != "null" ]; then
    DAYS_SINCE_PUSH=$(( ($(date +%s) - $(date -d "$PUSHED_AT" +%s)) / 86400 ))
  else
    DAYS_SINCE_PUSH=999
  fi

  # Initialize health metrics
  HEALTH_SCORE=100
  HEALTH_STATUS="healthy"
  ISSUES=()
  WARNINGS=()

  # Check 1: Stale repository (no activity in 180 days)
  if [ "$DAYS_SINCE_PUSH" -gt 180 ]; then
    HEALTH_SCORE=$((HEALTH_SCORE - 30))
    ISSUES+=("Stale: No activity in $DAYS_SINCE_PUSH days")
  elif [ "$DAYS_SINCE_PUSH" -gt 90 ]; then
    HEALTH_SCORE=$((HEALTH_SCORE - 10))
    WARNINGS+=("Inactive: Last push $DAYS_SINCE_PUSH days ago")
  fi

  # Check 2: Get branch information
  DEFAULT_BRANCH=$(~/.local/bin/gh api repos/$GITHUB_USER/$REPO --jq '.default_branch' 2>/dev/null || echo "unknown")

  # Check 3: Open issues and PRs
  OPEN_ISSUES=$(~/.local/bin/gh issue list --repo "$GITHUB_USER/$REPO" --state open --limit 1000 --json number --jq 'length' 2>/dev/null || echo "0")
  OPEN_PRS=$(~/.local/bin/gh pr list --repo "$GITHUB_USER/$REPO" --state open --limit 1000 --json number --jq 'length' 2>/dev/null || echo "0")

  if [ "$OPEN_ISSUES" -gt 50 ]; then
    HEALTH_SCORE=$((HEALTH_SCORE - 20))
    ISSUES+=("High issue count: $OPEN_ISSUES open issues")
  elif [ "$OPEN_ISSUES" -gt 20 ]; then
    HEALTH_SCORE=$((HEALTH_SCORE - 10))
    WARNINGS+=("Moderate issues: $OPEN_ISSUES open")
  fi

  if [ "$OPEN_PRS" -gt 10 ]; then
    HEALTH_SCORE=$((HEALTH_SCORE - 15))
    ISSUES+=("High PR count: $OPEN_PRS open PRs")
  elif [ "$OPEN_PRS" -gt 5 ]; then
    HEALTH_SCORE=$((HEALTH_SCORE - 5))
    WARNINGS+=("Several PRs: $OPEN_PRS open")
  fi

  # Check 4: Clone and check locally (if Node.js project)
  REPO_DIR="$WORK_DIR/$REPO"
  HAS_PACKAGE_JSON=false
  OUTDATED_DEPS=0
  VULNERABILITIES=0
  BUILD_STATUS="unknown"

  if ~/.local/bin/gh repo clone "$GITHUB_USER/$REPO" "$REPO_DIR" --quiet 2>/dev/null; then
    cd "$REPO_DIR"

    # Check if Node.js project
    if [ -f "package.json" ]; then
      HAS_PACKAGE_JSON=true

      # Check for outdated dependencies
      if [ -f "package-lock.json" ] || [ -f "yarn.lock" ] || [ -f "pnpm-lock.yaml" ]; then
        # Quick dependency check
        OUTDATED_DEPS=$(npm outdated --json 2>/dev/null | jq 'length' 2>/dev/null || echo "0")

        if [ "$OUTDATED_DEPS" -gt 20 ]; then
          HEALTH_SCORE=$((HEALTH_SCORE - 15))
          ISSUES+=("Many outdated deps: $OUTDATED_DEPS packages")
        elif [ "$OUTDATED_DEPS" -gt 10 ]; then
          HEALTH_SCORE=$((HEALTH_SCORE - 5))
          WARNINGS+=("Some outdated deps: $OUTDATED_DEPS packages")
        fi

        # Quick vulnerability check (without installing)
        if npm audit --audit-level=high --json > /tmp/audit-$REPO.json 2>/dev/null; then
          VULNERABILITIES=0
        else
          CRITICAL_VULNS=$(jq -r '.metadata.vulnerabilities.critical // 0' /tmp/audit-$REPO.json 2>/dev/null || echo "0")
          HIGH_VULNS=$(jq -r '.metadata.vulnerabilities.high // 0' /tmp/audit-$REPO.json 2>/dev/null || echo "0")
          VULNERABILITIES=$((CRITICAL_VULNS + HIGH_VULNS))

          if [ "$VULNERABILITIES" -gt 0 ]; then
            HEALTH_SCORE=$((HEALTH_SCORE - 25))
            ISSUES+=("Security: $CRITICAL_VULNS critical, $HIGH_VULNS high vulnerabilities")
          fi
        fi
      else
        WARNINGS+=("No lock file found")
        HEALTH_SCORE=$((HEALTH_SCORE - 5))
      fi

      # Check for test script
      if ! grep -q '"test"' package.json; then
        WARNINGS+=("No test script defined")
        HEALTH_SCORE=$((HEALTH_SCORE - 5))
      fi

      # Check for README
      if [ ! -f "README.md" ]; then
        WARNINGS+=("No README.md")
        HEALTH_SCORE=$((HEALTH_SCORE - 5))
      fi
    fi
  else
    WARNINGS+=("Could not clone repository")
  fi

  # Determine health status
  if [ "$HEALTH_SCORE" -ge 80 ]; then
    HEALTH_STATUS="✅ healthy"
    HEALTHY_REPOS=$((HEALTHY_REPOS + 1))
  elif [ "$HEALTH_SCORE" -ge 50 ]; then
    HEALTH_STATUS="⚠️  warning"
    WARNING_REPOS=$((WARNING_REPOS + 1))
  else
    HEALTH_STATUS="🔴 critical"
    CRITICAL_REPOS=$((CRITICAL_REPOS + 1))
  fi

  echo "  Status: $HEALTH_STATUS (Score: $HEALTH_SCORE/100)"
  echo ""

  # Output based on format
  case "$OUTPUT_FORMAT" in
    json)
      if [ "$FIRST_REPO" = false ]; then
        echo "," >> "$REPORT_FILE"
      fi
      FIRST_REPO=false

      cat >> "$REPORT_FILE" <<EOF
{"name":"$REPO","health_score":$HEALTH_SCORE,"status":"$HEALTH_STATUS","metrics":{"days_since_push":$DAYS_SINCE_PUSH,"open_issues":$OPEN_ISSUES,"open_prs":$OPEN_PRS,"outdated_deps":$OUTDATED_DEPS,"vulnerabilities":$VULNERABILITIES,"stars":$STARS,"forks":$FORKS},"issues":$(printf '%s\n' "${ISSUES[@]}" | jq -R . | jq -s .),"warnings":$(printf '%s\n' "${WARNINGS[@]}" | jq -R . | jq -s .)}
EOF
      ;;
    markdown)
      cat >> "$REPORT_FILE" <<EOF
### $HEALTH_STATUS $REPO

**Health Score**: $HEALTH_SCORE/100

**Metrics**:
- Last Push: $DAYS_SINCE_PUSH days ago
- Open Issues: $OPEN_ISSUES
- Open PRs: $OPEN_PRS
- Outdated Dependencies: $OUTDATED_DEPS
- High/Critical Vulnerabilities: $VULNERABILITIES
- Stars: $STARS | Forks: $FORKS

EOF
      if [ ${#ISSUES[@]} -gt 0 ]; then
        echo "**Issues**:" >> "$REPORT_FILE"
        printf -- '- %s\n' "${ISSUES[@]}" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
      fi

      if [ ${#WARNINGS[@]} -gt 0 ]; then
        echo "**Warnings**:" >> "$REPORT_FILE"
        printf -- '- %s\n' "${WARNINGS[@]}" >> "$REPORT_FILE"
        echo "" >> "$REPORT_FILE"
      fi

      echo "---" >> "$REPORT_FILE"
      echo "" >> "$REPORT_FILE"
      ;;
    text)
      cat >> "$REPORT_FILE" <<EOF

Repository: $REPO
Status: $HEALTH_STATUS
Health Score: $HEALTH_SCORE/100
Days Since Push: $DAYS_SINCE_PUSH
Open Issues: $OPEN_ISSUES
Open PRs: $OPEN_PRS
Outdated Deps: $OUTDATED_DEPS
Vulnerabilities: $VULNERABILITIES

EOF
      if [ ${#ISSUES[@]} -gt 0 ]; then
        echo "Issues:" >> "$REPORT_FILE"
        printf -- '  - %s\n' "${ISSUES[@]}" >> "$REPORT_FILE"
      fi

      if [ ${#WARNINGS[@]} -gt 0 ]; then
        echo "Warnings:" >> "$REPORT_FILE"
        printf -- '  - %s\n' "${WARNINGS[@]}" >> "$REPORT_FILE"
      fi

      echo "----------------------------------------" >> "$REPORT_FILE"
      ;;
  esac
done

# Finalize report
case "$OUTPUT_FORMAT" in
  json)
    cat >> "$REPORT_FILE" <<EOF
],"summary":{"total":$TOTAL_REPOS,"healthy":$HEALTHY_REPOS,"warning":$WARNING_REPOS,"critical":$CRITICAL_REPOS}}
EOF
    ;;
  markdown)
    cat >> "$REPORT_FILE" <<EOF

## Summary Statistics

- **Total Repositories**: $TOTAL_REPOS
- **Healthy**: $HEALTHY_REPOS ($(( HEALTHY_REPOS * 100 / TOTAL_REPOS ))%)
- **Warning**: $WARNING_REPOS ($(( WARNING_REPOS * 100 / TOTAL_REPOS ))%)
- **Critical**: $CRITICAL_REPOS ($(( CRITICAL_REPOS * 100 / TOTAL_REPOS ))%)

## Recommendations

EOF
    if [ "$CRITICAL_REPOS" -gt 0 ]; then
      cat >> "$REPORT_FILE" <<EOF
### Critical Attention Needed

$CRITICAL_REPOS repositories require immediate attention.

**Actions**:
1. Review critical repositories above
2. Run \`/fix-vulns\` on repositories with security issues
3. Run \`/update-deps\` on repositories with outdated dependencies
4. Address stale repositories (archive or update)

EOF
    fi

    cat >> "$REPORT_FILE" <<EOF
### Maintenance Schedule

- **Weekly**: Review warning-level repositories
- **Monthly**: Run \`/update-deps --scope=security\` on all repos
- **Quarterly**: Comprehensive security scan with \`security-scan-all.sh\`

---

**Generated**: $(date -Iseconds)
**Script**: repo-health-check.sh
EOF
    ;;
  text)
    cat >> "$REPORT_FILE" <<EOF

========================================
SUMMARY STATISTICS
========================================

Total Repositories: $TOTAL_REPOS
Healthy: $HEALTHY_REPOS ($(( HEALTHY_REPOS * 100 / TOTAL_REPOS ))%)
Warning: $WARNING_REPOS ($(( WARNING_REPOS * 100 / TOTAL_REPOS ))%)
Critical: $CRITICAL_REPOS ($(( CRITICAL_REPOS * 100 / TOTAL_REPOS ))%)

Generated: $(date -Iseconds)
Script: repo-health-check.sh
EOF
    ;;
esac

# Display summary
echo ""
echo "=========================================="
echo "📊 Health Check Complete"
echo "=========================================="
echo ""
echo "Total Repositories: $TOTAL_REPOS"
echo "✅ Healthy: $HEALTHY_REPOS ($(( HEALTHY_REPOS * 100 / TOTAL_REPOS ))%)"
echo "⚠️  Warning: $WARNING_REPOS ($(( WARNING_REPOS * 100 / TOTAL_REPOS ))%)"
echo "🔴 Critical: $CRITICAL_REPOS ($(( CRITICAL_REPOS * 100 / TOTAL_REPOS ))%)"
echo ""
echo "📄 Full report: $REPORT_FILE"
echo ""

# Exit with appropriate code
if [ "$CRITICAL_REPOS" -gt 0 ]; then
  echo "⚠️  Action required: $CRITICAL_REPOS repositories need attention"
  exit 1
elif [ "$WARNING_REPOS" -gt 0 ]; then
  echo "ℹ️  $WARNING_REPOS repositories have warnings"
  exit 0
else
  echo "✅ All repositories healthy!"
  exit 0
fi
