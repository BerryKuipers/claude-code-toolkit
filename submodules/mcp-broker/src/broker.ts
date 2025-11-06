#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { loadServersConfig, loadToolsRegistry } from './config.js';
import { callUpstreamTool, disconnectAll } from './upstream.js';

const server = new Server(
  {
    name: 'mcp-broker',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

let serversConfig: any;
let toolsRegistry: any;
let serverMap: Map<string, any>;

async function initializeConfig() {
  serversConfig = await loadServersConfig();
  toolsRegistry = loadToolsRegistry();
  serverMap = new Map(serversConfig.servers.map((s: any) => [s.id, s]));
}

server.setRequestHandler(ListToolsRequestSchema, async () => {
  const tools: any[] = [
    {
      name: 'tools.search',
      description: 'Search available tools from the broker registry',
      inputSchema: {
        type: 'object' as const,
        properties: {
          query: {
            type: 'string' as const,
            description: 'Optional search query to filter tools',
          },
        },
      },
    },
  ];

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

  if (name === 'tools.search') {
    const query = (args?.query as string) || '';
    const filtered = toolsRegistry.tools.filter((t: any) => {
      if (!query) return true;
      const searchText = `${t.name} ${t.title || ''} ${t.description || ''}`.toLowerCase();
      return searchText.includes(query.toLowerCase());
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            filtered.map((t: any) => ({
              name: t.name,
              server: t.server,
              title: t.title,
              description: t.description,
            })),
            null,
            2
          ),
        },
      ],
    };
  }

  const toolEntry = toolsRegistry.tools.find((t: any) => t.name === name);
  if (!toolEntry) {
    throw new Error(`Tool not found: ${name}`);
  }

  const serverConfig = serverMap.get(toolEntry.server);
  if (!serverConfig) {
    throw new Error(`Server not found for tool ${name}: ${toolEntry.server}`);
  }

  const result = await callUpstreamTool(serverConfig, name, args || {});

  return result;
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
