# Claude Code Toolkit - Documentation

## Quick Links

### Getting Started
- [Cross-Platform Submodule Strategy](CROSS_PLATFORM_SUBMODULE_STRATEGY.md) - How the toolkit works as a git submodule
- [Sandbox Compatibility](SANDBOX_COMPATIBILITY.md) - **IMPORTANT**: Fix 403 errors with Claude Code sandbox

### Architecture & Design
- [Toolkit Modernization 2025](TOOLKIT_MODERNIZATION_2025.md) - Architecture decisions, hooks vs agents vs CI/CD

### Configuration Examples
- [Settings with Sandbox](settings-examples/settings-with-sandbox.json) - Recommended settings.json with GitHub domain allowlist

## Common Issues

### 403 Forbidden / Proxy Errors

**Symptom**: SessionStart hooks fail with "403 Forbidden from proxy"

**Cause**: Claude Code sandbox blocking GitHub access

**Fix**: See [SANDBOX_COMPATIBILITY.md](SANDBOX_COMPATIBILITY.md)

**Quick solution:**
```json
// Add to .claude/settings.json
{
  "sandbox": {
    "allowedDomains": ["github.com", "api.github.com", "raw.githubusercontent.com"]
  }
}
```

### Submodule Not Initializing

**Symptom**: .claude-toolkit directory is empty after clone

**Cause**: Submodule not initialized

**Fix**:
```bash
git submodule update --init --remote .claude-toolkit
```

Or ensure SessionStart hooks are configured (deployment script does this automatically).

### Settings.json Won't Stage

**Symptom**: `git add .claude/settings.json` ignored

**Cause**: Blanket `.claude/` in .gitignore

**Fix**: Deployment script now automatically removes blanket `.claude/` ignore

### Script Not Found in SessionStart

**Symptom**: "No such file or directory: .claude-toolkit/scripts/sync-claude-toolkit.sh"

**Cause**: Chicken-and-egg problem - scripts don't exist until submodule initialized

**Fix**: Deployment script now adds `git submodule update --init` as FIRST hook

## Documentation Index

### Core Documentation

| Document | Description |
|----------|-------------|
| [CROSS_PLATFORM_SUBMODULE_STRATEGY.md](CROSS_PLATFORM_SUBMODULE_STRATEGY.md) | How toolkit works as submodule, sync strategy |
| [SANDBOX_COMPATIBILITY.md](SANDBOX_COMPATIBILITY.md) | **Critical**: Sandbox configuration for GitHub access |
| [TOOLKIT_MODERNIZATION_2025.md](TOOLKIT_MODERNIZATION_2025.md) | Architecture analysis, hooks vs agents |

### Examples

| File | Description |
|------|-------------|
| [settings-with-sandbox.json](settings-examples/settings-with-sandbox.json) | Complete settings.json with sandbox config |

### Scripts

| Script | Purpose |
|--------|---------|
| [deploy-toolkit-submodule.sh](../scripts/deploy-toolkit-submodule.sh) | Deploy toolkit to target repo |
| [sync-claude-toolkit.sh](../scripts/sync-claude-toolkit.sh) | Sync toolkit files (runs on SessionStart) |
| [install-gh-cli.sh](../scripts/install-gh-cli.sh) | Install GitHub CLI without root |

### Prompts

| Prompt | Category | Purpose |
|--------|----------|---------|
| [issue-selection.md](../.claude/prompts/workflows/issue-selection.md) | Workflow | Pick best GitHub issue with scoring |
| [pr-review-response.md](../.claude/prompts/workflows/pr-review-response.md) | Workflow | Respond to PR reviews (incl. Gemini AI) |
| [conductor-full-cycle.md](../.claude/prompts/workflows/conductor-full-cycle.md) | Workflow | Complete issue→PR→merge workflow |
| [parallel-agents.md](../.claude/prompts/coordination/parallel-agents.md) | Coordination | Coordinate parallel agent execution |

## Toolkit Structure

```
claude-code-toolkit/
├── .claude/
│   ├── agents/              # 18 specialized agents (synced to projects)
│   ├── commands/            # 43 slash commands (synced to projects)
│   ├── skills/              # 14 reusable skills (synced to projects)
│   ├── prompts/             # Workflow prompts (synced, not ignored)
│   │   ├── workflows/       # End-to-end workflows
│   │   ├── coordination/    # Multi-agent coordination
│   │   ├── analysis/        # Investigation frameworks
│   │   └── templates/       # Reusable templates
│   └── api-skills-source/   # API skills (synced to projects)
├── scripts/
│   ├── deploy-toolkit-submodule.sh   # Deploy to repos
│   ├── sync-claude-toolkit.sh        # Sync on SessionStart
│   └── install-gh-cli.sh             # Install gh CLI
└── docs/
    ├── README.md (this file)
    ├── SANDBOX_COMPATIBILITY.md      # **READ THIS FIRST**
    ├── CROSS_PLATFORM_SUBMODULE_STRATEGY.md
    ├── TOOLKIT_MODERNIZATION_2025.md
    └── settings-examples/
        └── settings-with-sandbox.json
```

