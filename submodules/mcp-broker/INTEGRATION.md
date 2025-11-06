# MCP Broker Integration Guide

This guide explains how to integrate the MCP Broker into your projects when using the Claude Code Toolkit as a submodule.

## Scenario: Using the Toolkit as a Submodule

When you add the Claude Code Toolkit as a submodule to your project, the MCP Broker becomes available for consolidating your MCP servers.

### Step 1: Add Toolkit as Submodule

In your project root:

```bash
git submodule add <toolkit-url> submodules/claude-code-toolkit
git submodule update --init --recursive
cd submodules/claude-code-toolkit/submodules/mcp-broker
npm install
npm run build
```

### Step 2: Create Broker Configuration in Your Project

You can either:

**Option A: Configure directly in the broker directory**

```bash
cd submodules/claude-code-toolkit/submodules/mcp-broker
cp servers.config.sample.json servers.config.json
cp tools.registry.sample.json tools.registry.json
# Edit the files as needed
```

**Option B: Use workspace-relative paths** (advanced)

Create your own config files anywhere in your project and modify `src/config.ts` to load from custom paths.

### Step 3: Configure Claude Code to Use the Broker

Create or update `cloud/claude.mcp.json` in your project:

```json
{
  "mcpServers": {
    "broker": {
      "command": "node",
      "args": ["submodules/claude-code-toolkit/submodules/mcp-broker/dist/broker.js"]
    }
  }
}
```

### Step 4: Migrate Existing MCP Servers

If you already have MCP servers configured in `cloud/claude.mcp.json`:

**Before:**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your-token"
      }
    }
  }
}
```

**After (cloud/claude.mcp.json):**
```json
{
  "mcpServers": {
    "broker": {
      "command": "node",
      "args": ["submodules/claude-code-toolkit/submodules/mcp-broker/dist/broker.js"]
    }
  }
}
```

**Add to servers.config.json:**
```json
{
  "servers": [
    {
      "id": "filesystem",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"],
      "env": {},
      "startMode": "lazy"
    },
    {
      "id": "github",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      },
      "startMode": "lazy"
    }
  ]
}
```

**Add to tools.registry.json:**
```json
{
  "tools": [
    {
      "name": "read_file",
      "server": "filesystem",
      "title": "Read File",
      "description": "Read a file from the filesystem"
    },
    {
      "name": "write_file",
      "server": "filesystem",
      "title": "Write File",
      "description": "Write content to a file"
    },
    {
      "name": "create_or_update_file",
      "server": "github",
      "title": "Create or Update File",
      "description": "Create or update a file in a GitHub repository"
    }
  ]
}
```

## Benefits of Using the Broker

1. **Single MCP Server Entry**: Claude Code only sees one MCP server instead of many
2. **Lazy Loading**: Upstream servers only start when their tools are needed
3. **Centralized Configuration**: All MCP servers configured in one place
4. **Environment Management**: Use `${env:VAR}` syntax for secrets
5. **Tool Discovery**: Use `tools.search` to find available tools
6. **Reusable Across Projects**: Same broker can be used in multiple projects via the toolkit

## Example: Complete Setup

Here's a complete example for a project using Google Drive and Salesforce MCP servers:

**cloud/claude.mcp.json:**
```json
{
  "mcpServers": {
    "broker": {
      "command": "node",
      "args": ["submodules/claude-code-toolkit/submodules/mcp-broker/dist/broker.js"]
    }
  }
}
```

**submodules/claude-code-toolkit/submodules/mcp-broker/servers.config.json:**
```json
{
  "servers": [
    {
      "id": "google-drive",
      "transport": "stdio",
      "command": "node",
      "args": ["path/to/google-drive-mcp/dist/index.js"],
      "env": {
        "GOOGLE_CLIENT_ID": "${env:GOOGLE_CLIENT_ID}",
        "GOOGLE_CLIENT_SECRET": "${env:GOOGLE_CLIENT_SECRET}",
        "GOOGLE_REFRESH_TOKEN": "${env:GOOGLE_REFRESH_TOKEN}"
      },
      "startMode": "lazy"
    },
    {
      "id": "salesforce",
      "transport": "http",
      "url": "http://localhost:8080/mcp",
      "env": {},
      "startMode": "lazy"
    }
  ]
}
```

**submodules/claude-code-toolkit/submodules/mcp-broker/tools.registry.json:**
```json
{
  "tools": [
    {
      "name": "drive.listFiles",
      "server": "google-drive",
      "title": "List Drive Files",
      "description": "List files in Google Drive"
    },
    {
      "name": "drive.downloadFile",
      "server": "google-drive",
      "title": "Download Drive File",
      "description": "Download a file from Google Drive"
    },
    {
      "name": "salesforce.query",
      "server": "salesforce",
      "title": "SOQL Query",
      "description": "Execute a SOQL query in Salesforce"
    },
    {
      "name": "salesforce.createRecord",
      "server": "salesforce",
      "title": "Create Salesforce Record",
      "description": "Create a new record in Salesforce"
    }
  ]
}
```

**Your project's .env:**
```bash
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REFRESH_TOKEN=your-refresh-token
```

## Updating the Toolkit

When you update the toolkit submodule:

```bash
cd submodules/claude-code-toolkit
git pull origin main
cd submodules/mcp-broker
npm install
npm run build
```

Your configuration files (servers.config.json, tools.registry.json) remain unchanged.

## Troubleshooting

### Broker Not Starting

1. Check that the broker is built:
   ```bash
   ls submodules/claude-code-toolkit/submodules/mcp-broker/dist/
   ```

2. Verify the path in `cloud/claude.mcp.json` is correct

3. Check for errors in Claude Code logs

### Upstream Server Not Connecting

1. Verify the server configuration in `servers.config.json`
2. Check environment variables are set correctly
3. Test the upstream server independently first
4. Check broker logs for connection errors

### Tools Not Appearing

1. Ensure tools are registered in `tools.registry.json`
2. Verify the `server` field matches a server `id` in `servers.config.json`
3. Use `tools.search` to debug tool visibility
4. Restart Claude Code after configuration changes

## Advanced: Custom Config Paths

If you want to keep broker configs in your project root instead of the toolkit:

1. Modify `submodules/claude-code-toolkit/submodules/mcp-broker/src/config.ts`
2. Change the paths in `loadServersConfig()` and `loadToolsRegistry()`
3. Rebuild the broker

This allows you to keep the toolkit clean and your project-specific configs separate.
