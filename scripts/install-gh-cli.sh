#!/bin/bash
# Install GitHub CLI on Claude Code web sessions
# This script runs during SessionStart hooks
# Installs to ~/.local/bin (no root required)
# Uses github.com (allowed) instead of cli.github.com (blocked by proxy)

# Error handler - show what failed
trap 'echo "❌ install-gh-cli.sh failed at line $LINENO: $BASH_COMMAND"' ERR
set -e  # Exit on error

echo "🔍 Checking GitHub CLI availability..."
echo "  → CLAUDE_PROJECT_DIR: ${CLAUDE_PROJECT_DIR:-<not set>}"
echo "  → CLAUDE_CODE_REMOTE: ${CLAUDE_CODE_REMOTE:-<not set>}"
echo "  → Working dir: $(pwd)"

# Check if gh is already installed
if command -v gh &> /dev/null; then
  echo "✅ GitHub CLI already installed: $(gh --version | head -n1)"
  exit 0
fi

# Only install in remote (web) environments
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  echo "ℹ️  Skipping gh CLI installation (not in remote environment)"
  exit 0
fi

echo "📦 Installing GitHub CLI from GitHub releases..."

# Verify curl is available (should be in web sessions)
if ! command -v curl &> /dev/null; then
  echo "⚠️  curl not available - cannot download gh CLI"
  echo "ℹ️  gh CLI will not be available in this session"
  exit 0
fi

# Detect architecture
ARCH=$(uname -m)
case "$ARCH" in
  x86_64) GH_ARCH="amd64" ;;
  aarch64|arm64) GH_ARCH="arm64" ;;
  *) echo "❌ Unsupported architecture: $ARCH"; exit 1 ;;
esac

# Get latest version from GitHub API (allowed domain)
echo "  → Fetching latest version from api.github.com..."
GH_VERSION=$(curl -s https://api.github.com/repos/cli/cli/releases/latest | grep '"tag_name"' | cut -d'"' -f4 | sed 's/v//')

if [ -z "$GH_VERSION" ]; then
  echo "⚠️  Failed to fetch latest version (likely blocked by proxy)"
  echo "ℹ️  gh CLI will not be available in this session"
  exit 0
fi

# Download from github.com (allowed domain)
GH_URL="https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_${GH_ARCH}.tar.gz"
GH_TARBALL="/tmp/gh_${GH_VERSION}_linux_${GH_ARCH}.tar.gz"

echo "  → Downloading gh v${GH_VERSION} for ${GH_ARCH}..."
echo "  → URL: $GH_URL"

if ! curl -fsSL "$GH_URL" -o "$GH_TARBALL" 2>&1; then
  echo "⚠️  Download failed (likely blocked by proxy)"
  echo "ℹ️  gh CLI will not be available in this session"
  exit 0
fi

if [ ! -f "$GH_TARBALL" ]; then
  echo "⚠️  Download failed (likely blocked by proxy)"
  echo "ℹ️  gh CLI will not be available in this session"
  exit 0
fi

echo "  → Extracting..."
tar xzf "$GH_TARBALL" -C /tmp

# Install to user-local bin (no root required)
USER_BIN="$HOME/.local/bin"
mkdir -p "$USER_BIN"

echo "  → Installing to $USER_BIN/gh..."
install -m 755 "/tmp/gh_${GH_VERSION}_linux_${GH_ARCH}/bin/gh" "$USER_BIN/"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$USER_BIN:"* ]]; then
  echo "  → Adding $USER_BIN to PATH for this session"
  export PATH="$USER_BIN:$PATH"
fi

# Verify installation
if command -v gh &> /dev/null; then
  echo "✅ GitHub CLI installed successfully: $(gh --version | head -n1)"

  # Cleanup only after successful installation
  rm -f "$GH_TARBALL"
  rm -rf "/tmp/gh_${GH_VERSION}_linux_${GH_ARCH}"
else
  echo "⚠️  GitHub CLI installation failed"
  echo "  → Keeping extracted files for troubleshooting: /tmp/gh_${GH_VERSION}_linux_${GH_ARCH}"
  echo "ℹ️  gh CLI will not be available in this session"
  exit 0
fi

exit 0
