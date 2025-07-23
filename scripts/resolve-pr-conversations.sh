#!/bin/bash
# Automatically resolve all unresolved conversations in a GitHub Pull Request
# Bash equivalent of resolve-pr-conversations.ps1

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 -o OWNER -r REPO -p PR_NUMBER [-d]"
    echo ""
    echo "Options:"
    echo "  -o OWNER      Repository owner (username or organization)"
    echo "  -r REPO       Repository name"
    echo "  -p PR_NUMBER  Pull Request number"
    echo "  -d            Dry run - show what would be resolved without actually resolving"
    echo "  -h            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -o BerryKuipers -r crypto-insight -p 33"
    echo "  $0 -o BerryKuipers -r crypto-insight -p 33 -d"
    echo ""
    echo "Requirements:"
    echo "  - GitHub CLI (gh) must be installed and authenticated"
    echo "  - jq must be installed for JSON processing"
}

# Parse command line arguments
OWNER=""
REPO=""
PR_NUMBER=""
DRY_RUN=false

while getopts "o:r:p:dh" opt; do
    case $opt in
        o) OWNER="$OPTARG" ;;
        r) REPO="$OPTARG" ;;
        p) PR_NUMBER="$OPTARG" ;;
        d) DRY_RUN=true ;;
        h) show_usage; exit 0 ;;
        \?) print_error "Invalid option -$OPTARG"; show_usage; exit 1 ;;
    esac
done

# Validate required arguments
if [[ -z "$OWNER" || -z "$REPO" || -z "$PR_NUMBER" ]]; then
    print_error "Missing required arguments"
    show_usage
    exit 1
fi

# Check if required tools are installed
if ! command -v gh &> /dev/null; then
    print_error "GitHub CLI (gh) is not installed. Please install it first."
    echo "Installation: https://cli.github.com/"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    print_error "jq is not installed. Please install it first."
    echo "Installation: sudo apt install jq"
    exit 1
fi

# Check if GitHub CLI is authenticated
if ! gh auth status &> /dev/null; then
    print_error "GitHub CLI is not authenticated. Please run 'gh auth login' first."
    exit 1
fi

print_info "Fetching review threads for PR #$PR_NUMBER in $OWNER/$REPO"

# GraphQL query to get all review threads for the PR
QUERY='query($owner: String!, $repo: String!, $prNumber: Int!) {
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
}'

# Execute the query
RESULT=$(gh api graphql \
    -H "X-Github-Next-Global-ID:1" \
    -f query="$QUERY" \
    -F owner="$OWNER" \
    -F repo="$REPO" \
    -F prNumber="$PR_NUMBER")

# Check if PR exists
if [[ $(echo "$RESULT" | jq -r '.data.repository.pullRequest') == "null" ]]; then
    print_error "Pull Request #$PR_NUMBER not found in $OWNER/$REPO"
    exit 1
fi

# Extract threads
THREADS=$(echo "$RESULT" | jq -r '.data.repository.pullRequest.reviewThreads.nodes')
TOTAL_THREADS=$(echo "$THREADS" | jq length)

print_info "Found $TOTAL_THREADS total review threads"

# Filter for unresolved threads
UNRESOLVED_THREADS=$(echo "$THREADS" | jq '[.[] | select(.isResolved == false)]')
UNRESOLVED_COUNT=$(echo "$UNRESOLVED_THREADS" | jq length)

if [[ $UNRESOLVED_COUNT -eq 0 ]]; then
    print_success "All conversations are already resolved!"
    exit 0
fi

print_warning "Found $UNRESOLVED_COUNT unresolved conversations"

if [[ "$DRY_RUN" == true ]]; then
    print_warning "DRY RUN - Would resolve the following conversations:"
    echo "$UNRESOLVED_THREADS" | jq -r '.[] | 
        "  Thread ID: " + .id + 
        "\n    File: " + (.comments.nodes[0].path // "unknown") + " (line " + (.comments.nodes[0].line // "?" | tostring) + ")" +
        "\n    Author: " + (.comments.nodes[0].author.login // "unknown") + 
        "\n    Preview: " + ((.comments.nodes[0].body // "")[0:100]) + "..." +
        "\n"'
    print_warning "Run without -d to actually resolve these conversations"
    exit 0
fi

# Resolve each unresolved thread
RESOLVED_COUNT=0
FAILED_COUNT=0

echo "$UNRESOLVED_THREADS" | jq -c '.[]' | while read -r thread; do
    THREAD_ID=$(echo "$thread" | jq -r '.id')
    FILE_PATH=$(echo "$thread" | jq -r '.comments.nodes[0].path // "unknown"')
    LINE_NUMBER=$(echo "$thread" | jq -r '.comments.nodes[0].line // "?"')
    
    print_info "Resolving thread: $FILE_PATH:$LINE_NUMBER"
    
    # GraphQL mutation to resolve the thread
    RESOLVE_MUTATION='mutation($threadId: ID!) {
      resolveReviewThread(input: {threadId: $threadId}) {
        thread {
          id
          isResolved
        }
      }
    }'
    
    # Execute the mutation
    if RESOLVE_RESULT=$(gh api graphql \
        -H "X-Github-Next-Global-ID:1" \
        -f query="$RESOLVE_MUTATION" \
        -F threadId="$THREAD_ID" 2>/dev/null); then
        
        IS_RESOLVED=$(echo "$RESOLVE_RESULT" | jq -r '.data.resolveReviewThread.thread.isResolved')
        
        if [[ "$IS_RESOLVED" == "true" ]]; then
            print_success "  Successfully resolved"
            ((RESOLVED_COUNT++))
        else
            print_error "  Failed to resolve (unknown reason)"
            ((FAILED_COUNT++))
        fi
    else
        print_error "  Failed to resolve: API error"
        ((FAILED_COUNT++))
    fi
    
    # Small delay to avoid rate limiting
    sleep 0.1
done

# Summary
echo ""
print_info "Summary:"
print_success "  Resolved: $RESOLVED_COUNT"
if [[ $FAILED_COUNT -gt 0 ]]; then
    print_error "  Failed: $FAILED_COUNT"
fi
print_info "  PR: https://github.com/$OWNER/$REPO/pull/$PR_NUMBER"

if [[ $RESOLVED_COUNT -gt 0 ]]; then
    echo ""
    print_success "Successfully resolved $RESOLVED_COUNT conversation(s)!"
fi
