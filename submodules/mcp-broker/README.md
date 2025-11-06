# MCP Broker

A lightweight Model Context Protocol (MCP) broker with lazy initialization for upstream MCP servers. This broker allows you to consolidate multiple MCP servers behind a single entry point, with on-demand spawning of upstream servers.

## 📚 Documentation

- **[SETUP.md](./SETUP.md)** - Complete setup guide for global and per-project configurations
- **[REFLECTIVE-MODE.md](./REFLECTIVE-MODE.md)** - Dynamic tool discovery with `broker.search` and `broker.invoke`
- **[INTEGRATION.md](./INTEGRATION.md)** - Integration examples for projects
- **[VAULT-SETUP.md](./VAULT-SETUP.md)** - Secure secret management with Vault

## Features

### v2.0+ Reflective Mode
- **Dynamic Discovery**: No manual tool registration needed
- **Meta-Tools**: `broker.search` and `broker.invoke` for on-demand access
- **Optional Favorites**: Register frequently-used tools via `tools.overrides.json`
- **Tool Caching**: Upstream tool lists cached per session
- **Backwards Compatible**: `tools.registry.json` still supported

### Core Features
- **Lazy Initialization**: Upstream servers spawn/connect only when first called
- **Multiple Transport Support**: Supports both STDIO and HTTP upstream servers
- **Multi-Layer Secret Resolution**:
  - .env file (local overrides)
  - Process environment
  - Optional Vault on NAS (with network detection)
- **Configuration-Based**: Separate config files for servers and tools
- **Secret Syntax**: Use `${env:VAR}` or `${vault:PATH}` in configs
- **Graceful Fallback**: Continues without Vault if unreachable
- **Dual Mode**: Run as STDIO server or HTTP server

## Project Structure

```
submodules/mcp-broker/
├── src/
│   ├── config.ts         # Configuration loading with secret resolution
│   ├── secrets.ts        # Multi-layer secret resolver
│   ├── vault.ts          # Vault client with caching
│   ├── network.ts        # Network detection for NAS preference
│   ├── upstream.ts       # Upstream server client management
│   ├── broker.ts         # STDIO broker server
│   └── http-broker.ts    # HTTP broker server
├── dist/                 # Compiled JavaScript (generated)
├── servers.config.json   # Live server definitions (empty by default)
├── tools.registry.json   # Live tool registry (optional, for compatibility)
├── tools.overrides.json  # Favorite tools (empty by default)
├── *.sample.json         # Example configurations
├── .env.example          # Sample environment variables
├── README.md             # This file
├── REFLECTIVE-MODE.md    # Dynamic discovery documentation
├── INTEGRATION.md        # Integration guide
├── VAULT-SETUP.md        # Vault configuration guide
├── package.json
└── tsconfig.json
```

## Installation

```bash
cd submodules/mcp-broker
npm install
npm run build
```

## Configuration

### Step 1: Configure Servers

Copy the sample and edit `servers.config.json`:

```bash
cp servers.config.sample.json servers.config.json
```

Example server configuration:

```json
{
  "servers": [
    {
      "id": "my-stdio-server",
      "transport": "stdio",
      "command": "node",
      "args": ["path/to/server.js"],
      "env": {
        "API_KEY": "${env:MY_API_KEY}"
      },
      "startMode": "lazy"
    },
    {
      "id": "my-http-server",
      "transport": "http",
      "url": "http://localhost:8080/mcp",
      "env": {},
      "startMode": "lazy"
    }
  ]
}
```

### Step 2: Register Tools

Copy the sample and edit `tools.registry.json`:

```bash
cp tools.registry.sample.json tools.registry.json
```

Example tool registry:

```json
{
  "tools": [
    {
      "name": "myserver.doSomething",
      "server": "my-stdio-server",
      "title": "Do Something",
      "description": "Performs an action on the upstream server",
      "requireSchema": false
    }
  ]
}
```

### Step 3: Set Environment Variables

Copy `.env.example` and configure your environment:

```bash
cp .env.example .env
```

## Usage

### As STDIO Server (for Claude Code)

In your `claude.mcp.json`:

```json
{
  "mcpServers": {
    "broker": {
      "command": "node",
      "args": ["path/to/submodules/mcp-broker/dist/broker.js"]
    }
  }
}
```

Or run directly:

```bash
npm run start:stdio
```

### As HTTP Server

```bash
BROKER_PORT=3033 npm run start:http
```

The broker will be available at `http://localhost:3033/mcp`.

## Built-in Tools

### tools.search

Search available tools in the registry.

**Arguments:**
- `query` (optional): Search query to filter tools by name, title, or description

**Example:**
```json
{
  "name": "tools.search",
  "arguments": {
    "query": "file"
  }
}
```

## How It Works

1. **Registration**: The broker reads `tools.registry.json` and registers all tools
2. **Discovery**: Claude Code sees all registered tools via `tools.search` or tool listing
3. **Lazy Start**: When a tool is first called:
   - The broker looks up which server provides that tool
   - If the server isn't running, it spawns/connects to it
   - The tool call is forwarded to the upstream server
4. **Reuse**: Subsequent calls to the same server reuse the existing connection

## Configuration Schema

### ServerConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the server |
| `transport` | 'stdio' \| 'http' | Yes | Transport type |
| `command` | string | STDIO only | Command to execute |
| `args` | string[] | No | Command arguments |
| `url` | string | HTTP only | HTTP endpoint URL |
| `env` | object | No | Environment variables |
| `startMode` | 'lazy' \| 'eager' | No | Start mode (default: 'lazy') |

### ToolRegistryEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Tool name (must match upstream) |
| `server` | string | Yes | Server ID that provides this tool |
| `title` | string | No | Human-readable title |
| `description` | string | No | Tool description |
| `requireSchema` | boolean | No | Whether schema is required (default: false) |

## Environment Variable Expansion

Use `${env:VAR_NAME}` syntax in any string field in `servers.config.json`:

```json
{
  "env": {
    "API_KEY": "${env:MY_SECRET_KEY}",
    "BASE_URL": "${env:SERVICE_URL}"
  }
}
```

Missing environment variables resolve to empty strings.

## Integration with Claude Code Toolkit

When using this toolkit as a submodule in other repos:

1. Add the toolkit as a submodule:
   ```bash
   git submodule add <toolkit-url> submodules/claude-code-toolkit
   ```

2. Reference the broker in your project's `cloud/claude.mcp.json`:
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

3. Create your own config files at the broker location or use relative paths

## Development

```bash
# Build
npm run build

# Test STDIO mode
npm run start:stdio

# Test HTTP mode
npm run start:http
```

## License

Part of the Claude Code Toolkit project.
