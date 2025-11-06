# MCP Broker Setup Guide

This guide covers setting up the MCP Broker for **portable use** on any system, whether globally or per-project.

---

## Quick Start

### 1. Clone the Toolkit

Choose where you want the toolkit (examples shown for common locations):

**Option A: Global location (recommended)**
```bash
# Linux/Mac
cd ~/.config/claude/
git clone https://github.com/BerryKuipers/claude-code-toolkit.git toolkit

# Windows
cd C:\Users\YourUsername\.claude\
git clone https://github.com/BerryKuipers/claude-code-toolkit.git toolkit
```

**Option B: Projects directory**
```bash
cd ~/Projects  # or wherever you keep projects
git clone https://github.com/BerryKuipers/claude-code-toolkit.git
```

### 2. Build the Broker

```bash
cd claude-code-toolkit/submodules/mcp-broker
npm install
npm run build
```

### 3. Configure Your MCP Servers

```bash
# Copy sample config
cp servers.config.sample.json servers.config.json

# Edit with your MCP servers
nano servers.config.json  # or use your preferred editor
```

**Example configuration:**
```json
{
  "servers": [
    {
      "id": "qdrant",
      "transport": "stdio",
      "command": "uvx",
      "args": ["--with", "mcp-server-qdrant", "mcp-server-qdrant"],
      "env": {
        "QDRANT_URL": "http://localhost:6333"
      },
      "startMode": "lazy"
    }
  ]
}
```

### 4. Configure Claude Code

**Global Setup (all projects):**

Edit `~/.claude.json` (Linux/Mac) or `C:\Users\YourUsername\.claude.json` (Windows):

```json
{
  "mcpServers": {
    "broker": {
      "command": "node",
      "args": [
        "/absolute/path/to/your/claude-code-toolkit/submodules/mcp-broker/dist/broker.js"
      ]
    }
  }
}
```

**Replace `/absolute/path/to/your/` with your actual path!**

Examples:
- Linux/Mac: `"/home/username/.config/claude/toolkit/submodules/mcp-broker/dist/broker.js"`
- Windows: `"C:\\Users\\Username\\.claude\\toolkit\\submodules\\mcp-broker\\dist\\broker.js"`

**Per-Project Setup (project-specific MCPs):**

Create `.claude.json` in your project root:

```json
{
  "mcpServers": {
    "broker": {
      "command": "node",
      "args": [
        ".claude-toolkit/submodules/mcp-broker/dist/broker.js"
      ]
    }
  }
}
```

Then add toolkit as submodule:
```bash
git submodule add https://github.com/BerryKuipers/claude-code-toolkit.git .claude-toolkit
cd .claude-toolkit/submodules/mcp-broker
npm install && npm run build
```

---

## Configuration Files

### servers.config.json (Required)

Defines your MCP servers with lazy loading:

```json
{
  "servers": [
    {
      "id": "my-server",
      "transport": "stdio",
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "env": {
        "API_KEY": "${vault:secret/path/to/key}",
        "DEBUG": "${env:DEBUG}"
      },
      "startMode": "lazy"
    }
  ]
}
```

**Fields:**
- `id`: Unique identifier for the server
- `transport`: `stdio` or `http`
- `command`: Command to start the server
- `args`: Command arguments
- `env`: Environment variables (supports `${vault:...}` and `${env:...}`)
- `startMode`: `lazy` (on-demand) or `eager` (start immediately)

### tools.overrides.json (Optional)

Register favorite tools to appear directly in Claude's tool list:

```json
{
  "tools": [
    {
      "name": "qdrant.search",
      "server": "qdrant",
      "title": "Search Vector Database",
      "description": "Search the Qdrant vector database"
    }
  ]
}
```

**Without overrides**, tools are discovered dynamically via `broker.search` and `broker.invoke`.

---

## Usage

### Dynamic Tool Discovery

The broker provides two meta-tools:

**broker.search** - Find available tools:
```
Use broker.search to discover all MCP tools across servers
```

**broker.invoke** - Call any tool:
```
Use broker.invoke with server="qdrant" tool="search" args={...}
```

### Lazy Loading

Servers only start when their tools are called, saving memory and context tokens!

### OAuth Authentication

The broker supports OAuth 2.0 for HTTP MCP servers that require authentication (like Jam, GitHub, etc.).

**Configuration:**
```json
{
  "servers": [
    {
      "id": "jam",
      "transport": "http",
      "url": "https://mcp.jam.dev/mcp",
      "startMode": "lazy",
      "oauth": {
        "authorizationUrl": "https://example.com/oauth/authorize",  // Optional if server supports discovery
        "tokenUrl": "https://example.com/oauth/token",              // Optional if server supports discovery
        "clientId": "your-client-id",                               // Optional, for registered apps
        "clientSecret": "your-client-secret",                       // Optional, for confidential clients
        "scopes": ["read:data", "write:data"],                      // Scopes to request
        "redirectUri": "http://localhost:45454/oauth/callback"      // Default callback URI
      }
    }
  ]
}
```

