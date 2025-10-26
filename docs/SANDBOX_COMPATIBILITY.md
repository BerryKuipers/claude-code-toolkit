# Claude Code Sandbox Compatibility

**Issue**: Toolkit submodule sync and gh CLI fail with proxy 403 errors when Claude Code sandbox is enabled.

## Root Cause

Claude Code's network sandboxing blocks GitHub access by default:

1. **SessionStart hooks run**: `git submodule update --init --remote .claude-toolkit`
2. **Network sandbox blocks**: github.com connection → **403 Forbidden**
3. **gh CLI also blocked**: API calls to api.github.com → **403 Forbidden**

## Solutions

### Solution 1: Allow GitHub Domains (Recommended)

Add GitHub to your sandbox network allowlist in `settings.json`:

```json
{
  "sandbox": {
    "enabled": true,
    "allowedDomains": [
      "github.com",
      "api.github.com",
      "raw.githubusercontent.com",
      "objects.githubusercontent.com",
      "codeload.github.com"
    ]
  }
}
```

**Pros:**
- Maintains sandbox security for other operations
- Allows toolkit sync and gh CLI to work
- One-time configuration

**Cons:**
- Broad github.com access (potential data exfiltration risk per docs)
- Must manually add each GitHub domain as needed

### Solution 2: Exclude Commands from Sandbox

Exclude git and gh from sandbox entirely:

```json
{
  "sandbox": {
    "enabled": true,
    "excludedCommands": [
      "git",
      "gh"
    ]
  }
}
```

**Pros:**
- Simple configuration
- Git and gh work normally
- No domain management needed

**Cons:**
- Git and gh run outside sandbox (less isolation)
- Could be exploited if repository is malicious

### Solution 3: Disable Sandbox for Development

Disable sandbox temporarily during toolkit setup:

```json
{
  "sandbox": {
    "enabled": false
  }
}
```

**Pros:**
- No restrictions
- Everything works immediately

**Cons:**
- No sandbox protection at all
- Not recommended for production use

### Solution 4: Manual Submodule Init (Workaround)

Remove submodule init from SessionStart hooks and initialize manually:

```bash
# Run once after cloning
git submodule update --init --remote .claude-toolkit

# Then SessionStart hooks work (submodule already exists)
```

**Pros:**
- One-time manual step
- Subsequent syncs work (no network needed for local sync)

**Cons:**
- Requires manual intervention on fresh clone
- Easy to forget

## Recommended Configuration

For most users, **Solution 1** (allow GitHub domains) provides the best balance:

```json
{
  "sandbox": {
    "enabled": true,
    "allowedDomains": [
      "github.com",
      "api.github.com",
      "raw.githubusercontent.com",
      "objects.githubusercontent.com",
      "codeload.github.com"
    ],
    "excludedCommands": []
  },
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "git submodule update --init --remote .claude-toolkit"
          },
          {
            "type": "command",
            "command": "bash .claude-toolkit/scripts/sync-claude-toolkit.sh"
          },
          {
            "type": "command",
            "command": "bash .claude-toolkit/scripts/install-gh-cli.sh"
          }
        ]
      }
    ]
  }
}
```

## Security Considerations

⚠️ **Warning from Claude Code docs:**
> Users should be aware of potential risks that come from allowing broad domains like `github.com` that may allow for data exfiltration.

### Mitigation Strategies

1. **Trust your repositories**: Only work on repos you control/trust
2. **Review submodules**: Check .gitmodules for unexpected URLs
3. **Monitor network requests**: Watch for unusual GitHub activity
4. **Use narrow permissions**: Only add domains as needed
5. **Combine with filesystem isolation**: Sandbox still protects filesystem

### Domain Fronting Risk

