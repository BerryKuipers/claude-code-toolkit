#!/bin/bash
# Configure Git Authentication for Claude Code Environment
# This script sets up git to work with GitHub through the egress proxy

set -e

echo "Configuring git authentication for Claude Code..."

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "ERROR: GITHUB_TOKEN environment variable is not set"
    exit 1
fi

# Get current remote URL
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")

# Check if remote is using local proxy
if [[ "$CURRENT_REMOTE" == *"127.0.0.1"* ]] || [[ "$CURRENT_REMOTE" == *"local_proxy"* ]]; then
    echo "Detected local proxy URL. Switching to HTTPS GitHub URL..."
    
    # Extract repository path from current remote
    REPO_PATH=$(echo "$CURRENT_REMOTE" | sed -n 's|.*\/git\/\(.*\)|\1|p')
    
    if [ -z "$REPO_PATH" ]; then
        echo "ERROR: Could not extract repository path from remote URL: $CURRENT_REMOTE"
        exit 1
    fi
    
    # Set new HTTPS remote
    NEW_REMOTE="https://github.com/$REPO_PATH"
    git remote set-url origin "$NEW_REMOTE"
    echo "Remote URL changed to: $NEW_REMOTE"
fi

# Configure git to use GITHUB_TOKEN for authentication
echo "Configuring git credential helper..."
git config --global credential.helper store

# Configure URL rewriting to inject token
echo "Configuring URL rewriting with GitHub token..."
git config --global url."https://${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"

# Verify configuration
echo ""
echo "Configuration complete!"
echo "Current remote: $(git remote get-url origin)"
echo ""
echo "Testing git connectivity..."
if git ls-remote origin HEAD &>/dev/null; then
    echo "SUCCESS: Git can connect to GitHub!"
else
    echo "WARNING: Could not connect to GitHub. Check your GITHUB_TOKEN."
fi

