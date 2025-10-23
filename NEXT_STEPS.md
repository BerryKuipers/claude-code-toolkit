# Next Steps: Deploy Toolkit to Your Repositories

## 🎯 Quick Start

You're in the **claude-code-toolkit** repository - the single source of truth for Claude Code configuration across all your projects.

### Deploy to a Repository

```bash
# Deploy to one repo
./scripts/deploy-toolkit-submodule.sh <repo-name>

# Examples:
./scripts/deploy-toolkit-submodule.sh GreenSphere-
./scripts/deploy-toolkit-submodule.sh home-sage
./scripts/deploy-toolkit-submodule.sh TribeVibe
```

### Recommended Order

**1. Start with simple repos:**
- GreenSphere-
- oraculum
- MixItUp

**2. Medium complexity:**
- home-sage (has broken submodules - fix first)
- TuneScout
- SceneSpeak
- quantfolio

**3. TribeVibe last:**
- Most complex
- Has active workflows
- Deploy after perfecting approach

## 📋 What Each Deployment Does

1. Clones the target repository
2. Adds toolkit as git submodule
3. Copies sync-claude-toolkit.sh
4. Copies install-gh-cli.sh
5. Creates .claude/settings.json with SessionStart hooks
6. Updates .gitignore
7. Runs initial sync (copies agents/commands/skills)
8. Commits and pushes to feature branch
9. Provides PR creation command

## 🔧 Fix Broken Submodules First

Some repos (like home-sage) have broken submodules:

```bash
cd <repo>
git submodule deinit -f <broken-submodule>
git rm <broken-submodule>
rm -rf .git/modules/<broken-submodule>
git commit -m "chore: Remove broken submodule"
git push
```

## 📖 Documentation

- **README.md** - Quick start guide
- **docs/CROSS_PLATFORM_SUBMODULE_STRATEGY.md** - How it all works (Windows-compatible!)
- **docs/CENTRAL_REPO_STRATEGY.md** - Why this repository exists
- **docs/DEPLOY_CENTRAL_TOOLKIT.md** - Deployment guide
- **docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md** - SessionStart hooks explained
- **docs/PROJECT_CUSTOMIZATION_CHECKLIST.md** - Per-project customization

## ✅ Verify Deployment

After deploying:

```bash
cd <repo>
./scripts/sync-claude-toolkit.sh
ls .claude/agents/ | wc -l    # Should be 15
ls .claude/commands/ | wc -l  # Should be 42
ls .claude/skills/ | wc -l    # Should be 14
```

## 🎉 Expected Results

After deploying to all repos:
- ✅ Single source of truth (this toolkit)
- ✅ Update agents once → applies everywhere
- ✅ Consistent experience across projects
- ✅ Windows-compatible (Git Bash)
- ✅ 2,640 duplicate files eliminated
- ✅ 10+ hours/month maintenance saved

## 🚀 Ready to Deploy!

All scripts and documentation are ready. Start with a simple repo and work your way up!
