import { z } from 'zod';

const text = z
  .string()
  .max(32768)
  .refine((value) => !value.includes('\0'), 'Null bytes are not allowed.');
const identifier = z
  .string()
  .min(1)
  .max(512)
  .refine((value) => !value.includes('\0'));
const agent = z.enum(['claude', 'codex', 'gemini', 'antigravity']);

export const settingsSchema = z
  .object({
    theme: z.enum(['system', 'light', 'dark']),
    fontSize: z.number().int().min(10).max(28),
    terminalScrollback: z.number().int().min(100).max(100000),
    defaultProfileId: identifier,
    projects: z.array(text).max(100),
    historyRoots: z.array(z.object({ id: identifier, agent, path: text }).strict()).max(60),
    skillDirectories: z.array(text).max(60),
    agentCommands: z
      .object({ claude: text, codex: text, gemini: text, antigravity: text })
      .strict(),
    proxyCommand: text,
    scanOnStart: z.boolean(),
    autoRefreshSeconds: z.number().int().min(0).max(3600),
  })
  .strict();

export const profileSchema = z
  .object({
    id: z.string().regex(/^[A-Za-z0-9_-]{1,120}$/),
    name: z.string().min(1).max(160),
    agent,
    provider: z.enum(['native', 'local-proxy', 'openrouter', 'deepseek', 'custom']),
    route: z.enum(['native', 'anthropic', 'openai-responses', 'gemini']),
    baseUrl: text.optional(),
    model: text.optional(),
    smallModel: text.optional(),
    subagentModel: text.optional(),
    effort: z.string().max(60).optional(),
    apiKeyEnv: z.string().max(160).optional(),
    authMode: z.enum(['bearer', 'api-key']).optional(),
    settingsFile: text.optional(),
    contextWindow: z.number().int().min(1024).max(10000000).optional(),
    env: z
      .record(z.string(), z.string().max(4096))
      .refine((value) => Object.keys(value).length <= 80),
    hasSecret: z.boolean().optional(),
  })
  .strict();

export const launchSchema = z
  .object({
    agent,
    projectPath: text,
    profileId: identifier.optional(),
    sessionId: identifier.optional(),
    prompt: z
      .string()
      .max(200000)
      .refine((value) => !value.includes('\0'))
      .optional(),
  })
  .strict();

export const ipcSchemas = {
  none: z.tuple([]),
  id: z.tuple([identifier]),
  edit: z.tuple([
    z.object({ id: identifier, content: z.string().max(2000000), revision: identifier }).strict(),
  ]),
  skillCreate: z.tuple([
    z
      .object({
        rootId: identifier,
        name: z.string().min(1).max(120),
        content: z.string().max(2000000),
      })
      .strict(),
  ]),
  skillToggle: z.tuple([z.object({ id: identifier, enabled: z.boolean() }).strict()]),
  secret: z.tuple([
    z
      .object({ profileId: identifier, secret: z.string().max(16384), persist: z.boolean() })
      .strict(),
  ]),
  text: z.tuple([text]),
  terminalInput: z.tuple([identifier, z.string().max(1000000)]),
  resize: z.tuple([identifier, z.number().int().min(2).max(600), z.number().int().min(1).max(300)]),
};
