#!/bin/bash
# Install git hooks for auto-syncing Claude Code Toolkit
# Run once after cloning the repo: ./scripts/install-git-hooks.sh

set -e

echo "🔧 Installing git hooks for Claude Code Toolkit auto-sync..."

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Install post-merge hook (runs after git pull)
cat > .git/hooks/post-merge << 'EOF'
#!/bin/bash
# Auto-sync Claude Code Toolkit after git pull/merge
# This ensures VS Code/Cursor users get toolkit updates automatically

# Only sync if .claude-toolkit submodule exists
if [ -f ".gitmodules" ] && grep -q "\.claude-toolkit" .gitmodules; then
  echo ""
  echo "🔄 Auto-syncing Claude Code Toolkit..."

  # Run sync script if it exists
  if [ -f "scripts/sync-claude-toolkit.sh" ]; then
    bash scripts/sync-claude-toolkit.sh
  fi
fi
EOF

chmod +x .git/hooks/post-merge

# Install post-checkout hook (runs after git checkout)
cat > .git/hooks/post-checkout << 'EOF'
#!/bin/bash
# Auto-sync Claude Code Toolkit after git checkout
# This ensures VS Code/Cursor users get toolkit updates when switching branches

# Only sync if .claude-toolkit submodule exists
if [ -f ".gitmodules" ] && grep -q "\.claude-toolkit" .gitmodules; then
  # Run sync script if it exists
  if [ -f "scripts/sync-claude-toolkit.sh" ]; then
    echo ""
    echo "🔄 Auto-syncing Claude Code Toolkit..."
    bash scripts/sync-claude-toolkit.sh
  fi
fi
EOF

chmod +x .git/hooks/post-checkout

echo ""
echo "✅ Git hooks installed successfully!"
echo ""
echo "Installed hooks:"
echo "  - post-merge  → Auto-syncs after 'git pull'"
echo "  - post-checkout → Auto-syncs after 'git checkout'"
echo ""
echo "Now when you pull or switch branches in VS Code/Cursor,"
echo "the toolkit will automatically sync!"
