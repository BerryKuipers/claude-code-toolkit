import type { AgentId, LaunchRequest, ProviderProfile, SessionRecord } from '../shared/types';

export interface LaunchPlan {
  args: string[];
  env: Record<string, string>;
  cwd: string;
}

const CLAUDE_ROUTE_ENV = [
  'ANTHROPIC_BASE_URL',
  'ANTHROPIC_AUTH_TOKEN',
  'ANTHROPIC_MODEL',
  'ANTHROPIC_DEFAULT_OPUS_MODEL',
  'ANTHROPIC_DEFAULT_SONNET_MODEL',
  'ANTHROPIC_DEFAULT_HAIKU_MODEL',
  'ANTHROPIC_SMALL_FAST_MODEL',
  'CLAUDE_CODE_SUBAGENT_MODEL',
  'CLAUDE_CODE_MAX_CONTEXT_TOKENS',
  'CLAUDE_CODE_AUTO_COMPACT_WINDOW',
  'CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK',
  'CLAUDE_PROVIDER',
  'CLAUDE_PROXY_ACTIVE',
  'CLAUDE_PROXY_URL',
];

const BLOCKED_ENV =
  /^(?:NODE_OPTIONS|ELECTRON_.+|LD_.+|DYLD_.+|BASH_ENV|ENV|COMSPEC|SHELL|PATH|PATHEXT|HOME|USERPROFILE|CLAUDE_CONFIG_DIR|CODEX_HOME|GEMINI_CLI_HOME)$/i;

export function validateProfileCompatibility(profile: ProviderProfile): void {
  const allowed: Record<AgentId, ProviderProfile['route'][]> = {
    claude: ['native', 'anthropic'],
    codex: ['native', 'openai-responses'],
    gemini: ['native', 'gemini'],
    antigravity: ['native', 'gemini'],
  };
  if (!allowed[profile.agent].includes(profile.route))
    throw new Error(
      `${profile.agent} cannot use the ${profile.route} protocol. Choose a compatible connection.`,
    );
  if (profile.route !== 'native') {
    if (!profile.baseUrl) throw new Error('This connection needs a base URL.');
    const url = new URL(profile.baseUrl);
    if (
      !['http:', 'https:'].includes(url.protocol) ||
      url.username ||
      url.password ||
      url.hash ||
      url.search
    )
      throw new Error('Use an HTTP(S) base URL without embedded credentials, query or fragment.');
    if (
      url.protocol === 'http:' &&
      !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname) &&
      profile.provider !== 'custom'
    )
      throw new Error(
        'Remote provider connections require HTTPS. Select Custom only for an intentional private-network endpoint.',
      );
  }
}

