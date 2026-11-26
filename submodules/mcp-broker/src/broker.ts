#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { loadServersConfig, loadToolsRegistry, loadToolOverrides } from './config.js';
import { callUpstreamTool, disconnectAll } from './upstream.js';
import { describeTool, describeUpstreamTool, searchTools } from './discovery.js';

const server = new Server(
  {
    name: 'mcp-broker',
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
    describeTool,
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
    return searchTools(serversConfig.servers, [...toolOverrides.overrides, ...toolsRegistry.tools], args);
  }

  if (name === 'broker.describe') {
    return describeUpstreamTool(serversConfig.servers, args);
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

  const transport = new StdioServerTransport();
  await server.connect(transport);

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
