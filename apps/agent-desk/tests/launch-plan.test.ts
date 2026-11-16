import { describe, expect, it } from 'vitest';
import { buildLaunchPlan } from '../src/main/launch-plan';
import { npmShimTarget } from '../src/main/executables';
import type { LaunchRequest, ProviderProfile, SessionRecord } from '../src/shared/types';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

const native: ProviderProfile = {
  id: 'native',
  name: 'Native',
  agent: 'claude',
  provider: 'native',
  route: 'native',
  env: {},
};
const request: LaunchRequest = { agent: 'claude', projectPath: '/projects/with spaces' };
const session: SessionRecord = {
  id: 'claude:abc',
  nativeId: 'abc',
  agent: 'claude',
  title: 'Test',
  projectPath: '/project',
  projectName: 'project',
  createdAt: '',
  updatedAt: '',
  preview: '',
  messageCount: 0,
  sourceKind: 'cli',
  resumable: true,
};

describe('native launch plans', () => {
  it('preserves installed routing and credentials together for native configuration', () => {
    const parent = {
      ANTHROPIC_BASE_URL: 'http://old-proxy',
      ANTHROPIC_AUTH_TOKEN: 'old-key',
      ANTHROPIC_API_KEY: 'native-key',
      ANTHROPIC_MODEL: 'old-model',
      CLAUDE_PROXY_ACTIVE: '1',
      CLAUDECODE: '1',
      PATH: '/bin',
    };
    const plan = buildLaunchPlan(request, native, parent);
    expect(plan.env.ANTHROPIC_BASE_URL).toBe('http://old-proxy');
    expect(plan.env.ANTHROPIC_AUTH_TOKEN).toBe('old-key');
    expect(plan.env.ANTHROPIC_API_KEY).toBe('native-key');
    expect(plan.env.ANTHROPIC_MODEL).toBe('old-model');
    expect(plan.env.CLAUDE_PROXY_ACTIVE).toBe('1');
    expect(plan.env.CLAUDECODE).toBeUndefined();
    expect(parent.ANTHROPIC_BASE_URL).toBe('http://old-proxy');
    expect(plan.cwd).toBe('/projects/with spaces');
  });

  it('puts hostile prompt text in one argument, after the option delimiter', () => {
    const prompt = '--dangerously-skip-permissions; $(touch /tmp/unwanted)';
    const plan = buildLaunchPlan({ ...request, prompt }, native, {});
    expect(plan.args).toEqual(['--', prompt]);
  });

  it('resumes the native identifier in its real project', () => {
    const plan = buildLaunchPlan(
      { ...request, sessionId: session.id },
      native,
      {},
      undefined,
      session,
    );
    expect(plan.args).toEqual(['--resume', 'abc']);
    expect(plan.cwd).toBe('/project');
    expect(() => buildLaunchPlan({ ...request, sessionId: 'missing' }, native, {})).toThrow(
      /no longer exists/,
    );
  });

  it('does not add bypass or sandbox-changing flags', () => {
    for (const agent of ['claude', 'codex', 'gemini', 'antigravity'] as const) {
      const plan = buildLaunchPlan({ ...request, agent }, { ...native, agent }, {});
      expect(plan.args).toEqual([]);
    }
  });
});