GitHub domains could potentially be exploited via [domain fronting](https://en.wikipedia.org/wiki/Domain_fronting) to bypass network restrictions. This is a theoretical risk but worth noting.

## Troubleshooting

### Error: "fatal: unable to access 'https://github.com/...': Received HTTP code 403 from proxy"

**Cause**: Network sandbox is blocking GitHub

**Fix**: Add GitHub domains to `allowedDomains` (Solution 1)

### Error: "git: command not found" (inside sandbox)

**Cause**: Git not available in sandbox environment

**Fix**: Add `"git"` to `excludedCommands` (Solution 2)

### Error: "gh: command not found"

**Cause**: gh CLI not installed or not in PATH within sandbox

**Fix 1**: Run install-gh-cli.sh outside SessionStart
**Fix 2**: Add `"gh"` to `excludedCommands`

### SessionStart hooks fail silently

**Cause**: Hooks run before user can approve network requests

**Fix**: Pre-configure `allowedDomains` in settings.json before starting session

## Testing Your Configuration

After configuring sandbox settings:

```bash
# Test 1: Submodule update works
git submodule update --init --remote .claude-toolkit
# Should succeed without 403 error

# Test 2: Sync script works
bash .claude-toolkit/scripts/sync-claude-toolkit.sh
# Should complete successfully

# Test 3: gh CLI works
gh auth status
# Should show authentication status
```

## Enterprise Considerations

For organizations deploying toolkit across multiple repos:

### Managed Settings

Use [managed settings](https://docs.claude.com/en/docs/claude-code/settings#settings-precedence) to enforce consistent sandbox configuration:

```json
// managed-settings.json (pushed to all developers)
{
  "sandbox": {
    "enabled": true,
    "allowedDomains": [
      "github.com",
      "api.github.com",
      "raw.githubusercontent.com",
      "objects.githubusercontent.com",
      "codeload.github.com",
      "your-internal-domain.com"  // Add internal resources
    ],
    "excludedCommands": []
  }
}
```

### Custom Proxy (Advanced)

For organizations requiring traffic inspection:

```json
{
  "sandbox": {
    "httpProxyPort": 8080,
    "socksProxyPort": 8081,
    "allowedDomains": ["*"]  // Proxy handles filtering
  }
}
```

Then run your own proxy server that:
- Decrypts and inspects HTTPS traffic
- Applies custom filtering rules
- Logs all network requests
- Integrates with security infrastructure

## Alternative: Devcontainers

For complete isolation, use [devcontainers](https://docs.claude.com/en/docs/claude-code/devcontainer) instead:

```json
// .devcontainer/devcontainer.json
{
  "name": "Project with Toolkit",
  "image": "mcr.microsoft.com/devcontainers/base:ubuntu",
  "postCreateCommand": "git submodule update --init",
  "customizations": {
    "claude": {
      "settings": {
        // Sandbox settings here
      }
    }
  }
}
```

## Documentation Updates Needed

### In deployment script comments:

```bash
#!/bin/bash
# Deploy Claude Code Toolkit as Submodule
#
# IMPORTANT: If using Claude Code sandbox, you must allow GitHub domains:
# See: .claude-toolkit/docs/SANDBOX_COMPATIBILITY.md
#
# Quick fix - Add to your settings.json:
#   "sandbox": {
#     "allowedDomains": ["github.com", "api.github.com", "raw.githubusercontent.com"]
#   }
```

### In toolkit README:

```markdown
## Requirements

- Git
- Bash (Windows: Git Bash)
- GitHub CLI (gh) - installed automatically
- **Claude Code sandbox**: Must allow GitHub domains (see SANDBOX_COMPATIBILITY.md)
```

## Summary

**Problem**: Sandbox blocks GitHub → 403 errors
**Solution**: Allow GitHub domains in sandbox settings
**Alternative**: Exclude git/gh from sandbox
**Best practice**: Solution 1 (allowlist) for security + functionality balance

## See Also

- [Claude Code Sandbox Documentation](https://docs.claude.com/en/docs/claude-code/sandboxing)
- [Settings Reference](https://docs.claude.com/en/docs/claude-code/settings)
- [Toolkit Deployment Script](../scripts/deploy-toolkit-submodule.sh)
