import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import type { ServerConfig } from './config.js';

const upstreamClients = new Map<string, Client>();
const toolsCache = new Map<string, any[]>();

async function createStdioClient(config: ServerConfig): Promise<Client> {
  if (!config.command) {
    throw new Error(`Server ${config.id} has stdio transport but no command specified`);
  }

  const mergedEnv: Record<string, string> = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (value !== undefined) {
      mergedEnv[key] = value;
    }
  }
  for (const [key, value] of Object.entries(config.env)) {
    mergedEnv[key] = value;
  }

  const transport = new StdioClientTransport({
    command: config.command,
    args: config.args || [],
    env: mergedEnv,
  });

  const client = new Client(
    {
      name: 'mcp-broker',
      version: '1.0.0',
    },
    {
      capabilities: {},
    }
  );

  await client.connect(transport);
  return client;
}

async function createHttpClient(config: ServerConfig): Promise<Client> {
  if (!config.url) {
    throw new Error(`Server ${config.id} has http transport but no url specified`);
  }

  const transport = new StreamableHTTPClientTransport(new URL(config.url));

  const client = new Client(
    {
      name: 'mcp-broker',
      version: '1.0.0',
    },
    {
      capabilities: {},
    }
  );

  await client.connect(transport);
  return client;
}

async function getOrCreateClient(config: ServerConfig): Promise<Client> {
  let client = upstreamClients.get(config.id);

  if (!client) {
    if (config.transport === 'stdio') {
      client = await createStdioClient(config);
    } else if (config.transport === 'http') {
      client = await createHttpClient(config);
    } else {
      throw new Error(`Unknown transport type: ${config.transport}`);
    }
    upstreamClients.set(config.id, client);
  }

  return client;
}

export async function callUpstreamTool(
  config: ServerConfig,
  toolName: string,
  args: Record<string, unknown>
): Promise<any> {
  const client = await getOrCreateClient(config);
  return await client.callTool({ name: toolName, arguments: args });
}

export async function listUpstreamTools(config: ServerConfig): Promise<any[]> {
  if (toolsCache.has(config.id)) {
    return toolsCache.get(config.id)!;
  }

  const client = await getOrCreateClient(config);
  const result = await client.listTools();
  const tools = result.tools || [];

  toolsCache.set(config.id, tools);
  return tools;
}

export function getCachedTools(serverId: string): any[] | undefined {
  return toolsCache.get(serverId);
}

export function isServerConnected(serverId: string): boolean {
  return upstreamClients.has(serverId);
}

export function disconnectAll(): void {
  for (const [id, client] of upstreamClients.entries()) {
    try {
      client.close();
    } catch (error) {
      console.error(`Error closing client ${id}:`, error);
    }
  }
  upstreamClients.clear();
  toolsCache.clear();
}
