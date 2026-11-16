import { describe, expect, it, vi } from 'vitest';
import { defaultProfiles, ProviderService, validateProfile } from '../src/main/providers';

describe('provider routing and discovery', () => {
  it('uses documented direct gateways and discovers models without renaming their provider', () => {
    const profiles = defaultProfiles();
    const service = new ProviderService();
    const router = profiles.find(profile => profile.provider === 'openrouter')!;
    const deepseek = profiles.find(profile => profile.provider === 'deepseek')!;
    expect(router.baseUrl).toBe('https://openrouter.ai/api');
    expect(deepseek.baseUrl).toBe('https://api.deepseek.com/anthropic');
    expect(service.catalogUrl(router)).toBe('https://openrouter.ai/api/v1/models');
    expect(service.catalogUrl(deepseek)).toBe('https://api.deepseek.com/models');
    expect(service.catalogUrl(profiles.find(profile => profile.provider === 'local-proxy')!)).toBe('http://127.0.0.1:18765/v1/models');
    expect(profiles.every(profile => !profile.model)).toBe(true);
  });

  it('normalizes a live catalogue with prices per million, without sending a key to a public catalogue', async () => {
    const fetcher = vi.fn(async (_url: string | URL | Request, options?: RequestInit) => {
      expect((options?.headers as Record<string, string>).Authorization).toBeUndefined();
      expect(options?.redirect).toBe('error');
      return new Response(JSON.stringify({ data: [{ id: 'example/coder', name: 'Coder', context_length: 200000, pricing: { prompt: '0.000002', completion: '0.000008' } }, { id: 'example/free', pricing: { prompt: '0', completion: '0' } }] }));
    });
    const service = new ProviderService({ fetch: fetcher as typeof fetch, secretValue: async () => 'private-value' });
    const catalog = await service.models(defaultProfiles().find(profile => profile.provider === 'openrouter')!);
    expect(catalog.models[0]).toMatchObject({ id: 'example/coder', inputPrice: 2, outputPrice: 8, contextWindow: 200000, free: false });
    expect(catalog.models[1].free).toBe(true);
    expect(catalog.warnings.join()).toContain('not proof');
  });

  it('tests OpenRouter authentication without a paid generation', async () => {
    const fetcher = vi.fn(async (url: string | URL | Request, options?: RequestInit) => {
      expect(url).toBe('https://openrouter.ai/api/v1/key');
      expect(options?.method).toBe('GET');
      expect((options?.headers as Record<string, string>).Authorization).toBe('Bearer test-credential');
      return new Response(JSON.stringify({ data: { label: 'test' } }));
    });
    const status = await new ProviderService({ fetch: fetcher as typeof fetch, secretValue: async () => 'test-credential' }).probe(defaultProfiles().find(profile => profile.provider === 'openrouter')!);
    expect(status.ok).toBe(true);
    expect(status.message).not.toContain('test-credential');
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it('does not confuse proxy liveness with upstream credentials', async () => {
    const service = new ProviderService({ fetch: vi.fn(async () => new Response('{"ok":true}')) as typeof fetch });
    const status = await service.probe(defaultProfiles().find(profile => profile.provider === 'local-proxy')!);
    expect(status.ok).toBe(true);
    expect(status.message).toContain('does not verify');
  });

  it('redacts upstream errors instead of exposing bodies', async () => {
    const service = new ProviderService({ fetch: vi.fn(async () => new Response('secret upstream body', { status: 401 })) as typeof fetch });
    const status = await service.probe(defaultProfiles().find(profile => profile.provider === 'deepseek')!);
    expect(status.ok).toBe(false);
    expect(status.message).toContain('401');
    expect(status.message).not.toContain('secret upstream body');
  });

  it('bounds catalogue responses and recognizes malformed data', async () => {
    const profile = defaultProfiles().find(item => item.provider === 'deepseek')!;
    const huge = new ProviderService({ fetch: vi.fn(async () => new Response('{}', { headers: { 'content-length': '9999999' } })) as typeof fetch });
    await expect(huge.models(profile)).rejects.toThrow('too large');
    const invalid = new ProviderService({ fetch: vi.fn(async () => new Response('{"hello":1}')) as typeof fetch });
    await expect(invalid.models(profile)).rejects.toThrow('supported model catalogue');
  });

  it('aborts unavailable endpoints with a bounded timeout', async () => {
    const fetcher = vi.fn((_url: string | URL | Request, options?: RequestInit) => new Promise<Response>((_resolve, reject) => {
      options?.signal?.addEventListener('abort', () => reject(new Error('aborted')));
    }));
    const service = new ProviderService({ fetch: fetcher as typeof fetch, timeoutMs: 5 });
    await expect(service.models(defaultProfiles().find(profile => profile.provider === 'deepseek')!)).rejects.toThrow('timeout');
  });

  it('rejects secret persistence, endpoint credentials and incompatible routes', () => {
    const profile = defaultProfiles()[0];
    expect(() => validateProfile({ ...profile, env: { OPENROUTER_API_KEY: 'value' } })).toThrow('API key field');
    expect(() => validateProfile({ ...profile, env: { NODE_OPTIONS: '--require=x' } })).toThrow('Runtime');
    expect(() => validateProfile({ ...profile, env: { CODEX_HOME: '/different/history' } })).toThrow('original history store');
    expect(() => validateProfile({ ...profile, route: 'openai-responses', baseUrl: 'https://example.com', provider: 'custom' })).toThrow('Anthropic-compatible');
    expect(() => validateProfile({ ...profile, route: 'anthropic', baseUrl: 'https://user:secret@example.com', provider: 'custom' })).toThrow('without credentials');
  });
});
