import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';
import { AjvJsonSchemaValidator } from '@modelcontextprotocol/sdk/validation/ajv-provider.js';
import type { JsonSchemaValidator } from '@modelcontextprotocol/sdk/validation/types.js';
import { ErrorCode, McpError } from '@modelcontextprotocol/sdk/types.js';
import type { ServerConfig } from './config.js';
import { getOAuthToken } from './oauth.js';

const upstreamClients = new Map<string, Client>();
const toolsCache = new Map<string, any[]>();
const outputValidators = new Map<string, JsonSchemaValidator<unknown>>();

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

  // Build transport options
  const transportOptions: any = {};

  // Get OAuth token if configured
  if (config.oauth) {
    try {
      const token = await getOAuthToken(config.id, config.url, config.oauth);
      transportOptions.requestInit = {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      };
    } catch (error) {
      console.error(`OAuth failed for ${config.id}: ${error}`);
      throw error;
    }
  }

  const transport = new StreamableHTTPClientTransport(
    new URL(config.url),
    transportOptions
  );

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

async function createSseClient(config: ServerConfig): Promise<Client> {
  if (!config.url) {
    throw new Error(`Server ${config.id} has sse transport but no url specified`);
  }

  const transport = new SSEClientTransport(new URL(config.url));

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
    } else if (config.transport === 'sse') {
      client = await createSseClient(config);
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
  const result = await client.callTool({ name: toolName, arguments: args });
  const schema = toolsCache.get(config.id)?.find((tool) => tool.name === toolName)?.outputSchema;
  if (schema) {
    if (!result.structuredContent && !result.isError) {
      throw new McpError(ErrorCode.InvalidRequest, `Tool ${toolName} has an output schema but did not return structured content`);
    }
    if (result.structuredContent) {
      const key = JSON.stringify([config.id, toolName]);
      let validator = outputValidators.get(key);
      if (!validator) {
        validator = new AjvJsonSchemaValidator().getValidator(schema);
        outputValidators.set(key, validator);
      }
      const validation = validator(result.structuredContent);
      if (!validation.valid) {
        throw new McpError(ErrorCode.InvalidParams, `Structured content does not match the tool's output schema: ${validation.errorMessage}`);
      }
    }
  }
  return result;
}

export async function listUpstreamTools(config: ServerConfig): Promise<any[]> {
  if (toolsCache.has(config.id)) {
    return toolsCache.get(config.id)!;
  }

  const client = await getOrCreateClient(config);
  const tools: any[] = [];
  const cursors = new Set<string>();
  let cursor: string | undefined;
  do {
    const result = await client.listTools(cursor ? { cursor } : undefined);
    tools.push(...result.tools);
    cursor = result.nextCursor;
    if (cursor) {
      if (cursors.has(cursor)) throw new Error(`Repeated tools/list cursor from ${config.id}`);
      cursors.add(cursor);
    }
  } while (cursor);

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
  outputValidators.clear();
}
