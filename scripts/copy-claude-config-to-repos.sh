#!/bin/bash
# Copy Claude Code configuration to multiple repositories
# Usage: ./scripts/copy-claude-config-to-repos.sh

set -e

WESCOBAR_DIR="/home/user/WescoBar-Universe-Storyteller"

# Define your target repositories here
# Organized by priority - uncomment/comment as needed

# 🔥 HIGH PRIORITY - Active AI/Complex Projects
REPOS=(
  "/home/user/TribeVibe"              # Community dating app (React + Backend)
  "/home/user/home-sage"              # Multi-agent home automation
  "/home/user/TuneScout"              # AI music discovery
  "/home/user/SceneSpeak"             # Real-time AI commentator
  "/home/user/quantfolio"             # Crypto portfolio tracker (Blazor/C#)

  # 🟡 MEDIUM PRIORITY - Infrastructure & Tools
  "/home/user/AgenticDevelopment"     # Agentic development experiments
  "/home/user/TetherKey"              # Event access control (ASP.NET)
  "/home/user/mcp-servers"            # Multiple MCP servers
  "/home/user/mcp-qdrant"             # MCP Qdrant integration

  # 🟢 ACTIVE PROJECTS - Good candidates
  "/home/user/GreenSphere-"           # Smart herb management
  "/home/user/oraculum"               # Voice AI assistant
  "/home/user/audiotagger_2025"       # Audio file management
  "/home/user/MixItUp"                # (No description - check if active)

  # 🔵 ADDITIONAL PROJECTS
  "/home/user/PinballDreaming"        # Pinball project
  "/home/user/GenZeditAi"             # Gen Z edit AI
  "/home/user/crypto-insight"         # Crypto insights
  "/home/user/json-event-editor"      # JSON event editor
  "/home/user/nas-playlist-generator" # NAS playlist generator
  "/home/user/GreenHomeAI"            # Green home AI
  "/home/user/crypto_ui"              # Crypto UI

  # 🔵 SKIP THESE (duplicates or special cases)
  # "/home/user/Audiotagger"            # Old version (audiotagger_2025 is newer)
  # "/home/user/dev-setup-windows"      # Windows-specific setup
  # "/home/user/SpeechInjector"
  # "/home/user/webinar_insights"
)

echo "📦 Copying Claude Code configuration to multiple repositories..."
echo "Source: $WESCOBAR_DIR"
echo ""

for TARGET_REPO in "${REPOS[@]}"; do
  echo "---"
  echo "📁 Target: $TARGET_REPO"

  # Check if target exists
  if [ ! -d "$TARGET_REPO" ]; then
    echo "⚠️  Skipping: Directory doesn't exist"
    continue
  fi

  cd "$TARGET_REPO"

  # Check if it's a git repo
  if [ ! -d ".git" ]; then
    echo "⚠️  Skipping: Not a git repository"
    continue
  fi

  echo "  → Creating directories..."
  mkdir -p .claude scripts docs

  echo "  → Copying SessionStart hooks..."
  cp "$WESCOBAR_DIR/.claude/settings.json" .claude/

  echo "  → Copying gh CLI installer..."
  cp "$WESCOBAR_DIR/scripts/install-gh-cli.sh" scripts/
  chmod +x scripts/install-gh-cli.sh

  echo "  → Copying agents and commands..."
  cp "$WESCOBAR_DIR/.claude/config.yml" .claude/
  cp -r "$WESCOBAR_DIR/.claude/agents" .claude/
  cp -r "$WESCOBAR_DIR/.claude/commands" .claude/

  echo "  → Copying documentation..."
  cp "$WESCOBAR_DIR/docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md" docs/
  cp "$WESCOBAR_DIR/docs/COPY_TO_NEW_REPO.md" docs/

  echo "  → Customizing config.yml for this repo..."
  REPO_NAME=$(basename "$TARGET_REPO")
  # Update workspace tempDir with repo name
  sed -i "s|tempDir: \"/tmp/.*-orchestrator\"|tempDir: \"/tmp/${REPO_NAME}-orchestrator\"|" .claude/config.yml

  echo "✅ Configuration copied!"
  echo ""
  echo "Next steps for $REPO_NAME:"
  echo "1. cd $TARGET_REPO"
  echo "2. Review .claude/config.yml (update project-specific settings)"
  echo "3. Review .claude/agents/*.md (update file paths if needed)"
  echo "4. Create custom CLAUDE.md with project rules"
  echo "5. git add .claude/ scripts/ docs/"
  echo "6. git commit -m 'feat: Add Claude Code SessionStart hooks and agent system'"
  echo "7. git push"
  echo ""
done

echo "---"
echo "✅ All repositories processed!"
echo ""
echo "Remember:"
echo "- Update .claude/config.yml in each repo (workspace tempDir, labels)"
echo "- Update agent file paths if your project structure differs"
echo "- Create project-specific CLAUDE.md with your rules"
echo "- DON'T copy WescoBar's CLAUDE.md - it's project-specific!"
