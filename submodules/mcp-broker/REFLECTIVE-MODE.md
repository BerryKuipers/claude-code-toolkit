# Reflective Mode - Dynamic Tool Discovery

The MCP Broker v2.0+ operates in **reflective mode**, eliminating the need for manual tool registration while preserving lazy loading and performance.

## Overview

Instead of manually registering every tool in `tools.registry.json`, the broker now:
1. Provides two meta-tools (`broker.search` and `broker.invoke`) for dynamic discovery
2. Optionally registers "favorite" tools via `tools.overrides.json`
3. Discovers upstream tools on-demand with caching
4. Never requires a giant static registry

## Key Changes from v1.x

### Before (v1.x - Static Registry)
- Required manual tool registration in `tools.registry.json`
- Every tool needed an entry: name, server, title, description
- Adding new upstream servers meant updating the registry
- Large registries consumed tokens

### After (v2.0+ - Reflective Mode)
- `broker.search` - Discover tools dynamically
- `broker.invoke` - Call any upstream tool by name
- `tools.overrides.json` - Optional favorites (empty by default)
- `tools.registry.json` - Still supported for backwards compatibility
- Lazy loading + caching for performance

## Core Meta-Tools

### broker.search

Discover available tools across all upstream servers.

**Parameters:**
- `q` (string, optional): Search query to filter tools
- `servers` (string[], optional): Limit search to specific server IDs

**Behavior:**
1. Returns tools from `tools.overrides.json` first (if any)
2. Returns tools from `tools.registry.json` (if any)
3. For remaining servers:
   - If cached, searches cached tool names
   - If not cached and `q` is empty, connects and lists tools
   - If not cached and `q` is provided, skips (avoids unnecessary connections)

**Examples:**

```javascript
// List all tools (light, no connections if empty query)
{
  "name": "broker.search",
  "arguments": {}
}

// Search for specific tools
{
  "name": "broker.search",
  "arguments": {
    "q": "search"
  }
}

// Search within specific servers
{
  "name": "broker.search",
  "arguments": {
    "servers": ["qdrant", "github"]
  }
}
```

**Response Format:**
```json
[
  {
    "server": "qdrant",
    "name": "qdrant.search",
    "title": "Qdrant Vector Search",
    "description": "Search the Qdrant vector database"
  },
  {
    "server": "github",
    "name": "github.create_issue",
    "title": "Create GitHub Issue",
    "description": "Create a new issue in a GitHub repository"
  }
]
```

### broker.invoke

Call any upstream tool by server ID and tool name.

**Parameters:**
- `server` (string, required): Server ID from `servers.config.json`
- `tool` (string, required): Tool name exactly as exposed by upstream
- `args` (object, optional): Arguments to pass to the tool

**Behavior:**
1. Validates server exists
2. Lazily connects/spawns server if not already connected
3. Forwards tool call to upstream
4. Returns upstream response as-is
5. Caches connection for future calls

**Example:**

```javascript
{
  "name": "broker.invoke",
  "arguments": {
    "server": "qdrant",
    "tool": "search",
    "args": {
      "collection": "my_collection",
      "query": "example search",
      "limit": 10
    }
  }
}
```

## Tool Override System

### Purpose

Register a small number of "favorite" tools that:
- Appear in tool lists natively (not as meta-tools)
- Have Claude-friendly names and descriptions
- Are called directly without `broker.invoke`

### Configuration

**tools.overrides.json** (empty by default):

```json
{
  "overrides": []
}
```

**Example with overrides:**

```json
{
  "overrides": [
    {
      "name": "qdrant.search",
      "server": "qdrant",
      "title": "Qdrant Vector Search",
      "description": "Search the Qdrant vector database"
    },
    {
      "name": "github.create_issue",
      "server": "github",
      "title": "Create GitHub Issue",
      "description": "Create a new issue"
    }
  ]
}
```

**Behavior:**
- Override tools appear in `tools/list` as native tools
- Can be called directly: `{"name": "qdrant.search", "arguments": {...}}`
- Broker automatically routes to correct upstream server
- Still lazy loads - server only spawns on first call

### When to Use Overrides

Use `tools.overrides.json` for:
- ✅ Frequently used tools (3-10 entries)
- ✅ Tools you want Claude to see without discovery
- ✅ Tools with better descriptions than upstream provides

Don't use for:
- ❌ Every tool from every server (defeats the purpose)
- ❌ Rarely used tools (use `broker.invoke` instead)
- ❌ Tools that change frequently

## Backwards Compatibility

### tools.registry.json

Still fully supported! If you have existing registries:
- They continue to work exactly as before
- Tools are registered natively
- Can coexist with `tools.overrides.json`
- Useful for migration or mixed approaches

**Migration path:**
1. Keep `tools.registry.json` as-is initially
2. Try `broker.search` and `broker.invoke` for new tools
3. Gradually move favorite tools to `tools.overrides.json`
4. Eventually empty `tools.registry.json` (or remove it)

## Caching Strategy

### Tool List Caching

- **Per-server basis**: Each server's tool list is cached after first fetch
- **Session lifetime**: Cache persists for the broker process lifetime
- **Lazy population**: Only fetched when needed (search or invoke)

