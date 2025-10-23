# Central Claude Code Configuration Repository Strategy

**Problem:** Currently Claude Code configuration is duplicated across 20+ repositories. When we update agents or skills, we need to manually sync changes.

**Solution:** Create a central "source of truth" repository that all projects can reference.

---

## Proposed Repository: `claude-code-toolkit`

**Purpose:** Universal Claude Code configuration, agents, skills, and workflows.

**URL:** `https://github.com/BerryKuipers/claude-code-toolkit`

### Repository Structure

```
claude-code-toolkit/
├── .claude/
│   ├── settings.json           # SessionStart hooks template
│   ├── config.yml              # Base configuration (customizable)
│   ├── agents/                 # Universal agents
│   │   ├── architect.md
│   │   ├── conductor.md
│   │   ├── database.md
│   │   ├── design.md
│   │   ├── refactor.md
│   │   ├── security-pentest.md
│   │   └── ...
│   ├── commands/               # Universal slash commands
│   │   ├── issue-pickup.md
│   │   ├── conductor.md
│   │   └── ...
│   └── skills/                 # Universal skills
│       ├── quality/
│       ├── testing/
│       └── ...
├── scripts/
│   ├── install-gh-cli.sh       # SessionStart hook scripts
│   ├── setup-git.sh            # Additional setup scripts
│   └── init-project.sh         # Initialize new project
├── docs/
│   ├── README.md               # Main documentation
│   ├── SETUP_GUIDE.md          # How to use in projects
│   ├── AGENTS.md               # Agent documentation
│   └── CUSTOMIZATION.md        # How to customize
├── templates/
│   ├── CLAUDE.md.template      # Project rules template
│   └── config.yml.template     # Project-specific config
└── README.md                   # Overview

```

---

## Integration Strategies

### Option 1: Git Submodule (Recommended for Web Sessions)

**Pros:**
- ✅ Single source of truth
- ✅ Easy updates (git submodule update)
- ✅ Version control (lock to specific commit)
- ✅ Works in web sessions

**Cons:**
- ⚠️ Requires submodule knowledge
- ⚠️ Extra step in setup

**Setup:**

```bash
# In your project
git submodule add https://github.com/BerryKuipers/claude-code-toolkit.git .claude-toolkit

# Symlink or copy files
ln -s .claude-toolkit/.claude .claude
cp .claude-toolkit/scripts/install-gh-cli.sh scripts/

# Commit
git add .gitmodules .claude-toolkit
git commit -m "feat: Add Claude Code toolkit as submodule"
```

**Update toolkit across all projects:**

```bash
# Pull latest toolkit changes
cd .claude-toolkit
git pull origin main

# In parent project
git add .claude-toolkit
git commit -m "chore: Update Claude Code toolkit"
```

### Option 2: Package/Template Repository

**Pros:**
- ✅ Simple to understand
- ✅ Works with GitHub template feature
- ✅ Can version as npm package (optional)

**Cons:**
- ⚠️ Manual updates per project
- ⚠️ Configuration drift

**Setup:**

```bash
# Initialize from template
gh repo create my-new-project --template BerryKuipers/claude-code-toolkit

# Or manually copy
git clone https://github.com/BerryKuipers/claude-code-toolkit.git
cp -r claude-code-toolkit/.claude my-project/
cp -r claude-code-toolkit/scripts my-project/
```

### Option 3: SessionStart Hook + Git Clone

**Pros:**
- ✅ Always up-to-date
- ✅ Automatic in web sessions
- ✅ Zero maintenance

**Cons:**
- ⚠️ Network dependency
- ⚠️ Can't lock versions
- ⚠️ Slower session start

**Setup:**

```json
// .claude/settings.json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "git clone --depth 1 https://github.com/BerryKuipers/claude-code-toolkit.git /tmp/claude-toolkit && cp -r /tmp/claude-toolkit/.claude/* \"$CLAUDE_PROJECT_DIR\"/.claude/"
          },
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/install-gh-cli.sh"
          }
        ]
      }
    ]
  }
}
```

### Option 4: Hybrid Approach (Recommended)

**Best of both worlds:**

1. **Core config in central repo** (agents, scripts, base config)
2. **Local customizations** (project-specific .claude/local/, CLAUDE.md)
3. **Automatic sync** via SessionStart hook or git submodule

**Project Structure:**

```
your-project/
├── .claude/
│   ├── settings.json         # SessionStart hooks
│   ├── local/                # Project-specific (gitignored)
│   │   ├── agents/          # Custom agents
│   │   └── config-override.yml
│   └── ...                   # Symlinks to .claude-toolkit/
├── .claude-toolkit/          # Git submodule
│   └── ...                   # Central toolkit
├── CLAUDE.md                 # Project-specific rules
└── ...
```

**.gitignore:**

```
.claude/local/
```

**Merge strategy:**

```bash
# Load central config + local overrides
# Implemented in .claude/config.yml

includes:
  - .claude-toolkit/.claude/config.yml    # Base
  - .claude/local/config-override.yml     # Project-specific
```

---

## Implementation Plan

### Phase 1: Create Central Repository

