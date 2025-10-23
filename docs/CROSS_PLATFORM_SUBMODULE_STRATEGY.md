# Cross-Platform Claude Code Toolkit Integration

**Windows-Compatible Strategy for Git Submodules**

---

## ✅ Problem Solved

**Challenge:** Symlinks don't work on Windows

**Solution:** Sync files on SessionStart using cross-platform script

---

## 🎯 How It Works

### 1. Toolkit as Submodule

```bash
# Add toolkit to your project
git submodule add https://github.com/BerryKuipers/claude-code-toolkit.git .claude-toolkit
```

### 2. Sync Script (Cross-Platform)

**`scripts/sync-claude-toolkit.sh`** - Works on:
- ✅ Windows (via Git Bash)
- ✅ Linux
- ✅ Mac

**What it does:**
1. Updates submodule from GitHub (`git submodule update`)
2. Syncs agents/commands/skills from `.claude-toolkit/.claude/` to `.claude/`
3. Preserves project-specific files (settings.json, config.yml)
4. Uses `rsync` if available, falls back to `cp`

### 3. SessionStart Hook

**`.claude/settings.json`:**
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/sync-claude-toolkit.sh"
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

**Execution Order:**
1. Session starts
2. Sync toolkit (pull updates, copy files)
3. Install gh CLI
4. Ready to work!

---

## 📂 Directory Structure

```
your-project/
├── .claude-toolkit/        # Git submodule (read-only)
│   └── .claude/
│       ├── agents/         # 15 universal agents
│       ├── commands/       # 42 slash commands
│       ├── skills/         # 14 skills
│       └── config.yml      # Base configuration
├── .claude/                # Project files (gitignored duplicates)
│   ├── agents/            # Synced from toolkit
│   ├── commands/          # Synced from toolkit
│   ├── skills/            # Synced from toolkit
│   ├── settings.json      # PROJECT-SPECIFIC (kept)
│   ├── config.yml         # PROJECT-SPECIFIC (kept)
│   └── local/             # Project overrides (optional)
├── scripts/
│   ├── sync-claude-toolkit.sh    # Sync script
│   └── install-gh-cli.sh          # gh CLI installer
├── .gitmodules            # Submodule config
└── CLAUDE.md              # Project rules (optional)
```

---

## 🔄 Update Workflow

### Toolkit Maintainer Updates Agents

```bash
# In claude-code-toolkit repo
cd claude-code-toolkit
nano .claude/agents/architect.md  # Improve agent
git commit -m "feat: Better architecture detection"
git push
```

### Projects Get Updates Automatically

**On next session start:**
1. SessionStart hook runs
2. `sync-claude-toolkit.sh` executes
3. `git submodule update --remote` pulls latest
4. Files synced to `.claude/`
5. New agent version ready!

**Manual update:**
```bash
cd your-project
./scripts/sync-claude-toolkit.sh
```

---

## ⚙️ .gitignore Configuration

**Add to `.gitignore`:**
```
# Claude toolkit synced files (don't commit duplicates)
.claude/agents/
.claude/commands/
.claude/skills/
.claude/api-skills-source/

# Keep project-specific
!.claude/settings.json
!.claude/config.yml
!.claude/local/
```

This ensures:
- ✅ Submodule reference tracked (`.claude-toolkit`)
- ✅ Project-specific files tracked (settings.json)
- ❌ Synced duplicates not tracked

---

## 🧪 Testing

### Test Sync Manually

```bash
cd your-project
./scripts/sync-claude-toolkit.sh
```

**Expected output:**
```
🔄 Syncing Claude Code Toolkit...
  → Updating toolkit submodule...
  → Syncing agents...
  → Syncing commands...
  → Syncing skills...
  → Syncing API skills...
  → Preserving project-specific files (settings.json, config.yml)
✅ Toolkit synced successfully!
```

### Verify Files

```bash
ls -la .claude/agents/    # Should have 15 agents
ls -la .claude/commands/  # Should have 42 commands
ls -la .claude/skills/    # Should have 14 skills
```

### Test SessionStart Hook

Start new Claude Code session - sync should run automatically.

---

## 🪟 Windows Compatibility

### Git Bash Required

Windows users need Git Bash installed (comes with Git for Windows).

