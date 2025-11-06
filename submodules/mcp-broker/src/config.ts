import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { z } from 'zod';
import { createSecretResolver } from './secrets.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const secretResolver = createSecretResolver();

const ServerConfigSchema = z.object({
  id: z.string(),
  transport: z.enum(['stdio', 'http']),
  command: z.string().optional(),
  args: z.array(z.string()).optional(),
  url: z.string().optional(),
  env: z.record(z.string()).default({}),
  startMode: z.enum(['eager', 'lazy']).default('lazy'),
});

const ServersConfigSchema = z.object({
  servers: z.array(ServerConfigSchema),
});

const ToolRegistryEntrySchema = z.object({
  name: z.string(),
  server: z.string(),
  title: z.string().optional(),
  description: z.string().optional(),
  requireSchema: z.boolean().default(false),
});

const ToolsRegistrySchema = z.object({
  tools: z.array(ToolRegistryEntrySchema),
});

export type ServerConfig = z.infer<typeof ServerConfigSchema>;
export type ServersConfig = z.infer<typeof ServersConfigSchema>;
export type ToolRegistryEntry = z.infer<typeof ToolRegistryEntrySchema>;
export type ToolsRegistry = z.infer<typeof ToolsRegistrySchema>;

export async function loadServersConfig(): Promise<ServersConfig> {
  const configPath = join(__dirname, '..', 'servers.config.json');
  try {
    const raw = readFileSync(configPath, 'utf-8');
    const parsed = JSON.parse(raw);
    const expanded = await secretResolver.resolveObject(parsed);
    return ServersConfigSchema.parse(expanded);
  } catch (error) {
    if ((error as any).code === 'ENOENT') {
      return { servers: [] };
    }
    throw error;
  }
}

export function loadToolsRegistry(): ToolsRegistry {
  const registryPath = join(__dirname, '..', 'tools.registry.json');
  try {
    const raw = readFileSync(registryPath, 'utf-8');
    const parsed = JSON.parse(raw);
    return ToolsRegistrySchema.parse(parsed);
  } catch (error) {
    if ((error as any).code === 'ENOENT') {
      return { tools: [] };
    }
    throw error;
  }
}
