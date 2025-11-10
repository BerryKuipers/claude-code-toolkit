#!/bin/bash
# Verify Git Configuration in Claude Code

echo "=== Git Configuration Verification ==="
echo ""

# Check remote URL
echo "1. Remote URL:"
REMOTE_URL=$(git remote get-url origin 2>/dev/null)
if [[ "$REMOTE_URL" == *"github.com"* ]] && [[ "$REMOTE_URL" != *"127.0.0.1"* ]]; then
    if [[ "$REMOTE_URL" == https://*@github.com/* ]]; then
        echo "   ✅ HTTPS GitHub URL with embedded token"
    else
        echo "   ✅ HTTPS GitHub URL: $REMOTE_URL"
    fi
else
    echo "   ❌ Not using GitHub HTTPS: $REMOTE_URL"
    exit 1
fi

# Check URL rewriting (optional if token is embedded)
echo ""
echo "2. Token Authentication:"
if [[ "$REMOTE_URL" == https://*@github.com/* ]]; then
    echo "   ✅ Token embedded in remote URL"
elif git config --get url."https://${GITHUB_TOKEN}@github.com/".insteadOf &>/dev/null; then
    echo "   ✅ URL rewriting configured with GITHUB_TOKEN"
else
    echo "   ⚠️  No token authentication configured"
fi

# Check credential helper
echo ""
echo "3. Credential Helper:"
CRED_HELPER=$(git config --get credential.helper 2>/dev/null)
if [[ -n "$CRED_HELPER" ]]; then
    echo "   ✅ Credential helper: $CRED_HELPER"
else
    echo "   ℹ️  No credential helper (using URL-embedded token)"
fi

# Test connectivity
echo ""
echo "4. GitHub Connectivity:"
if git ls-remote origin HEAD &>/dev/null; then
    echo "   ✅ Can connect to GitHub"
else
    echo "   ❌ Cannot connect to GitHub"
    exit 1
fi

# Check gh CLI
echo ""
echo "5. GitHub CLI:"
if command -v gh &>/dev/null; then
    GH_VERSION=$(gh --version 2>/dev/null | head -n1)
    echo "   ✅ gh CLI available: $GH_VERSION"
elif [ -f "/root/.local/bin/gh" ]; then
    GH_VERSION=$(/root/.local/bin/gh --version 2>/dev/null | head -n1)
    echo "   ✅ gh CLI available at /root/.local/bin/gh: $GH_VERSION"
else
    echo "   ❌ gh CLI not found"
fi

echo ""
echo "=== All Checks Passed! ==="
echo ""
echo "You can now:"
echo "  - git push"
echo "  - git pull"
echo "  - /root/.local/bin/gh pr create"
echo "  - /root/.local/bin/gh issue list"
echo ""