### Cache Behavior

**First `broker.search` call (empty query):**
- Connects to all uncached servers
- Fetches and caches tool lists
- Returns all tools

**Subsequent `broker.search` calls:**
- Uses cached lists (no connection)
- Filters in-memory
- Fast response

**First `broker.invoke` call to a server:**
- Connects/spawns server
- Calls tool
- Caches connection
- Future `broker.search` reuses this connection to fetch tools

### Performance

- **No connections**: If you never use a server, it never spawns
- **Single connection**: Each server connects at most once
- **Fast search**: Cached tool lists enable instant filtering
- **Low tokens**: Meta-tools + overrides = minimal token usage

## Usage Patterns

### Pattern 1: Discovery First

```javascript
// Step 1: Discover what's available
broker.search({})

// Step 2: Call specific tool
broker.invoke({
  server: "qdrant",
  tool: "search",
  args: {...}
})
```

### Pattern 2: Direct Invoke (Known Tools)

```javascript
// If you know the server and tool name
broker.invoke({
  server: "github",
  tool: "create_issue",
  args: {
    repo: "owner/repo",
    title: "Bug report",
    body: "Description"
  }
})
```

### Pattern 3: Favorite Tools

```json
// tools.overrides.json
{
  "overrides": [
    {"name": "search_vectors", "server": "qdrant", ...}
  ]
}
```

```javascript
// Call directly by override name
search_vectors({
  collection: "docs",
  query: "example"
})
```

## Error Handling

### Server Not Found

```javascript
broker.invoke({server: "nonexistent", tool: "foo", args: {}})
// Error: Server not found: nonexistent
```

### Tool Not Found (Static Tools)

```javascript
some_unknown_tool({})
// Error: Tool not found: some_unknown_tool.
// Use broker.search to discover tools or broker.invoke to call by name.
```

### Upstream Server Failure

```javascript
broker.search({})
// Logs: [broker.search] Failed to list tools from qdrant: connection timeout
// Returns: tools from other servers (graceful degradation)
```

## Best Practices

### 1. Start with Empty Configs

```json
// tools.overrides.json
{"overrides": []}

// tools.registry.json
{"tools": []}
```

Use `broker.search` and `broker.invoke` exclusively at first.

### 2. Add Overrides Selectively

After identifying frequently used tools:

```json
{
  "overrides": [
    {"name": "my_favorite_tool", "server": "main-server", ...}
  ]
}
```

### 3. Use Search for Exploration

```javascript
// What tools does this server have?
broker.search({servers: ["qdrant"]})

// What search-related tools exist?
broker.search({q: "search"})
```

### 4. Use Invoke for One-offs

```javascript
// Don't register a tool you'll use once
broker.invoke({
  server: "special-service",
  tool: "rare_operation",
  args: {...}
})
```

## Migration Guide

### From Static Registry (v1.x)

**Before:**
```json
// tools.registry.json (100+ entries)
{
  "tools": [
    {"name": "qdrant.search", "server": "qdrant", ...},
    {"name": "qdrant.list", "server": "qdrant", ...},
    {"name": "github.list_repos", "server": "github", ...},
    ...
  ]
}
```

**After:**
```json
// tools.overrides.json (5 favorites)
{
  "overrides": [
    {"name": "qdrant.search", "server": "qdrant", ...}
  ]
}

// tools.registry.json
{"tools": []}
```

**Usage:**
- Call favorites directly: `qdrant.search(...)`
- Discover others: `broker.search({q: "github"})`
- Invoke others: `broker.invoke({server: "github", tool: "list_repos", args: {}})`

## Troubleshooting

### broker.search returns empty

**Possible causes:**
1. All config files are empty (expected)
2. Servers failed to connect (check logs)
3. Query filter too restrictive

**Solution:**
```javascript
// Try without query to see all servers
broker.search({})

// Try specific server
broker.search({servers: ["your-server-id"]})
```

### Tool not found error

**Message:** `Tool not found: xyz. Use broker.search to discover tools or broker.invoke to call by name.`

**Solutions:**
1. Use `broker.search` to find the correct tool name
2. Use `broker.invoke` with exact upstream tool name
3. Add tool to `tools.overrides.json` if frequently used

### Server connection fails

**Logs:** `[broker.search] Failed to list tools from xyz: error message`

**Check:**
1. Server config in `servers.config.json` is correct
2. Command/URL is valid
3. Environment variables are set
4. Server process can actually start

## Summary

**Reflective Mode Benefits:**
- ✅ No manual tool registration needed
- ✅ Dynamic discovery via `broker.search`
- ✅ Generic passthrough via `broker.invoke`
- ✅ Optional favorites via `tools.overrides.json`
- ✅ Lazy loading + caching for performance
- ✅ Backwards compatible with `tools.registry.json`
- ✅ Lower token usage
- ✅ Easier maintenance

**Key Files:**
- `tools.overrides.json` - Optional favorites (empty by default)
- `tools.registry.json` - Legacy support (still works)
- `servers.config.json` - Server definitions (unchanged)

**Meta-Tools:**
- `broker.search` - Discover tools dynamically
- `broker.invoke` - Call any tool by server + name
