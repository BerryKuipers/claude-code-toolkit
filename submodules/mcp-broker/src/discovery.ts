import type { Tool } from '@modelcontextprotocol/sdk/types.js';
import type { ServerConfig, ToolRegistryEntry, ToolOverride } from './config.js';
import { getCachedTools, listUpstreamTools } from './upstream.js';

export const describeTool: Tool = {
  name: 'broker.describe',
  description: 'Load one upstream tool definition, including its input schema, before invoking it',
  inputSchema: {
    type: 'object',
    properties: {
      server: { type: 'string', description: 'Server ID from broker.search' },
      tool: { type: 'string', description: 'Tool name from broker.search' },
    },
    required: ['server', 'tool'],
  },
};

type Summary = {
  server: string;
  name: string;
  title: string;
  description: string;
};

export async function searchTools(
  servers: ServerConfig[],
  entries: (ToolRegistryEntry | ToolOverride)[],
  args: Record<string, unknown> = {}
): Promise<{ content: { type: 'text'; text: string }[]; isError: boolean }> {
  if (args.q !== undefined && typeof args.q !== 'string') {
    throw new Error('broker.search q must be a string');
  }
  if (args.servers !== undefined && (!Array.isArray(args.servers) || !args.servers.every((id) => typeof id === 'string'))) {
    throw new Error('broker.search servers must be an array of server IDs');
  }
  const query = ((args.q as string | undefined) || '').toLowerCase();
  const filter = (args.servers as string[] | undefined) || [];
  const unknown = filter.filter((id) => !servers.some((server) => server.id === id));
  if (unknown.length) throw new Error(`Unknown server IDs: ${unknown.join(', ')}`);
  const results: Summary[] = [];
  const seen = new Set<string>();
  const failed: string[] = [];
  const add = (entry: Summary): void => {
    const key = JSON.stringify([entry.server, entry.name]);
    if (seen.has(key) || (filter.length && !filter.includes(entry.server))) return;
    if (query && !`${entry.name} ${entry.title} ${entry.description}`.toLowerCase().includes(query)) return;
    seen.add(key);
    results.push(entry);
  };
  for (const entry of entries) {
    add({ server: entry.server, name: entry.name, title: entry.title || entry.name, description: entry.description || '' });
  }
  for (const config of servers.filter((server) => !filter.length || filter.includes(server.id))) {
    try {
      const tools = getCachedTools(config.id) ?? await listUpstreamTools(config);
      for (const tool of tools) {
        add({ server: config.id, name: tool.name, title: tool.title || tool.name, description: tool.description || '' });
      }
    } catch {
      failed.push(config.id);
    }
  }
  const content: { type: 'text'; text: string }[] = [{ type: 'text', text: JSON.stringify(results) }];
  if (failed.length) {
    content.push({ type: 'text', text: `Incomplete discovery: could not list tools from ${failed.join(', ')}. Retry those servers before treating an absent tool as unavailable.` });
  }
  return { content, isError: failed.length > 0 && results.length === 0 };
}

export async function describeUpstreamTool(
  servers: ServerConfig[],
  args: Record<string, unknown> = {}
): Promise<{ content: { type: 'text'; text: string }[] }> {
  if (typeof args.server !== 'string' || typeof args.tool !== 'string' || !args.server || !args.tool) {
    throw new Error('broker.describe requires server and tool names');
  }
  const config = servers.find((server) => server.id === args.server);
  if (!config) throw new Error(`Server not found: ${args.server}`);
  const tools = getCachedTools(config.id) ?? await listUpstreamTools(config);
  const tool = tools.find((candidate) => candidate.name === args.tool);
  if (!tool) throw new Error(`Tool not found on ${config.id}: ${args.tool}`);
  return { content: [{ type: 'text', text: JSON.stringify({ ...tool, server: config.id }) }] };
}