## Deployment Workflow

### 1. Deploy Toolkit to Repo

```bash
./scripts/deploy-toolkit-submodule.sh my-repo
```

This creates:
- Git submodule at `.claude-toolkit/`
- SessionStart hooks in `.claude/settings.json`
- Sync script at `scripts/sync-claude-toolkit.sh`
- PR with changes

### 2. Configure Sandbox (If Enabled)

**Critical**: If Claude Code sandbox is enabled, add GitHub domains:

```json
// .claude/settings.json
{
  "sandbox": {
    "allowedDomains": [
      "github.com",
      "api.github.com",
      "raw.githubusercontent.com"
    ]
  },
  "hooks": {
    // ... SessionStart hooks ...
  }
}
```

See [SANDBOX_COMPATIBILITY.md](SANDBOX_COMPATIBILITY.md) for details.

### 3. Merge PR

After review, merge the PR. The toolkit is now active!

### 4. On SessionStart (Automatic)

Every time you start a Claude Code session:

```bash
# Runs automatically via SessionStart hooks:
1. git submodule update --init --remote .claude-toolkit
2. bash .claude-toolkit/scripts/sync-claude-toolkit.sh
3. bash .claude-toolkit/scripts/install-gh-cli.sh

# Results:
✅ Toolkit synced to .claude/
✅ 18 agents available
✅ 43 commands available
✅ 14 skills available
✅ Workflow prompts available
✅ gh CLI installed
```

## Usage Examples

### Use Workflow Prompts

```markdown
"Use issue-selection prompt to analyze these GitHub issues and recommend the best one.

Repository: my-repo
Available time: 4 hours
Issues: [paste gh issue list]"
```

### Conductor Full-Cycle

```markdown
"Use conductor full-cycle workflow to pick and implement the best GitHub issue end-to-end."
```

### Parallel Implementation

```markdown
"Use parallel-agents prompt to implement user preferences across frontend, backend, and database."
```

### PR Review Response

```markdown
"Check PR #45 and use pr-review-response prompt to analyze all comments including Gemini AI feedback."
```

## Troubleshooting

### Issue: 403 Forbidden Errors

**Solution**: [SANDBOX_COMPATIBILITY.md](SANDBOX_COMPATIBILITY.md)

### Issue: Hooks Not Running

Check:
1. `.claude/settings.json` has SessionStart hooks
2. Hooks are syntactically valid JSON
3. Sandbox allows GitHub domains (if enabled)
4. Submodule exists: `ls .claude-toolkit/`

### Issue: Agents/Commands Not Found

Check:
1. Sync ran: `bash scripts/sync-claude-toolkit.sh`
2. Files exist: `ls .claude/agents/`
3. No .gitignore blocking: `cat .gitignore | grep .claude`

### Issue: Can't Stage .claude/settings.json

**Cause**: Blanket `.claude/` in .gitignore

**Fix**: Remove with: `sed -i '/^\.claude\/$/d' .gitignore`

(Deployment script does this automatically)

## Best Practices

### For Repository Maintainers

1. **Configure sandbox first**: Add GitHub domains before merging toolkit
2. **Test SessionStart hooks**: Verify they work after deployment
3. **Document custom prompts**: If you customize prompts per project
4. **Keep toolkit updated**: `cd .claude-toolkit && git pull`

### For Toolkit Contributors

1. **Test cross-platform**: Verify on Linux, Mac, Windows (Git Bash)
2. **Update documentation**: Keep docs in sync with changes
3. **Version prompts**: Significant prompt changes should be documented
4. **Test sandbox compatibility**: Ensure new features work with sandbox

## Contributing

To contribute to the toolkit:

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test in multiple repos
5. Update documentation
6. Create PR

## Support

For issues:
- Check [SANDBOX_COMPATIBILITY.md](SANDBOX_COMPATIBILITY.md) first
- Review troubleshooting section above
- Check GitHub issues
- Create new issue with details

## License

[Add license information]

## See Also

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [Claude Code Sandbox](https://docs.claude.com/en/docs/claude-code/sandboxing)
- [Settings Reference](https://docs.claude.com/en/docs/claude-code/settings)
