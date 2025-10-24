#!/bin/bash
# Monitor GitHub Actions CI workflow status
# Usage: ./monitor_ci.sh <owner> <repo> <branch> [commit-sha]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OWNER="${1:-BerryKuipers}"
REPO="${2:-crypto-insight}"
BRANCH="${3:-main}"
COMMIT_SHA="${4:-}"
CHECK_INTERVAL=15  # seconds
MAX_CHECKS=60      # 15 minutes total

# Detect repo owner/name from git remote if not provided
if [[ -z "$OWNER" ]] || [[ -z "$REPO" ]]; then
    REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
    if [[ $REMOTE_URL =~ github\.com[:/]([^/]+)/([^/.]+) ]]; then
        OWNER="${BASH_REMATCH[1]}"
        REPO="${BASH_REMATCH[2]}"
    fi
fi

# Get current branch if not specified
if [[ -z "$BRANCH" ]] || [[ "$BRANCH" == "main" ]]; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
fi

# Get current commit if not specified
if [[ -z "$COMMIT_SHA" ]]; then
    COMMIT_SHA=$(git rev-parse HEAD 2>/dev/null || echo "")
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 CI Workflow Monitor${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

echo -e "${BLUE}Repository:${NC} $OWNER/$REPO"
echo -e "${BLUE}Branch:${NC} $BRANCH"
if [[ -n "$COMMIT_SHA" ]]; then
    echo -e "${BLUE}Commit:${NC} ${COMMIT_SHA:0:7}"
fi
echo ""

# Function to check workflow status
check_workflow_status() {
    local api_url="https://api.github.com/repos/$OWNER/$REPO/actions/runs"

    if [[ -n "$COMMIT_SHA" ]]; then
        api_url="${api_url}?head_sha=${COMMIT_SHA}&per_page=5"
    else
        api_url="${api_url}?branch=${BRANCH}&per_page=5"
    fi

    # Fetch workflow runs
    local response=$(curl -s -H "Accept: application/vnd.github+json" "$api_url" 2>/dev/null)

    if [[ -z "$response" ]] || [[ "$response" == *"API rate limit exceeded"* ]]; then
        echo -e "${RED}❌ Failed to fetch workflow status (API error)${NC}"
        return 1
    fi

    # Parse workflow runs (get the first/latest one)
    local workflow_id=$(echo "$response" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    local status=$(echo "$response" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
    local conclusion=$(echo "$response" | grep -o '"conclusion":"[^"]*"' | head -1 | cut -d'"' -f4)
    local workflow_name=$(echo "$response" | grep -o '"name":"[^"]*"' | head -1 | cut -d'"' -f4)
    local html_url=$(echo "$response" | grep -o '"html_url":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [[ -z "$workflow_id" ]]; then
        echo -e "${YELLOW}⏳ No workflow run found yet... waiting for CI to start${NC}"
        return 2
    fi

    echo -e "${BLUE}Workflow:${NC} $workflow_name (ID: $workflow_id)"
    echo -e "${BLUE}URL:${NC} $html_url"
    echo ""

    # Display status
    case "$status" in
        "completed")
            case "$conclusion" in
                "success")
                    echo -e "${GREEN}✅ CI PASSED - All checks successful!${NC}\n"
                    return 0
                    ;;
                "failure")
                    echo -e "${RED}❌ CI FAILED - Some checks failed${NC}\n"
                    fetch_failed_jobs "$workflow_id"
                    return 1
                    ;;
                "cancelled")
                    echo -e "${YELLOW}⚠️  CI CANCELLED${NC}\n"
                    return 1
                    ;;
                *)
                    echo -e "${YELLOW}⚠️  CI COMPLETED with conclusion: $conclusion${NC}\n"
                    return 1
                    ;;
            esac
            ;;
        "in_progress"|"queued"|"waiting")
            echo -e "${YELLOW}⏳ CI $status...${NC}"
            fetch_job_status "$workflow_id"
            return 2
            ;;
        *)
            echo -e "${YELLOW}❓ Unknown status: $status${NC}\n"
            return 2
            ;;
    esac
}

# Function to fetch job status details
fetch_job_status() {
    local workflow_id="$1"
    local jobs_url="https://api.github.com/repos/$OWNER/$REPO/actions/runs/$workflow_id/jobs"

    local jobs_response=$(curl -s -H "Accept: application/vnd.github+json" "$jobs_url" 2>/dev/null)

    if [[ -z "$jobs_response" ]]; then
        return
    fi

    # Parse jobs
    echo -e "\n${BLUE}Jobs:${NC}"
    while IFS= read -r job; do
        local job_name=$(echo "$job" | cut -d'|' -f1)
        local job_status=$(echo "$job" | cut -d'|' -f2)
        local job_conclusion=$(echo "$job" | cut -d'|' -f3)

        local icon=""
        local color="$NC"

        case "$job_status" in
            "completed")
                case "$job_conclusion" in
                    "success") icon="✅"; color="$GREEN" ;;
                    "failure") icon="❌"; color="$RED" ;;
                    "skipped") icon="⏭️ "; color="$YELLOW" ;;
                    *) icon="⚠️ "; color="$YELLOW" ;;
                esac
                ;;
            "in_progress") icon="⏳"; color="$YELLOW" ;;
            "queued"|"waiting") icon="⏸️ "; color="$BLUE" ;;
            *) icon="❓"; ;;
        esac

        echo -e "  ${color}${icon} ${job_name}${NC} (${job_status})"
    done < <(echo "$jobs_response" | grep -o '"name":"[^"]*","status":"[^"]*","conclusion":"[^"]*"' | sed 's/"name":"//; s/","status":"/|/; s/","conclusion":"/|/; s/"$//')

    echo ""
}

# Function to fetch failed job details
fetch_failed_jobs() {
    local workflow_id="$1"
    local jobs_url="https://api.github.com/repos/$OWNER/$REPO/actions/runs/$workflow_id/jobs"

    local jobs_response=$(curl -s -H "Accept: application/vnd.github+json" "$jobs_url" 2>/dev/null)

    if [[ -z "$jobs_response" ]]; then
        return
    fi

    echo -e "${RED}Failed Jobs:${NC}"
    while IFS= read -r job; do
        local job_name=$(echo "$job" | cut -d'|' -f1)
        local job_conclusion=$(echo "$job" | cut -d'|' -f2)

        if [[ "$job_conclusion" == "failure" ]]; then
            echo -e "  ${RED}❌ ${job_name}${NC}"
        fi
    done < <(echo "$jobs_response" | grep -o '"name":"[^"]*".*"conclusion":"[^"]*"' | sed 's/"name":"//; s/".*"conclusion":"/|/; s/"$//')

    echo ""
}

# Main monitoring loop
check_count=0
while [[ $check_count -lt $MAX_CHECKS ]]; do
    check_workflow_status
    result=$?

    if [[ $result -eq 0 ]]; then
        # Success
        exit 0
    elif [[ $result -eq 1 ]]; then
        # Failed
        exit 1
    fi

    # Still running (result == 2)
    ((check_count++))

    if [[ $check_count -ge $MAX_CHECKS ]]; then
        echo -e "${RED}⏱️  Timeout: CI workflow still running after 15 minutes${NC}"
        echo -e "${YELLOW}Check status manually: https://github.com/$OWNER/$REPO/actions${NC}\n"
        exit 1
    fi

    echo -e "${BLUE}Next check in ${CHECK_INTERVAL}s... (${check_count}/${MAX_CHECKS})${NC}\n"
    sleep $CHECK_INTERVAL
done
