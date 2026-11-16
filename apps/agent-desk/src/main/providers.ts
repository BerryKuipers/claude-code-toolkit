import { z } from 'zod';
import type { ModelCatalog, ModelInfo, ProviderProfile, ProviderStatus } from '../shared/types';
import { validateProfileCompatibility } from './launch-plan';

const agents = ['claude', 'codex', 'gemini', 'antigravity'] as const;
const secretName = /(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTHORIZATION)/i;
const secretValue = /(?:sk-(?:or-|ant-)?[A-Za-z0-9_-]{12,}|-----BEGIN .*PRIVATE KEY-----)/;
const envSchema = z.record(z.string().regex(/^[A-Za-z_][A-Za-z0-9_]*$/), z.string().max(4096));

const profileSchema = z.object({
  id: z.string().regex(/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/),
  name: z.string().trim().min(1).max(100),
  agent: z.enum(agents),
  provider: z.enum(['native', 'local-proxy', 'openrouter', 'deepseek', 'custom']),
  route: z.enum(['native', 'anthropic', 'openai-responses', 'gemini']),
  baseUrl: z.string().max(2048).optional(),
  model: z.string().max(200).optional(),
  smallModel: z.string().max(200).optional(),
  subagentModel: z.string().max(200).optional(),
  effort: z.string().max(32).optional(),
  apiKeyEnv: z
    .string()
    .regex(/^[A-Za-z_][A-Za-z0-9_]*$/)
    .optional(),
  authMode: z.enum(['bearer', 'api-key']).optional(),
  settingsFile: z.string().max(4096).optional(),
  contextWindow: z.number().int().min(1024).max(100_000_000).optional(),
  env: envSchema,
  hasSecret: z.boolean().optional(),
});

export function endpoint(value: string): URL {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error('Enter a complete HTTP or HTTPS endpoint URL.');
  }
  if (
    !['http:', 'https:'].includes(url.protocol) ||
    url.username ||
    url.password ||
    url.search ||
    url.hash
  ) {
    throw new Error(
      'Endpoints must use HTTP or HTTPS without credentials, a query, or a fragment.',
    );
  }
  return url;
}

export function validateProfile(input: ProviderProfile): ProviderProfile {
  const profile = profileSchema.parse(input);
  delete profile.hasSecret;
  if (profile.baseUrl) profile.baseUrl = endpoint(profile.baseUrl).href.replace(/\/$/, '');
  if (profile.route !== 'native' && !profile.baseUrl)
    throw new Error('This route needs an endpoint URL.');
  if (profile.route === 'native' && profile.provider !== 'native')
    throw new Error('Choose an API route for a non-native provider.');
  if (profile.agent === 'claude' && !['native', 'anthropic'].includes(profile.route))
    throw new Error('Claude Code requires an Anthropic-compatible route.');
  if (profile.agent === 'codex' && !['native', 'openai-responses'].includes(profile.route))
    throw new Error('Codex requires a Responses-compatible route.');
  if (
    ['gemini', 'antigravity'].includes(profile.agent) &&
    !['native', 'gemini'].includes(profile.route)
  )
    throw new Error('This agent does not support the selected API protocol.');
  validateProfileCompatibility(profile);
  if (Object.keys(profile.env).length > 100)
    throw new Error('A profile may contain at most 100 extra environment settings.');
  for (const [name, value] of Object.entries(profile.env)) {
    if (/^(?:CLAUDE_CONFIG_DIR|CODEX_HOME|GEMINI_CLI_HOME)$/i.test(name))
      throw new Error(
        'Agent home overrides belong to the app environment, not individual profiles, so resumed sessions keep their original history store.',
      );
    if (
      /^(?:NODE_OPTIONS|ELECTRON_|LD_|DYLD_|PATH$|PATHEXT$|HOME$|USERPROFILE$|SHELL$|COMSPEC$|BASH_ENV$|ENV$)/i.test(
        name,
      )
    )
      throw new Error(
        'Runtime, shell, and executable search environment variables cannot be overridden in a launch profile.',
      );
    if ((secretName.test(name) && value !== '') || secretValue.test(value)) {
      throw new Error(
        'Use the API key field or an environment variable reference for credentials, not extra environment settings.',
      );
    }
    if (value.includes('\0') || name === '__proto__')
      throw new Error('Invalid environment setting.');
  }
  for (const value of [
    profile.name,
    profile.baseUrl,
    profile.model,
    profile.smallModel,
    profile.subagentModel,
    profile.effort,
    profile.settingsFile,
  ]) {
    if (value && (value.includes('\0') || secretValue.test(value)))
      throw new Error('Profile fields must not contain credentials or null characters.');
  }
  return profile;
}