**Verify:**
```bash
# In Git Bash
bash --version
```

### Why It Works on Windows

1. **No symlinks** - Uses file copy instead
2. **Git Bash** - Provides Unix-like shell on Windows
3. **Portable paths** - Script uses `$CLAUDE_PROJECT_DIR` variable
4. **Fallback logic** - Uses `cp` if `rsync` not available

### Alternative: Windows PowerShell Version

If needed, create `sync-claude-toolkit.ps1`:

```powershell
# PowerShell version of sync script
$ToolkitDir = "$env:CLAUDE_PROJECT_DIR\.claude-toolkit\.claude"
$TargetDir = "$env:CLAUDE_PROJECT_DIR\.claude"

Write-Host "🔄 Syncing Claude Code Toolkit..."

# Update submodule
git submodule update --init --remote .claude-toolkit

# Sync files
Copy-Item "$ToolkitDir\agents" "$TargetDir" -Recurse -Force
Copy-Item "$ToolkitDir\commands" "$TargetDir" -Recurse -Force
Copy-Item "$ToolkitDir\skills" "$TargetDir" -Recurse -Force

Write-Host "✅ Toolkit synced successfully!"
```

---

## 🚀 Deployment to New Repos

### Step 1: Add Submodule

```bash
cd your-project
git submodule add https://github.com/BerryKuipers/claude-code-toolkit.git .claude-toolkit
```

### Step 2: Copy Scripts

```bash
mkdir -p scripts
cp .claude-toolkit/scripts/sync-claude-toolkit.sh scripts/
cp .claude-toolkit/scripts/install-gh-cli.sh scripts/
chmod +x scripts/*.sh
```

### Step 3: Update Settings

Create `.claude/settings.json`:
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/scripts/sync-claude-toolkit.sh"
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

### Step 4: Initial Sync

```bash
./scripts/sync-claude-toolkit.sh
```

### Step 5: Configure .gitignore

```bash
echo ".claude/agents/" >> .gitignore
echo ".claude/commands/" >> .gitignore
echo ".claude/skills/" >> .gitignore
echo ".claude/api-skills-source/" >> .gitignore
```

### Step 6: Commit

```bash
git add .claude-toolkit .gitmodules scripts/ .claude/settings.json .gitignore
git commit -m "feat: Add Claude Code toolkit via submodule"
git push
```

---

## 📋 Benefits vs Symlinks

| Feature | Symlinks | File Copy (Our Approach) |
|---------|----------|--------------------------|
| Windows Support | ❌ Requires admin | ✅ Works everywhere |
| Auto-sync | ❌ Manual | ✅ SessionStart hook |
| Git tracking | ✅ Simple | ✅ via .gitignore |
| Offline work | ✅ Always available | ✅ Files are local |
| Updates | ✅ Instant | ✅ On session start |
| Cross-platform | ❌ Linux/Mac only | ✅ Linux/Mac/Windows |

---

## ✅ Verified Working

**Tested On:**
- ✅ WescoBar-Universe-Storyteller (this repo)
- ✅ Linux (Claude Code web session)
- ⏳ Windows (to be tested locally)
- ⏳ Mac (to be tested locally)

**Files Synced:**
- ✅ 15 agents
- ✅ 42 commands
- ✅ 14 skills
- ✅ API skills source

**SessionStart Hook:**
- ✅ Sync before gh CLI install
- ✅ Toolkit updates pulled
- ✅ Project files preserved

---

## 🆘 Troubleshooting

### Sync Script Fails

**Check submodule:**
```bash
git submodule status
git submodule init
git submodule update
```

### Files Not Syncing

**Check toolkit exists:**
```bash
ls .claude-toolkit/.claude/agents/
```

**Run sync manually:**
```bash
bash -x ./scripts/sync-claude-toolkit.sh  # Debug output
```

### Windows: "command not found"

**Solution:** Use Git Bash, not CMD/PowerShell

**Or:** Create PowerShell version (see above)

---

## 🎉 Success!

WescoBar now uses the central toolkit!

**Next:** Deploy to remaining 19 repos using same approach.

**Command:**
```bash
./scripts/deploy-claude-config-to-github-repos.sh  # Updated to use submodules
```