describe('provider routing', () => {
  it('routes OpenRouter directly with bearer auth and blank native API key', () => {
    const profile: ProviderProfile = {
      ...native,
      provider: 'openrouter',
      route: 'anthropic',
      baseUrl: 'https://openrouter.ai/api',
      model: 'vendor/model',
      smallModel: 'vendor/small',
      effort: 'high',
      apiKeyEnv: 'OPENROUTER_API_KEY',
    };
    const plan = buildLaunchPlan(request, profile, {
      OPENROUTER_API_KEY: 'test-key',
      ANTHROPIC_API_KEY: 'stale',
    });
    expect(plan.env.ANTHROPIC_AUTH_TOKEN).toBe('test-key');
    expect(plan.env.ANTHROPIC_API_KEY).toBe('');
    expect(plan.env.ANTHROPIC_BASE_URL).toBe('https://openrouter.ai/api');
    expect(plan.env.ANTHROPIC_DEFAULT_HAIKU_MODEL).toBe('vendor/small');
    expect(plan.args).toEqual(['--model', 'vendor/model', '--effort', 'high']);
  });

  it('uses an ephemeral environment reference for Codex custom provider credentials', () => {
    const profile: ProviderProfile = {
      ...native,
      agent: 'codex',
      route: 'openai-responses',
      provider: 'custom',
      baseUrl: 'https://example.test/v1',
      model: 'model',
      effort: 'medium',
    };
    const plan = buildLaunchPlan({ ...request, agent: 'codex' }, profile, {}, 'test-secret');
    expect(plan.env.AGENT_DESK_API_KEY).toBe('test-secret');
    expect(plan.args.join(' ')).not.toContain('test-secret');
    expect(plan.args).toContain('model_providers.agent_desk.wire_api="responses"');
    expect(plan.args).toContain('model_reasoning_effort="medium"');
  });

  it('rejects incompatible routes, embedded credentials, and runtime injection', () => {
    expect(() =>
      buildLaunchPlan(
        request,
        { ...native, route: 'openai-responses', baseUrl: 'https://example.test' },
        {},
      ),
    ).toThrow(/cannot use/);
    expect(() =>
      buildLaunchPlan(
        request,
        { ...native, route: 'anthropic', baseUrl: 'https://key:secret@example.test' },
        {},
      ),
    ).toThrow(/embedded credentials/);
    expect(() =>
      buildLaunchPlan(request, { ...native, env: { NODE_OPTIONS: '--require evil.js' } }, {}),
    ).toThrow(/cannot be set/);
  });

  it('requires credentials for direct providers but not the local proxy', () => {
    const profile: ProviderProfile = {
      ...native,
      provider: 'deepseek',
      route: 'anthropic',
      baseUrl: 'https://api.deepseek.com/anthropic',
    };
    expect(() => buildLaunchPlan(request, profile, {})).toThrow(/API key/);
    const local = buildLaunchPlan(
      request,
      { ...profile, provider: 'local-proxy', baseUrl: 'http://127.0.0.1:18765' },
      {},
    );
    expect(local.env.ANTHROPIC_AUTH_TOKEN).toBe('unused');
  });

  it('keeps Gemini in interactive mode with an initial prompt', () => {
    const plan = buildLaunchPlan(
      { ...request, agent: 'gemini', prompt: 'review the code' },
      { ...native, agent: 'gemini' },
      {},
    );
    expect(plan.args).toEqual(['--prompt-interactive=review the code']);
  });

  it('blocks direct resume for Antigravity desktop sessions needing import', () => {
    expect(() =>
      buildLaunchPlan(
        { ...request, agent: 'antigravity', sessionId: 'desktop' },
        { ...native, agent: 'antigravity' },
        {},
        undefined,
        {
          ...session,
          agent: 'antigravity',
          resumable: false,
          resumeNote: 'Import using /resume → Other.',
        },
      ),
    ).toThrow(/Import/);
  });

  it('rejects native session identifiers that could be interpreted as flags', () => {
    expect(() =>
      buildLaunchPlan({ ...request, sessionId: 'bad' }, native, {}, undefined, {
        ...session,
        nativeId: '--dangerously-skip-permissions',
      }),
    ).toThrow(/invalid native identifier/);
  });
});

describe('Windows npm launchers', () => {
  it('extracts the real executable entry point without invoking cmd', () => {
    expect(
      npmShimTarget(
        '"%_prog%" "%dp0%\\node_modules\\@openai\\codex\\bin\\codex.js" %*',
        join(tmpdir(), 'bin', 'codex.cmd'),
      ),
    ).toBe(join(tmpdir(), 'bin', 'node_modules', '@openai', 'codex', 'bin', 'codex.js'));
    expect(npmShimTarget('"%dp0%\\..\\outside.js" %*', '/tmp/bin/custom.cmd')).toBeUndefined();
    expect(npmShimTarget('powershell -Command evil', '/tmp/bin/custom.cmd')).toBeUndefined();
  });
});