export function defaultProfiles(): ProviderProfile[] {
  return [
    {
      id: 'claude-native',
      name: 'Claude · native configuration',
      agent: 'claude',
      provider: 'native',
      route: 'native',
      env: {},
    },
    {
      id: 'codex-native',
      name: 'Codex · native configuration',
      agent: 'codex',
      provider: 'native',
      route: 'native',
      env: {},
    },
    {
      id: 'gemini-native',
      name: 'Gemini · native',
      agent: 'gemini',
      provider: 'native',
      route: 'native',
      env: {},
    },
    {
      id: 'antigravity-native',
      name: 'Antigravity · native',
      agent: 'antigravity',
      provider: 'native',
      route: 'native',
      env: {},
    },
    {
      id: 'claude-local-proxy',
      name: 'Claude · local proxy',
      agent: 'claude',
      provider: 'local-proxy',
      route: 'anthropic',
      baseUrl: 'http://127.0.0.1:18765',
      authMode: 'bearer',
      env: {
        CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1',
        CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK: '1',
        CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY: '1',
      },
    },
    {
      id: 'claude-openrouter',
      name: 'Claude · OpenRouter',
      agent: 'claude',
      provider: 'openrouter',
      route: 'anthropic',
      baseUrl: 'https://openrouter.ai/api',
      apiKeyEnv: 'OPENROUTER_API_KEY',
      authMode: 'bearer',
      env: { CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY: '1' },
    },
    {
      id: 'claude-deepseek',
      name: 'Claude · DeepSeek',
      agent: 'claude',
      provider: 'deepseek',
      route: 'anthropic',
      baseUrl: 'https://api.deepseek.com/anthropic',
      apiKeyEnv: 'DEEPSEEK_API_KEY',
      authMode: 'bearer',
      env: {},
    },
  ];
}

export interface ProviderDependencies {
  secretValue?: (id: string) => Promise<string | undefined>;
  fetch?: typeof fetch;
  timeoutMs?: number;
}

export class ProviderService {
  constructor(private readonly dependencies: ProviderDependencies = {}) {}

  private async key(profile: ProviderProfile): Promise<string | undefined> {
    return (
      (await this.dependencies.secretValue?.(profile.id)) ||
      (profile.apiKeyEnv ? process.env[profile.apiKeyEnv] : undefined)
    );
  }

