import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

const server = new Server({ name: 'discovery-fixture', version: '1.0.0' }, { capabilities: { tools: {} } });
const tools = [
  {
    name: 'first', description: 'First page', inputSchema: { type: 'object', properties: {} },
    outputSchema: { type: 'object', properties: { value: { type: 'number' } }, required: ['value'] },
  },
  {
    name: 'filtered_rows',
    description: 'Read matching rows',
    inputSchema: {
      type: 'object',
      properties: { status: { type: 'string', enum: ['pending', 'done'] }, limit: { type: 'integer', minimum: 1, maximum: 1000 } },
      required: ['status', 'limit'],
    },
    outputSchema: { type: 'object', properties: { rows: { type: 'array' } } },
    annotations: { readOnlyHint: true },
  },
];
server.setRequestHandler(ListToolsRequestSchema, async ({ params }) => params?.cursor === 'next'
  ? { tools: tools.slice(1), ...(process.argv.includes('--cycle') ? { nextCursor: 'next' } : {}) }
  : { tools: tools.slice(0, 1), nextCursor: 'next' });
server.setRequestHandler(CallToolRequestSchema, async ({ params }) => {
  if (params.name === 'first') {
    const scenario = params.arguments?.scenario;
    return {
      content: [{ type: 'text', text: 'Fixture result' }],
      ...(scenario === 'missing' || scenario === 'error' ? {} : { structuredContent: { value: scenario === 'invalid' || scenario === 'invalid-error' ? 'not-a-number' : 42 } }),
      isError: scenario === 'error' || scenario === 'invalid-error',
    };
  }
  return {
    content: [{ type: 'text', text: JSON.stringify({ received: params.arguments, rows: Array.from({ length: 1000 }, (_, id) => ({ id })) }) }],
    isError: params.arguments?.status === 'done',
  };
});
await server.connect(new StdioServerTransport());
