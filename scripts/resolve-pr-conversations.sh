#!/usr/bin/env bash
#
# Automatically resolve all unresolved conversations in a GitHub Pull Request
#
# Usage:
#   ./scripts/resolve-pr-conversations.sh <PR_NUMBER> [--dry-run]
#
# Examples:
#   ./scripts/resolve-pr-conversations.sh 25
#   ./scripts/resolve-pr-conversations.sh 25 --dry-run
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Parameters
OWNER="${OWNER:-BerryKuipers}"
REPO="${REPO:-WescoBar-Universe-Storyteller}"
PR_NUMBER=${1:-""}
DRY_RUN=false

# Parse arguments
if [ -z "$PR_NUMBER" ]; then
  echo -e "${RED}❌ Error: PR number required${RESET}"
  echo "Usage: $0 <PR_NUMBER> [--dry-run]"
  exit 1
fi

if [ "$2" = "--dry-run" ]; then
  DRY_RUN=true
fi

echo -e "${BLUE}Fetching review threads for PR #${PR_NUMBER} in ${OWNER}/${REPO}${RESET}"

# GraphQL query to get all review threads
QUERY='
query($owner: String!, $repo: String!, $prNumber: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $prNumber) {
      id
      title
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes {
              path
              line
              body
              author {
                login
              }
            }
          }
        }
      }
    }
  }
}
'

# Fetch PR data
RESULT=$(gh api graphql -H "X-Github-Next-Global-ID:1" \
  -f query="$QUERY" \
  -F owner="$OWNER" \
  -F repo="$REPO" \
  -F prNumber="$PR_NUMBER")

# Check if PR exists
if ! echo "$RESULT" | jq -e '.data.repository.pullRequest' >/dev/null 2>&1; then
  echo -e "${RED}❌ Pull Request #${PR_NUMBER} not found in ${OWNER}/${REPO}${RESET}"
  exit 1
fi

# Extract threads
THREADS=$(echo "$RESULT" | jq -r '.data.repository.pullRequest.reviewThreads.nodes')
TOTAL_COUNT=$(echo "$THREADS" | jq 'length')

echo -e "${BLUE}Found ${TOTAL_COUNT} total review threads${RESET}"

# Filter unresolved threads
UNRESOLVED_THREADS=$(echo "$THREADS" | jq '[.[] | select(.isResolved == false)]')
UNRESOLVED_COUNT=$(echo "$UNRESOLVED_THREADS" | jq 'length')

if [ "$UNRESOLVED_COUNT" -eq 0 ]; then
  echo -e "${GREEN}✅ All conversations are already resolved!${RESET}"
  exit 0
fi

echo -e "${YELLOW}Found ${UNRESOLVED_COUNT} unresolved conversations${RESET}"

# Dry run mode
if [ "$DRY_RUN" = true ]; then
  echo -e "${YELLOW}DRY RUN - Would resolve the following conversations:${RESET}"
  echo "$UNRESOLVED_THREADS" | jq -r '.[] |
    "  Thread ID: \(.id)\n    File: \(.comments.nodes[0].path) (line \(.comments.nodes[0].line))\n    Author: \(.comments.nodes[0].author.login)\n    Preview: \(.comments.nodes[0].body[0:100])...\n"'
  echo -e "${YELLOW}Run without --dry-run to actually resolve these conversations${RESET}"
  exit 0
fi

# Resolve threads
RESOLVED_COUNT=0
FAILED_COUNT=0

echo "$UNRESOLVED_THREADS" | jq -r '.[].id' | while read -r THREAD_ID; do
  # Get thread details for logging
  THREAD_INFO=$(echo "$UNRESOLVED_THREADS" | jq -r --arg tid "$THREAD_ID" '.[] | select(.id == $tid)')
  FILE_PATH=$(echo "$THREAD_INFO" | jq -r '.comments.nodes[0].path')
  LINE_NUM=$(echo "$THREAD_INFO" | jq -r '.comments.nodes[0].line')

  echo -e "${BLUE}Resolving thread: ${FILE_PATH}:${LINE_NUM}${RESET}"

  # GraphQL mutation to resolve thread
  RESOLVE_MUTATION='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread {
        id
        isResolved
      }
    }
  }
  '

  # Execute mutation
  if RESOLVE_RESULT=$(gh api graphql -H "X-Github-Next-Global-ID:1" \
    -f query="$RESOLVE_MUTATION" \
    -F threadId="$THREAD_ID" 2>&1); then

    IS_RESOLVED=$(echo "$RESOLVE_RESULT" | jq -r '.data.resolveReviewThread.thread.isResolved')

    if [ "$IS_RESOLVED" = "true" ]; then
      echo -e "${GREEN}  ✅ Successfully resolved${RESET}"
      ((RESOLVED_COUNT++)) || true
    else
      echo -e "${RED}  ❌ Failed to resolve (unknown reason)${RESET}"
      ((FAILED_COUNT++)) || true
    fi
  else
    echo -e "${RED}  ❌ Failed to resolve: $RESOLVE_RESULT${RESET}"
    ((FAILED_COUNT++)) || true
  fi

  # Small delay to avoid rate limiting
  sleep 0.1
done

# Summary
echo ""
echo -e "${BLUE}📊 Summary:${RESET}"
echo -e "${GREEN}  ✅ Resolved: ${RESOLVED_COUNT}${RESET}"
if [ "$FAILED_COUNT" -gt 0 ]; then
  echo -e "${RED}  ❌ Failed: ${FAILED_COUNT}${RESET}"
fi
echo -e "${BLUE}  🔗 PR: https://github.com/${OWNER}/${REPO}/pull/${PR_NUMBER}${RESET}"

if [ "$RESOLVED_COUNT" -gt 0 ]; then
  echo ""
  echo -e "${GREEN}🎉 Successfully resolved ${RESOLVED_COUNT} conversation(s)!${RESET}"
fi