```bash
# Create new repository
gh repo create claude-code-toolkit --public --description "Universal Claude Code configuration, agents, skills, and workflows"

# Initialize with current WescoBar config
cd /tmp
gh repo clone BerryKuipers/claude-code-toolkit
cd claude-code-toolkit

# Copy universal config from WescoBar
cp -r /path/to/WescoBar/.claude .
cp -r /path/to/WescoBar/scripts .
cp -r /path/to/WescoBar/docs .

# Remove project-specific files
rm CLAUDE.md  # Project-specific rules

# Create templates
mkdir templates
cat > templates/CLAUDE.md.template <<'EOF'
# {{PROJECT_NAME}} - AI Assistant Rules

## 🎬 Project Overview

{{PROJECT_DESCRIPTION}}

**Tech Stack:**
- Frontend: {{FRONTEND}}
- Backend: {{BACKEND}}
- Database: {{DATABASE}}

## 🏗️ Architectural Rules

{{ARCHITECTURE_PATTERNS}}

## 📋 Common Commands

```bash
{{DEV_COMMAND}}    # Start development
{{BUILD_COMMAND}}  # Build for production
{{TEST_COMMAND}}   # Run tests
```
EOF

# Commit and push
git add .
git commit -m "feat: Initial Claude Code toolkit"
git push
```

### Phase 2: Migrate Existing Repositories

**Option A: Automated Migration Script**

```bash
# scripts/migrate-to-central-toolkit.sh
#!/bin/bash
for repo in TribeVibe home-sage ...; do
  cd "$repo"

  # Remove duplicated config
  rm -rf .claude/agents .claude/commands .claude/skills

  # Add toolkit as submodule
  git submodule add https://github.com/BerryKuipers/claude-code-toolkit.git .claude-toolkit

  # Symlink agents/commands/skills from toolkit
  ln -s ../.claude-toolkit/.claude/agents .claude/agents
  ln -s ../.claude-toolkit/.claude/commands .claude/commands
  ln -s ../.claude-toolkit/.claude/skills .claude/skills

  # Keep project-specific files
  mkdir -p .claude/local
  mv .claude/config.yml .claude/local/config-override.yml  # Customizations

  # Commit
  git add .gitmodules .claude-toolkit .claude
  git commit -m "refactor: Migrate to central Claude Code toolkit"
  git push
done
```

**Option B: Create PR for Each Repo**

Similar to current deployment script, but:
- Removes duplicated agents/commands
- Adds toolkit submodule
- Creates symlinks

### Phase 3: Update Workflow

**When updating agents:**

```bash
# Update central toolkit
cd claude-code-toolkit
nano .claude/agents/architect.md  # Make improvements
git commit -m "feat: Improve architect agent"
git push

# All projects using submodules get updates via:
cd your-project
git submodule update --remote .claude-toolkit
git add .claude-toolkit
git commit -m "chore: Update Claude Code toolkit"
```

**When starting new project:**

```bash
# Option 1: Template
gh repo create my-new-project --template BerryKuipers/claude-code-toolkit

# Option 2: Submodule
git init my-new-project
cd my-new-project
git submodule add https://github.com/BerryKuipers/claude-code-toolkit.git .claude-toolkit
ln -s .claude-toolkit/.claude .claude
cp .claude-toolkit/templates/CLAUDE.md.template CLAUDE.md
# Edit CLAUDE.md with project specifics
```

---

## Benefits

### For Web Sessions

✅ **Always up-to-date**: SessionStart hook pulls latest toolkit
✅ **Zero config duplication**: All projects reference same agents
✅ **Consistent experience**: Same agents across all repos
✅ **Easy customization**: Project-specific overrides in .claude/local/

### For Maintenance

✅ **Single source of truth**: Update once, applies to all
✅ **Version control**: Lock projects to specific toolkit version
✅ **Testing**: Test agent changes in toolkit before deploying
✅ **Documentation**: Centralized agent/skill documentation

### For Collaboration

✅ **Shareable**: Other developers can use same toolkit
✅ **Open source ready**: Can make toolkit public for community
✅ **Modular**: Projects pick which agents to enable

---

## Recommended Approach

**For your 20+ repos:**

1. **Create `claude-code-toolkit` repository** (central source)
2. **Use Git Submodules** for each project
3. **SessionStart hook syncs toolkit** in web sessions
4. **Local customizations** in `.claude/local/`

**Workflow:**

```bash
# One-time: Create central repo
gh repo create claude-code-toolkit --public

# For each project: Add submodule
cd TribeVibe
git submodule add https://github.com/BerryKuipers/claude-code-toolkit.git .claude-toolkit
ln -s .claude-toolkit/.claude .claude

# SessionStart hook (in .claude/settings.json)
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "git submodule update --init --remote .claude-toolkit"
      },
      {
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/install-gh-cli.sh"
      }
    ]
  }
}
```

**Updates:**

```bash
# Update toolkit once
cd claude-code-toolkit
git commit -m "feat: Improve agents"
git push

# All projects auto-update on next web session (SessionStart hook)
# Or manually: git submodule update --remote
```

---

## Next Steps

1. Create `claude-code-toolkit` repository
2. Migrate WescoBar config to toolkit
3. Update deployment script to use submodules
4. Test with 2-3 repos first (TribeVibe, home-sage)
5. Roll out to remaining repos

Want to proceed with creating the central repository?