  private async request(
    url: string,
    profile: ProviderProfile,
    options: { public?: boolean; forceBearer?: boolean } = {},
  ): Promise<unknown> {
    endpoint(url);
    const secret = options.public ? undefined : await this.key(profile);
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (secret) {
      if (profile.route === 'gemini') headers['x-goog-api-key'] = secret;
      else if (profile.authMode === 'api-key' && !options.forceBearer)
        headers['x-api-key'] = secret;
      else headers.Authorization = `Bearer ${secret}`;
    }
    if (profile.route === 'anthropic') headers['anthropic-version'] = '2023-06-01';
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.dependencies.timeoutMs ?? 10_000);
    let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
    try {
      const response = await (this.dependencies.fetch ?? fetch)(url, {
        method: 'GET',
        headers,
        signal: controller.signal,
        redirect: 'error',
      });
      if (!response.ok)
        throw new Error(
          response.status === 401 || response.status === 403
            ? `Authentication was rejected (HTTP ${response.status}). Check the selected endpoint and API key.`
            : `Endpoint returned HTTP ${response.status}.`,
        );
      if (Number(response.headers.get('content-length') ?? 0) > 4 * 1024 * 1024)
        throw new Error('Model catalogue response is too large.');
      if (!response.body) throw new Error('Endpoint returned an empty response.');
      reader = response.body.getReader();
      const chunks: Uint8Array[] = [];
      let length = 0;
      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        length += chunk.value.byteLength;
        if (length > 4 * 1024 * 1024) throw new Error('Endpoint response is too large.');
        chunks.push(chunk.value);
      }
      try {
        return JSON.parse(Buffer.concat(chunks).toString('utf8'));
      } catch {
        throw new Error('Endpoint returned invalid JSON.');
      }
    } catch (error) {
      if (controller.signal.aborted)
        throw new Error('Endpoint did not respond within the timeout.');
      if (error instanceof TypeError)
        throw new Error(
          'Could not connect to this endpoint. Check the address and connection. Redirects are not followed.',
        );
      throw error;
    } finally {
      clearTimeout(timeout);
      await reader?.cancel().catch(() => undefined);
    }
  }

  catalogUrl(profile: ProviderProfile): string {
    const url = endpoint(profile.baseUrl ?? '');
    if (profile.provider === 'openrouter' && url.hostname === 'openrouter.ai')
      return `${url.origin}/api/v1/models`;
    if (profile.provider === 'deepseek' && url.hostname === 'api.deepseek.com')
      return `${url.origin}/models`;
    const base = url.href.replace(/\/$/, '');
    return /\/v\d+(?:beta)?$/.test(base) ? `${base}/models` : `${base}/v1/models`;
  }

  async models(profile: ProviderProfile): Promise<ModelCatalog> {
    const started = Date.now();
    if (profile.route === 'native') {
      return {
        models: [],
        source: 'Native CLI',
        verifiedAt: new Date().toISOString(),
        latencyMs: 0,
        warnings: [
          'Native profiles use the installed CLI’s model picker, configuration and environment. Its provider can be a subscription, direct API or gateway. A model ID can still be saved in this profile.',
        ],
      };
    }
    const source = this.catalogUrl(profile);
    const publicCatalogue =
      profile.provider === 'openrouter' && new URL(source).hostname === 'openrouter.ai';
    const response = await this.request(source, profile, {
      public: publicCatalogue,
      forceBearer: profile.provider === 'deepseek',
    });
    if (!response || typeof response !== 'object')
      throw new Error('Endpoint did not return a model catalogue.');
    const data = response as { data?: unknown[]; models?: unknown[]; has_more?: boolean };
    const entries = data.data ?? data.models;
    if (!Array.isArray(entries))
      throw new Error('Endpoint did not return a supported model catalogue.');
    const models = entries.slice(0, 5000).flatMap((raw): ModelInfo[] => {
      if (!raw || typeof raw !== 'object') return [];
      const model = raw as Record<string, unknown>;
      const id =
        typeof model.id === 'string'
          ? model.id
          : typeof model.name === 'string'
            ? model.name.replace(/^models\//, '')
            : undefined;
      if (!id || id.length > 300) return [];
      const context = Number(model.context_length ?? model.context_window ?? model.inputTokenLimit);
      const pricing =
        model.pricing && typeof model.pricing === 'object'
          ? (model.pricing as Record<string, unknown>)
          : {};
      const input = pricing.prompt === undefined ? undefined : Number(pricing.prompt);
      const output = pricing.completion === undefined ? undefined : Number(pricing.completion);
      return [
        {
          id,
          name: String(model.display_name ?? model.displayName ?? model.name ?? id).slice(0, 300),
          ...(context > 0 && Number.isFinite(context) ? { contextWindow: context } : {}),
          ...(input !== undefined && Number.isFinite(input) && input >= 0
            ? { inputPrice: input * 1_000_000 }
            : {}),
          ...(output !== undefined && Number.isFinite(output) && output >= 0
            ? { outputPrice: output * 1_000_000 }
            : {}),
          ...(input !== undefined && output !== undefined
            ? { free: input === 0 && output === 0 }
            : {}),
        },
      ];
    });
    const warnings: string[] = [];
    if (data.has_more || entries.length > 5000)
      warnings.push(
        'The endpoint returned a partial catalogue. You can enter an exact model ID manually.',
      );
    if (publicCatalogue)
      warnings.push(
        'OpenRouter’s public catalogue is not proof of tool compatibility or access on your account. Prices shown are per million tokens.',
      );
    return {
      models: [...new Map(models.map((model) => [model.id, model])).values()],
      source,
      verifiedAt: new Date().toISOString(),
      latencyMs: Date.now() - started,
      warnings,
    };
  }

  async probe(profile: ProviderProfile): Promise<ProviderStatus> {
    const started = Date.now();
    try {
      if (profile.route === 'native')
        return {
          ok: false,
          message:
            'Native profiles inherit the installed CLI’s configuration, provider and authentication. Open the agent and use its account/status command to verify access.',
          latencyMs: 0,
          checkedAt: new Date().toISOString(),
        };
      const base = endpoint(profile.baseUrl!);
      if (profile.provider === 'local-proxy') {
        const payload = await this.request(
          `${base.origin}${base.pathname.replace(/\/$/, '')}/healthz`,
          profile,
          { public: true },
        );
        if (!payload || typeof payload !== 'object' || !(payload as { ok?: boolean }).ok)
          throw new Error('The proxy did not return a successful health check.');
        return {
          ok: true,
          message: 'Proxy is running. This liveness check does not verify its upstream accounts.',
          latencyMs: Date.now() - started,
          checkedAt: new Date().toISOString(),
        };
      }
      if (profile.provider === 'openrouter' && base.hostname === 'openrouter.ai') {
        if (!(await this.key(profile)))
          throw new Error(
            'Add an API key or set its environment variable before testing authenticated access.',
          );
        const response = await this.request(`${base.origin}/api/v1/key`, profile, {
          forceBearer: true,
        });
        if (!response || typeof response !== 'object' || !('data' in response))
          throw new Error('The endpoint returned an unexpected account response.');
        return {
          ok: true,
          message: 'OpenRouter accepted this API key. No generation was requested.',
          latencyMs: Date.now() - started,
          checkedAt: new Date().toISOString(),
        };
      }
      const catalog = await this.models(profile);
      return {
        ok: true,
        message:
          'The model catalogue responded. A generation was not requested; model access and tool compatibility can still differ.',
        modelCount: catalog.models.length,
        latencyMs: Date.now() - started,
        checkedAt: new Date().toISOString(),
      };
    } catch (error) {
      return {
        ok: false,
        message: error instanceof Error ? error.message : 'Connection failed.',
        latencyMs: Date.now() - started,
        checkedAt: new Date().toISOString(),
      };
    }
  }

  async proxyMonitor(profile: ProviderProfile): Promise<unknown> {
    if (profile.provider !== 'local-proxy')
      throw new Error('The monitor is available for a local proxy profile.');
    const url = endpoint(profile.baseUrl!);
    return this.request(`${url.origin}${url.pathname.replace(/\/$/, '')}/monitor`, profile, {
      public: true,
    });
  }
}
