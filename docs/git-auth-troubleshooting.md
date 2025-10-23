# Git Authentication Troubleshooting for Claude Code

## Overview

Claude Code uses a JWT-based egress proxy architecture that affects how git operations work. This document explains the issue and provides solutions.

## The Problem

**Symptom**: Git push returns HTTP 403 Forbidden, but git fetch/clone work fine.

**Root Cause**:
- Claude Code sets up a local git proxy at `127.0.0.1:<port>/git/...`
- The `NO_PROXY` environment variable includes `127.0.0.1`, preventing proxy authentication
- The local proxy blocks write operations (push) without proper GitHub authentication
- The `GITHUB_TOKEN` environment variable exists but isn't used by git with the local proxy URL

## The Solution

Change git remote from the local proxy URL to direct HTTPS GitHub URL with token authentication:

### Automatic Fix

Run the configuration script:

```bash
.claude-toolkit/hooks/configure-git-auth.sh
```

This script:
1. Detects if you're using the local proxy URL
2. Switches to HTTPS GitHub URL
3. Configures git to use GITHUB_TOKEN for authentication
4. Tests connectivity

### Manual Fix

If you need to configure manually:

1. **Change remote URL**:
   ```bash
   git remote set-url origin https://github.com/USER/REPO.git
   ```

2. **Configure token authentication**:
   ```bash
   git config --global credential.helper store
   git config --global url."https://${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"
   ```

3. **Test**:
   ```bash
   git push -u origin BRANCH_NAME
   ```

## How It Works

### Claude Code Proxy Architecture

Claude Code uses two proxy systems:

1. **External Proxy** (`21.0.0.55:15004`):
   - JWT-based authentication
   - Used for general internet access
   - Has an `allowed_hosts` whitelist including GitHub

2. **Local Git Proxy** (`127.0.0.1:<port>`):
   - Routes git operations through the external proxy
   - Has limitations on write operations
   - Not always compatible with token authentication

### URL Rewriting

The configuration sets up URL rewriting in `~/.gitconfig`:

```ini
[url "https://GITHUB_TOKEN@github.com/"]
    insteadOf = https://github.com/
```

This automatically injects the token into all GitHub URLs, enabling push operations.

## Environment Variables

Relevant environment variables in Claude Code:

- `GITHUB_TOKEN`: GitHub Personal Access Token (automatically provided)
- `HTTP_PROXY`: External proxy with JWT authentication
- `HTTPS_PROXY`: Same as HTTP_PROXY
- `NO_PROXY`: Localhost addresses that bypass proxy
- `CCR_TEST_GITPROXY`: Flag indicating git proxy test mode

## Verification

To verify your configuration is working:

1. **Check remote URL**:
   ```bash
   git remote get-url origin
   # Should show: https://github.com/USER/REPO.git
   ```

2. **Check git config**:
   ```bash
   git config --get url."https://${GITHUB_TOKEN}@github.com/".insteadOf
   # Should show: https://github.com/
   ```

3. **Test connectivity**:
   ```bash
   git ls-remote origin HEAD
   # Should list the HEAD reference without errors
   ```

4. **Test push**:
   ```bash
   git push -u origin BRANCH_NAME
   # Should succeed without 403 error
   ```

## GitHub CLI (gh)

The `gh` CLI works differently and uses the GitHub API directly:

- Authentication: Uses `GITHUB_TOKEN` environment variable automatically
- Network: Goes through the HTTP_PROXY (not the local git proxy)
- Operations: API-based, not git-protocol based

### Using gh CLI

The gh CLI should work without additional configuration:

```bash
# List issues
/root/.local/bin/gh issue list

# Create PR
/root/.local/bin/gh pr create --title "Title" --body "Body"

# View PR
/root/.local/bin/gh pr view 123
```

## Security Considerations

### Token Exposure

The git configuration stores the GitHub token in `~/.gitconfig`:

```ini
[url "https://github_pat_XXXXX@github.com/"]
    insteadOf = https://github.com/
```

**This is secure in Claude Code** because:
- The file is in the ephemeral sandbox environment
- It's not committed to the repository
- It's automatically cleaned up when the session ends

**Do NOT**:
- Commit `~/.gitconfig` to version control
- Share your `~/.gitconfig` file
- Copy this configuration to persistent systems without modification

### Alternative: Credential Helper

For persistent systems, use a credential helper instead:

```bash
git config --global credential.helper 'cache --timeout=3600'
```

This stores credentials in memory temporarily instead of in a file.

## Troubleshooting

### Push still returns 403

1. **Check token validity**:
   ```bash
   echo $GITHUB_TOKEN
   # Should show a token starting with ghp_ or github_pat_
   ```

2. **Check token permissions**:
   - The token needs `repo` scope for private repositories
   - The token needs `public_repo` scope for public repositories

3. **Check remote URL**:
   ```bash
   git remote -v
   # Should show HTTPS URLs, not local proxy URLs
   ```

4. **Re-run configuration**:
   ```bash
   .claude-toolkit/hooks/configure-git-auth.sh
   ```

### gh CLI doesn't work

1. **Check gh installation**:
   ```bash
   /root/.local/bin/gh --version
   ```

2. **Check authentication**:
   ```bash
   echo $GITHUB_TOKEN | /root/.local/bin/gh auth login --with-token
   ```

3. **Check proxy**:
   ```bash
   echo $HTTPS_PROXY
   # Should show the external proxy URL
   ```

### Remote changed back to local proxy

This can happen if:
- The repository was re-cloned
- Git operations reset the configuration

**Solution**: Add the configuration script to the toolkit's SessionStart hook:

```bash
# In .claude-toolkit/hooks/SessionStart
./configure-git-auth.sh
```

## Session Persistence

The configuration needs to be reapplied in each new Claude Code session because:
- The sandbox environment is ephemeral
- Git configuration is not persisted between sessions
- The GITHUB_TOKEN may change between sessions

### Auto-Configuration

To automatically configure git in each session, add to `.claude-toolkit/hooks/SessionStart`:

```bash
#!/bin/bash
# Auto-configure git authentication on session start

if [ -f ".claude-toolkit/hooks/configure-git-auth.sh" ]; then
    .claude-toolkit/hooks/configure-git-auth.sh
fi
```

## References

- [Git Configuration Documentation](https://git-scm.com/docs/git-config)
- [GitHub Token Authentication](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [Git Credential Helpers](https://git-scm.com/docs/gitcredentials)
- [GitHub CLI Documentation](https://cli.github.com/manual/)

## Summary

**Problem**: Claude Code's local git proxy blocks write operations

**Solution**: Use HTTPS GitHub URLs with GITHUB_TOKEN authentication

**Implementation**: Run `.claude-toolkit/hooks/configure-git-auth.sh`

**Verification**: Test with `git push`

**Persistence**: Add to SessionStart hook for auto-configuration
