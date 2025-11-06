import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { z } from 'zod';
import { createSecretResolver } from './secrets.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const secretResolver = createSecretResolver();

const OAuthConfigSchema = z.object({
  authorizationUrl: z.string().optional(),
  tokenUrl: z.string().optional(),
  clientId: z.string().optional(),
  clientSecret: z.string().optional(),
  scopes: z.array(z.string()).optional().default([]),
  redirectUri: z.string().optional().default('http://localhost:45454/oauth/callback'),
});

const ServerConfigSchema = z.object({
  id: z.string(),
  transport: z.enum(['stdio', 'http']),
  command: z.string().optional(),
  args: z.array(z.string()).optional(),
  url: z.string().optional(),
  env: z.record(z.string()).default({}),
  startMode: z.enum(['eager', 'lazy']).default('lazy'),
  oauth: OAuthConfigSchema.optional(),
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

const ToolOverrideSchema = z.object({
  name: z.string(),
  server: z.string(),
  title: z.string().optional(),
  description: z.string().optional(),
});

const ToolOverridesSchema = z.object({
  overrides: z.array(ToolOverrideSchema),
});

export type OAuthConfig = z.infer<typeof OAuthConfigSchema>;
export type ServerConfig = z.infer<typeof ServerConfigSchema>;
export type ServersConfig = z.infer<typeof ServersConfigSchema>;
export type ToolRegistryEntry = z.infer<typeof ToolRegistryEntrySchema>;
export type ToolsRegistry = z.infer<typeof ToolsRegistrySchema>;
export type ToolOverride = z.infer<typeof ToolOverrideSchema>;
export type ToolOverrides = z.infer<typeof ToolOverridesSchema>;

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

export function loadToolOverrides(): ToolOverrides {
  const overridesPath = join(__dirname, '..', 'tools.overrides.json');
  try {
    const raw = readFileSync(overridesPath, 'utf-8');
    const parsed = JSON.parse(raw);
    return ToolOverridesSchema.parse(parsed);
  } catch (error) {
    if ((error as any).code === 'ENOENT') {
      return { overrides: [] };
    }
    throw error;
  }
}
