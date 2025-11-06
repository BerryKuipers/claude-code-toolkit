# Integration Prompt for Other Repositories

Use this prompt in other repositories to integrate the MCP broker from the Claude Code Toolkit.

---

## Prompt to Use in Other Repos

```
I need to integrate the MCP broker from the claude-code-toolkit submodule into this project.

Context:
- This project has claude-code-toolkit as a submodule at: submodules/claude-code-toolkit
- The MCP broker is located at: submodules/claude-code-toolkit/submodules/mcp-broker
- I want to consolidate all MCP servers behind this single broker

Tasks:
1. Update the submodule to latest:
   - cd submodules/claude-code-toolkit
   - git pull origin main
   - cd submodules/mcp-broker
   - npm install && npm run build

2. Create/update cloud/claude.mcp.json to use ONLY the broker:
   {
     "mcpServers": {
       "broker": {
         "command": "node",
         "args": ["submodules/claude-code-toolkit/submodules/mcp-broker/dist/broker.js"]
       }
     }
   }

3. Configure servers in submodules/claude-code-toolkit/submodules/mcp-broker/servers.config.json:
   - Add each MCP server with:
     * id: unique identifier
     * transport: 'stdio' or 'http'
     * command/args (for stdio) OR url (for http)
     * env: environment variables with ${env:KEY} or ${vault:PATH} syntax

4. (v2.0+) Use reflective mode - NO manual tool registration needed:
   - broker.search - Discover tools dynamically
   - broker.invoke - Call any tool by server+name
   - tools.overrides.json - Optional favorites (empty by default)
   - See REFLECTIVE-MODE.md for details

5. Configure secrets (optional):
   - Create .env in broker directory if needed
   - Set up Vault if desired (see VAULT-SETUP.md)
   - Update env references in servers.config.json

Example migration:
OLD (cloud/claude.mcp.json):
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxx"
      }
    }
  }
}

NEW (cloud/claude.mcp.json):
{
  "mcpServers": {
    "broker": {
      "command": "node",
      "args": ["submodules/claude-code-toolkit/submodules/mcp-broker/dist/broker.js"]
    }
  }
}

NEW (submodules/claude-code-toolkit/submodules/mcp-broker/servers.config.json):
{
  "servers": [
    {
      "id": "filesystem",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./data"],
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

v2.0+ Reflective Mode (Recommended):
- Leave tools.registry.json and tools.overrides.json empty
- Use broker.search to discover tools
- Use broker.invoke to call tools
- Optionally add favorites to tools.overrides.json

Example usage after setup:
  // Discover tools
  broker.search({})

  // Call a tool
  broker.invoke({
    server: "github",
    tool: "create_or_update_file",
    args: {...}
  })

Legacy (v1.x compatibility):
If you prefer static registration, add tools to tools.registry.json:
{
  "tools": [
    {
      "name": "read_file",
      "server": "filesystem",
      "title": "Read File",
      "description": "Read a file from the filesystem"
    }
  ]
}

6. Test the setup:
   - Restart Claude Code
   - Try broker.search with no args
   - Try broker.invoke with a known server/tool
   - Check lazy initialization works

Do not modify the toolkit itself, only configure it for this project.
```

---

## Short Version (Minimal Setup)

```
Integrate MCP broker from claude-code-toolkit submodule:

1. Update & build:
   cd submodules/claude-code-toolkit && git pull
   cd submodules/mcp-broker && npm install && npm run build

2. Replace cloud/claude.mcp.json with:
   {
     "mcpServers": {
       "broker": {
         "command": "node",
         "args": ["submodules/claude-code-toolkit/submodules/mcp-broker/dist/broker.js"]
       }
     }
   }

3. Configure broker:
   - Copy sample configs: servers.config.sample.json → servers.config.json
   - Add your MCP servers there instead of claude.mcp.json
   - Register tools in tools.registry.json

4. Restart Claude Code

See submodules/claude-code-toolkit/submodules/mcp-broker/INTEGRATION.md for details.
```

---

## With Vault Integration

```
Integrate MCP broker with Vault support:

1. Update & build broker (as above)

2. Configure Vault in broker directory:
   cp .env.example .env

   Edit .env:
   VAULT_ENABLED=true
   VAULT_HOST=192.168.1.100
   VAULT_PORT=8200
   VAULT_TOKEN=your-vault-token
   VAULT_MOUNT_PATH=secret
   VAULT_PREFERRED_CIDR=192.168.1.0/24

3. Use vault secrets in servers.config.json:
   {
     "servers": [
       {
         "id": "github",
         "transport": "stdio",
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_TOKEN": "${vault:mcp/github/token}"
         },
         "startMode": "lazy"
       }
     ]
   }

4. Store secrets in Vault:
   vault kv put secret/mcp/github token=ghp_xxxxxxxxxxxx

5. Update cloud/claude.mcp.json to use broker (as above)

6. Restart Claude Code

See VAULT-SETUP.md for complete Vault documentation.
```

---

## Common Scenarios

### Scenario 1: First Time Setup (No Existing MCP Servers)

```
Set up MCP broker for the first time:
1. Update toolkit submodule
2. Build broker: cd submodules/claude-code-toolkit/submodules/mcp-broker && npm install && npm run build
3. Create cloud/claude.mcp.json with broker entry only
4. Leave broker configs empty for now
5. Restart Claude Code
6. Verify tools.search works (returns empty list)
```

### Scenario 2: Migrating Existing MCP Servers

```
Migrate existing MCP servers to broker:
1. Backup cloud/claude.mcp.json
2. Update and build broker (as above)
3. For each server in old config, create entry in broker's servers.config.json
4. Register all tools in tools.registry.json
5. Replace cloud/claude.mcp.json with broker-only config
6. Restart Claude Code and test
```

### Scenario 3: Adding Vault for Secrets

```
Add Vault integration to existing broker setup:
1. Set up Vault environment variables in .env
2. Change ${env:SECRET} to ${vault:path/to/secret} in servers.config.json
3. Store secrets in Vault
4. Restart Claude Code
5. Check logs for Vault initialization
```

---

## Troubleshooting in Other Repos

### Broker Not Starting
- Verify path in cloud/claude.mcp.json is correct
- Check broker is built: ls submodules/claude-code-toolkit/submodules/mcp-broker/dist/
- Run manually to see errors: node submodules/claude-code-toolkit/submodules/mcp-broker/dist/broker.js

### Servers Not Connecting
- Check servers.config.json syntax
- Verify command paths are correct
- Check environment variables are set
- Look at Claude Code logs for connection errors

### Vault Not Working
- Verify VAULT_ENABLED=true
- Check network (VAULT_PREFERRED_CIDR)
- Test Vault access: vault kv get secret/test
- Check broker logs for Vault warnings

---

## Documentation References

In the toolkit submodule:
- Full guide: submodules/claude-code-toolkit/submodules/mcp-broker/README.md
- Integration: submodules/claude-code-toolkit/submodules/mcp-broker/INTEGRATION.md
- Vault setup: submodules/claude-code-toolkit/submodules/mcp-broker/VAULT-SETUP.md
- Tech details: submodules/claude-code-toolkit/submodules/mcp-broker/SUMMARY.md