export function buildLaunchPlan(
  request: LaunchRequest,
  profile: ProviderProfile,
  parentEnv: NodeJS.ProcessEnv,
  secret?: string,
  session?: SessionRecord,
): LaunchPlan {
  validateProfileCompatibility(profile);
  if (request.agent !== profile.agent)
    throw new Error('The selected profile belongs to a different agent.');
  if (request.sessionId && (!session || session.agent !== request.agent))
    throw new Error(
      'The selected session no longer exists for this agent. Refresh the session list.',
    );
  if (session && !session.resumable)
    throw new Error(session.resumeNote ?? 'This session cannot be resumed directly.');
  if (
    session &&
    (!session.nativeId ||
      session.nativeId.startsWith('-') ||
      /[\x00-\x1f\x7f]/.test(session.nativeId) ||
      session.nativeId.length > 512)
  )
    throw new Error('This session has an invalid native identifier.');
  const env: Record<string, string> = {};
  for (const [key, value] of Object.entries(parentEnv))
    if (typeof value === 'string' && !key.startsWith('ELECTRON_')) env[key] = value;
  delete env.NODE_OPTIONS;
  delete env.CLAUDECODE;
  delete env.CLAUDE_CODE_ENTRYPOINT;
  delete env.AGENT_DESK_API_KEY;
  if (request.agent === 'claude' && profile.route !== 'native') {
    for (const key of CLAUDE_ROUTE_ENV) delete env[key];
    delete env.ANTHROPIC_API_KEY;
  } else if (
    (request.agent === 'gemini' || request.agent === 'antigravity') &&
    profile.route !== 'native'
  ) {
    delete env.GOOGLE_GEMINI_BASE_URL;
    delete env.GEMINI_API_KEY;
    delete env.GOOGLE_API_KEY;
  }
  for (const [key, value] of Object.entries(profile.env)) {
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(key) || BLOCKED_ENV.test(key))
      throw new Error(`The environment variable '${key}' cannot be set by a profile.`);
    if (value.includes('\0'))
      throw new Error(`The environment variable '${key}' contains an invalid character.`);
    env[key] = value;
  }
  const key = secret || (profile.apiKeyEnv ? parentEnv[profile.apiKeyEnv] : undefined);
  const args: string[] = [];
  const cwd = session?.projectPath || request.projectPath;
  if (!cwd || cwd.includes('\0'))
    throw new Error('Choose a project folder before starting a session.');
  if (request.agent === 'claude') {
    if (session) args.push('--resume', session.nativeId);
    if (profile.model) args.push('--model', profile.model);
    if (profile.effort) args.push('--effort', profile.effort);
    if (profile.settingsFile) args.push('--settings', profile.settingsFile);
    if (profile.route === 'anthropic') {
      env.ANTHROPIC_BASE_URL = profile.baseUrl!;
      env.ANTHROPIC_API_KEY = profile.authMode === 'api-key' ? (key ?? '') : '';
      env.ANTHROPIC_AUTH_TOKEN =
        profile.authMode === 'api-key'
          ? ''
          : (key ?? (profile.provider === 'local-proxy' ? 'unused' : ''));
      if (!key && profile.provider !== 'local-proxy')
        throw new Error(
          'Add an API key or set the API key environment variable for this connection.',
        );
      env.CLAUDE_PROVIDER = profile.provider;
      env.CLAUDE_PROXY_ACTIVE = '1';
      env.CLAUDE_PROXY_URL = profile.baseUrl!;
      env.CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = '1';
      env.CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK = '1';
      if (profile.model) {
        env.ANTHROPIC_MODEL = profile.model;
        env.ANTHROPIC_DEFAULT_OPUS_MODEL = profile.model;
        env.ANTHROPIC_DEFAULT_SONNET_MODEL = profile.model;
      }
    } else {
      if (key) env.ANTHROPIC_API_KEY = key;
    }
    if (profile.smallModel) {
      env.ANTHROPIC_DEFAULT_HAIKU_MODEL = profile.smallModel;
      env.ANTHROPIC_SMALL_FAST_MODEL = profile.smallModel;
    }
    if (profile.subagentModel) env.CLAUDE_CODE_SUBAGENT_MODEL = profile.subagentModel;
    if (profile.contextWindow) env.CLAUDE_CODE_MAX_CONTEXT_TOKENS = String(profile.contextWindow);
    if (request.prompt) args.push('--', request.prompt);
  } else if (request.agent === 'codex') {
    if (session) args.push('resume', session.nativeId);
    if (profile.model) args.push('-m', profile.model);
    if (profile.effort) args.push('-c', `model_reasoning_effort=${JSON.stringify(profile.effort)}`);
    if (profile.route === 'openai-responses') {
      env.AGENT_DESK_API_KEY = key ?? '';
      args.push(
        '-c',
        'model_provider="agent_desk"',
        '-c',
        'model_providers.agent_desk.name="Agent Desk"',
        '-c',
        `model_providers.agent_desk.base_url=${JSON.stringify(profile.baseUrl)}`,
        '-c',
        'model_providers.agent_desk.wire_api="responses"',
      );
      if (key) args.push('-c', 'model_providers.agent_desk.env_key="AGENT_DESK_API_KEY"');
    }
    if (request.prompt) args.push('--', request.prompt);
  } else {
    if (session)
      args.push(request.agent === 'gemini' ? '--resume' : '--conversation', session.nativeId);
    if (profile.model) args.push('--model', profile.model);
    if (profile.effort && request.agent === 'antigravity') args.push('--effort', profile.effort);
    if (profile.route === 'gemini') {
      env.GOOGLE_GEMINI_BASE_URL = profile.baseUrl!;
      if (!key) throw new Error('This Gemini-compatible connection needs an API key.');
      env.GEMINI_API_KEY = key;
    }
    if (request.prompt)
      args.push(
        request.agent === 'gemini' ? `--prompt-interactive=${request.prompt}` : '-i',
        ...(request.agent === 'antigravity' ? [request.prompt] : []),
      );
  }
  env.TERM = 'xterm-256color';
  env.COLORTERM = 'truecolor';
  return { args, env, cwd };
}
