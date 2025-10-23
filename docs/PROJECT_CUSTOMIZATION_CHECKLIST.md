# Claude Code Configuration - Project Customization Checklist

**This Claude Code configuration was automatically deployed from WescoBar-Universe-Storyteller.**

Before using, please customize for your project:

---

## ✅ Required Customizations

### 1. Update `.claude/config.yml`

**Lines to change:**

```yaml
# Line ~200: Update workspace directory with your project name
workspace:
  tempDir: "/tmp/YOUR-PROJECT-NAME-orchestrator"  # Change this!

# Lines ~154-159: Update GitHub labels for your project
integrations:
  github:
    enabled: true
    defaultLabels:
      - "automated"
      - "your-label-here"  # Add project-specific labels
```

### 2. Review Agent File Paths

**Agents reference specific file structures. Update if your project differs:**

**`.claude/agents/architect.md`** - Architecture review agent
- Search for: `src/components/`, `backend/`, `package.json`
- Update to: Your actual source paths

**`.claude/agents/database.md`** - Database operations agent
- Search for: `backend/DATABASE.md`, `PostgreSQL`
- Update to: Your database type and schema location

**`.claude/agents/design.md`** - UI/UX design agent
- Search for: `src/components/`, `React`
- Update to: Your UI framework and component paths

**`.claude/agents/refactor.md`** - Safe refactoring agent
- Search for: `npm run build`, `npm run test`
- Update to: Your build and test commands

### 3. Create `CLAUDE.md` (Optional but Recommended)

**DO NOT copy WescoBar's CLAUDE.md** - it's project-specific!

Create your own with:

```markdown
# [Your Project Name] - AI Assistant Rules

## 🎬 Project Overview

[Your project description]

**Tech Stack:**
- Frontend: [Your frontend stack]
- Backend: [Your backend stack]
- Database: [Your database]
- Testing: [Your test framework]

## 🏗️ Architectural Rules

[Your architecture patterns]

## 📂 Project Structure

```
your-project/
├── src/           # [What's here]
├── tests/         # [Test structure]
├── docs/          # [Documentation]
└── ...
```

## 📋 Common Commands

```bash
npm run dev       # [How to start dev server]
npm run build     # [How to build]
npm run test      # [How to run tests]
```

## 🚫 FORBIDDEN COMMANDS

[Any project-specific restrictions]
```

---

## 🟡 Optional Customizations

### 4. Update Tech Stack References

**If your project uses different tech:**

| WescoBar Uses | Your Project Uses | Files to Update |
|---------------|-------------------|-----------------|
| React 19 | Angular/Vue/Blazor | All agent `.md` files |
| Vite | Webpack/Parcel | `.claude/agents/refactor.md` |
| PostgreSQL | MongoDB/MySQL | `.claude/agents/database.md` |
| Vitest | Jest/Mocha | `.claude/agents/refactor.md` |
| TypeScript | JavaScript/C#/Python | All agent files |

**Find and replace in `.claude/agents/`:**

```bash
# Example: Replace React references
cd .claude/agents
grep -r "React" .  # Find all React references
# Manually update to your framework
```

### 5. Customize Validation Thresholds

**In `.claude/config.yml`:**

```yaml
validation:
  requireTestsBeforeRefactor: true
  requireBuildValidation: true
  requireCoverageThreshold: 80  # Adjust to your project's standard
```

### 6. Add Project-Specific Agents (Advanced)

**If you need custom agents:**

```bash
# Create new agent
nano .claude/agents/your-custom-agent.md
```

Follow the structure in existing agents.

### 7. Add Project-Specific Skills (Advanced)

**If you have custom build/test workflows:**

```bash
# CLI skills (local only)
mkdir -p .claude/skills/your-skill/
nano .claude/skills/your-skill/SKILL.md

# API skills (works in web sessions)
mkdir -p .claude/api-skills-source/your-skill/
nano .claude/api-skills-source/your-skill/SKILL.md
```

---

## 🧪 Testing the Configuration

### Step 1: Test in Claude Code Web Session

```bash
# Start new Claude Code session
# Hook should auto-install gh CLI

# Verify
gh --version  # Should show gh CLI version
```

### Step 2: Test an Agent

Use Task tool to invoke an agent:

```
Task({
  subagent_type: "architect",
  prompt: "Review the current project architecture"
})
```

### Step 3: Verify Paths

Check that agents aren't erroring on missing paths:

```bash
# Make sure these exist in your project
ls src/components/     # Or your component path
ls backend/           # Or your backend path
npm run build         # Or your build command
npm run test          # Or your test command
```

---

## 📝 Quick Start Checklist

**Before merging this PR:**

- [ ] Updated `.claude/config.yml` workspace directory
- [ ] Updated GitHub labels in `.claude/config.yml`
- [ ] Reviewed `.claude/agents/architect.md` - paths are correct
- [ ] Reviewed `.claude/agents/database.md` - database type matches
- [ ] Reviewed `.claude/agents/design.md` - UI framework matches
- [ ] Reviewed `.claude/agents/refactor.md` - build/test commands correct
- [ ] Created custom `CLAUDE.md` with project rules (optional)
- [ ] Tested in Claude Code session - gh CLI installs
- [ ] Tested an agent - no path errors

**After merging:**

- [ ] Start new Claude Code web session
- [ ] Verify `gh --version` works
- [ ] Test architect agent: Task({ subagent_type: "architect", ... })
- [ ] Test conductor workflow if needed

---

## 🆘 Troubleshooting

### gh CLI Not Installing

```bash
# Check hook configuration
cat .claude/settings.json

# Test script manually
./scripts/install-gh-cli.sh

# Check domain allowlist includes:
# - release-assets.githubusercontent.com
```

### Agents Failing on Paths

```bash
# Find path references
grep -r "src/components" .claude/agents/
grep -r "backend/" .claude/agents/
grep -r "npm run" .claude/agents/

# Update to match your project structure
```

### Build/Test Commands Wrong

```bash
# Update in refactor agent
nano .claude/agents/refactor.md

# Search for: npm run build
# Replace with: your build command
```

---

## 📚 Documentation

See these files for more details:

- `docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md` - Complete setup guide
- `docs/COPY_TO_NEW_REPO.md` - How configuration was copied
- `.claude/agents/` - Individual agent documentation

---

## 🚀 Ready to Use?

Once you've completed the checklist:

1. Merge this PR
2. Start a new Claude Code web session
3. The SessionStart hook will auto-install gh CLI
4. Agents will be available via Task tool
5. Enjoy automated workflows!

**Questions?** Check `docs/CLAUDE_CODE_WEB_SETUP_GUIDE.md` or open an issue.