**Authorization Flow:**

1. **First use**: When you try to use a tool from an OAuth-protected server, the broker:
   - Tries OAuth server discovery (`/.well-known/oauth-authorization-server`)
   - Generates PKCE parameters (secure for public clients)
   - Opens your browser to the authorization page
   - Starts a local callback server
   - Exchanges the authorization code for tokens
   - Saves tokens to `.oauth-tokens/{server-id}.json`

2. **Subsequent uses**: Tokens are loaded from disk and refreshed automatically when expired

3. **Re-authorization**: If tokens become invalid, you'll be prompted to authorize again

**Security:**
- Tokens are stored in `.oauth-tokens/` (gitignored)
- Uses PKCE (Proof Key for Code Exchange) for security
- Supports token refresh to minimize re-auth
- All authorization happens over HTTPS

**Discovery Support:**
If the server implements OAuth server discovery (RFC 8414), you only need to specify:
```json
{
  "oauth": {
    "scopes": ["read:data"],
    "redirectUri": "http://localhost:45454/oauth/callback"
  }
}
```

The broker will automatically discover `authorizationUrl` and `tokenUrl` from the server.

---

## Updating

```bash
cd /path/to/claude-code-toolkit
git pull origin main
cd submodules/mcp-broker
npm install  # only if package.json changed
npm run build
```

Then restart Claude Code to pick up changes.

---

## Multi-Tier Setup (Advanced)

**Global broker** for common MCPs + **per-project broker** for project-specific MCPs:

1. **Global**: Configure `~/.claude.json` with common servers (qdrant, home-nas, etc.)
2. **Project**: Add `.claude.json` in project with project-specific servers
3. Claude Code merges both configurations automatically!

---

## Troubleshooting

### "broker not found"
- Check absolute path in `.claude.json` is correct
- Verify `dist/broker.js` exists (run `npm run build`)

### "server failed to start"
- Check `command` and `args` in `servers.config.json`
- Verify dependencies are installed (python packages, npm packages, etc.)
- Check logs in Claude Code output

### "vault secrets not working"
- Ensure Vault is configured in `~/.claude.json`:
  ```json
  {
    "vault": {
      "address": "http://your-vault:8200",
      "token": "your-token"
    }
  }
  ```
- See [VAULT-SETUP.md](./VAULT-SETUP.md) for details

---

## Example Setups

### Berry's Setup (Global Broker)

```bash
# Toolkit location
D:\berry\Projects\claude-code-toolkit

# Global .claude.json
{
  "mcpServers": {
    "broker": {
      "command": "node",
      "args": ["D:\\berry\\Projects\\claude-code-toolkit\\submodules\\mcp-broker\\dist\\broker.js"]
    }
  }
}

# servers.config.json (7 global MCPs)
- qdrant, homey, home-nas, radarr-sonarr-global,
  sequential-thinking, context7, jam
```

### Per-Project Override Example

**Global broker** handles most MCPs, **project broker** adds project-specific:

```bash
# Project: home-sage
# Uses global broker + adds Spotify/WhatsApp MCPs

# .claude-toolkit/submodules/mcp-broker/servers.config.json
{
  "servers": [
    {
      "id": "spotify",
      "transport": "stdio",
      ...
    },
    {
      "id": "whatsapp",
      "transport": "stdio",
      ...
    }
  ]
}
```

---

## Platform-Specific Notes

### Windows
- Use double backslashes in paths: `C:\\Users\\...`
- Use `cmd /c` prefix for npm commands:
  ```json
  {
    "command": "cmd",
    "args": ["/c", "npx", "-y", "some-package"]
  }
  ```

### Linux/Mac
- Use forward slashes: `/home/user/...`
- Direct command invocation works:
  ```json
  {
    "command": "npx",
    "args": ["-y", "some-package"]
  }
  ```

### WSL (Windows Subsystem for Linux)
- Use Linux paths inside WSL: `/home/username/...`
- For Windows-side tools, use `/mnt/c/...`

---

## Security

- **Never commit** `servers.config.json` with secrets (it's gitignored)
- Use Vault for sensitive credentials: `${vault:secret/path}`
- Or use environment variables: `${env:MY_SECRET}`
- See [VAULT-SETUP.md](./VAULT-SETUP.md) for secure secret management

---

## Need Help?

- Check [REFLECTIVE-MODE.md](./REFLECTIVE-MODE.md) for dynamic discovery details
- Check [INTEGRATION.md](./INTEGRATION.md) for project integration examples
- Open an issue: https://github.com/BerryKuipers/claude-code-toolkit/issues
