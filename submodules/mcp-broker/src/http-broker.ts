#!/usr/bin/env node
import express from 'express';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { loadServersConfig, loadToolsRegistry, loadToolOverrides } from './config.js';
import { callUpstreamTool, listUpstreamTools, getCachedTools, disconnectAll } from './upstream.js';

const app = express();
const port = parseInt(process.env.BROKER_PORT || '3033', 10);

const server = new Server(
  {
    name: 'mcp-broker-http',
    version: '2.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

let serversConfig: any;
let toolsRegistry: any;
let toolOverrides: any;
let serverMap: Map<string, any>;

async function initializeConfig() {
  serversConfig = await loadServersConfig();
  toolsRegistry = loadToolsRegistry();
  toolOverrides = loadToolOverrides();
  serverMap = new Map(serversConfig.servers.map((s: any) => [s.id, s]));
}

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: any[] = [
    {
      name: 'broker.search',
      description: 'Search and discover tools from all upstream servers',
      inputSchema: {
        type: 'object' as const,
        properties: {
          q: {
            type: 'string' as const,
            description: 'Optional search query to filter tools',
          },
          servers: {
            type: 'array' as const,
            items: { type: 'string' as const },
            description: 'Optional list of server IDs to search',
          },
        },
      },
    },
    {
      name: 'broker.invoke',
      description: 'Invoke any upstream tool by server and tool name',
      inputSchema: {
        type: 'object' as const,
        properties: {
          server: {
            type: 'string' as const,
            description: 'Server ID',
          },
          tool: {
            type: 'string' as const,
            description: 'Tool name as exposed by upstream',
          },
          args: {
            type: 'object' as const,
            description: 'Arguments to pass to the tool',
          },
        },
        required: ['server', 'tool'],
      },
    },
  ];

  for (const entry of toolOverrides.overrides) {
    tools.push({
      name: entry.name,
      description: entry.description || entry.title || `Tool from ${entry.server}`,
      inputSchema: {
        type: 'object' as const,
        properties: {},
      },
    });
  }

  for (const entry of toolsRegistry.tools) {
    tools.push({
      name: entry.name,
      description: entry.description || entry.title || `Tool from ${entry.server}`,
      inputSchema: {
        type: 'object' as const,
        properties: {},
      },
    });
  }

  return { tools };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === 'broker.search') {
    const q = (args?.q as string) || '';
    const serverFilter = (args?.servers as string[]) || [];

    const results: any[] = [];

    for (const override of toolOverrides.overrides) {
      if (serverFilter.length > 0 && !serverFilter.includes(override.server)) {
        continue;
      }

      if (q) {
        const searchText = `${override.name} ${override.title || ''} ${override.description || ''}`.toLowerCase();
        if (!searchText.includes(q.toLowerCase())) {
          continue;
        }
      }

      results.push({
        server: override.server,
        name: override.name,
        title: override.title || override.name,
        description: override.description || '',
      });
    }

    for (const entry of toolsRegistry.tools) {
      if (serverFilter.length > 0 && !serverFilter.includes(entry.server)) {
        continue;
      }

      if (q) {
        const searchText = `${entry.name} ${entry.title || ''} ${entry.description || ''}`.toLowerCase();
        if (!searchText.includes(q.toLowerCase())) {
          continue;
        }
      }

      results.push({
        server: entry.server,
        name: entry.name,
        title: entry.title || entry.name,
        description: entry.description || '',
      });
    }

    const serversToQuery = serverFilter.length > 0
      ? serversConfig.servers.filter((s: any) => serverFilter.includes(s.id))
      : serversConfig.servers;

    for (const serverCfg of serversToQuery) {
      let tools = getCachedTools(serverCfg.id);

      if (!tools) {
        if (q) {
          continue;
        }

        try {
          tools = await listUpstreamTools(serverCfg);
        } catch (error) {
          console.warn(`[broker.search] Failed to list tools from ${serverCfg.id}:`, (error as Error).message);
          continue;
        }
      }

      for (const tool of tools) {
        if (q) {
          const searchText = `${tool.name} ${tool.description || ''}`.toLowerCase();
          if (!searchText.includes(q.toLowerCase())) {
            continue;
          }
        }

        const alreadyListed = results.some((r) => r.server === serverCfg.id && r.name === tool.name);
        if (!alreadyListed) {
          results.push({
            server: serverCfg.id,
            name: tool.name,
            title: tool.name,
            description: tool.description || '',
          });
        }
      }
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(results, null, 2),
        },
      ],
    };
  }

  if (name === 'broker.invoke') {
    const serverId = args?.server as string;
    const toolName = args?.tool as string;
    const toolArgs = (args?.args as Record<string, unknown>) || {};

    if (!serverId || !toolName) {
      throw new Error('broker.invoke requires "server" and "tool" parameters');
    }

    const serverConfig = serverMap.get(serverId);
    if (!serverConfig) {
      throw new Error(`Server not found: ${serverId}`);
    }

    const result = await callUpstreamTool(serverConfig, toolName, toolArgs);
    return result;
  }

  const overrideEntry = toolOverrides.overrides.find((t: any) => t.name === name);
  if (overrideEntry) {
    const serverConfig = serverMap.get(overrideEntry.server);
    if (!serverConfig) {
      throw new Error(`Server not found for tool ${name}: ${overrideEntry.server}`);
    }

    const result = await callUpstreamTool(serverConfig, name, args || {});
    return result;
  }

  const toolEntry = toolsRegistry.tools.find((t: any) => t.name === name);
  if (toolEntry) {
    const serverConfig = serverMap.get(toolEntry.server);
    if (!serverConfig) {
      throw new Error(`Server not found for tool ${name}: ${toolEntry.server}`);
    }

    const result = await callUpstreamTool(serverConfig, name, args || {});
    return result;
  }

  throw new Error(`Tool not found: ${name}. Use broker.search to discover tools or broker.invoke to call by name.`);
});

async function main() {
  await initializeConfig();

  app.use(express.json());

  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: () => Math.random().toString(36).substring(7),
  });

  await server.connect(transport);

  app.post('/mcp', async (req, res) => {
    await transport.handleRequest(req, res);
  });

  app.get('/mcp', async (req, res) => {
    await transport.handleRequest(req, res);
  });

  app.delete('/mcp', async (req, res) => {
    await transport.handleRequest(req, res);
  });

  app.listen(port, () => {
    console.log(`MCP Broker HTTP server listening on port ${port}`);
    console.log(`Endpoint: http://localhost:${port}/mcp`);
  });

  process.on('SIGINT', () => {
    disconnectAll();
    process.exit(0);
  });

  process.on('SIGTERM', () => {
    disconnectAll();
    process.exit(0);
  });
}

main().catch((error) => {
  console.error('Fatal error:', error);
  disconnectAll();
  process.exit(1);
});
