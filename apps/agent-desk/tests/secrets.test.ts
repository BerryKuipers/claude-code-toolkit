import { afterEach, describe, expect, it } from 'vitest';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { SecretStore, type SecretCipher } from '../src/main/secrets';

const directories: string[] = [];
afterEach(async () => {
  await Promise.all(
    directories.splice(0).map((directory) => rm(directory, { recursive: true, force: true })),
  );
});
const cipher: SecretCipher = {
  available: () => true,
  encrypt: (value) => Buffer.from([...value].reverse().join('')),
  decrypt: (value) => [...value.toString()].reverse().join(''),
};

async function store(available = true): Promise<{ instance: SecretStore; path: string }> {
  const directory = await mkdtemp(join(tmpdir(), 'agent-desk-secrets-'));
  directories.push(directory);
  const path = join(directory, 'keys.json');
  const instance = new SecretStore(path, { ...cipher, available: () => available });
  await instance.init();
  return { instance, path };
}

describe('credential persistence', () => {
  it('never writes session-only credentials to disk', async () => {
    const { instance, path } = await store(false);
    await instance.set('local', 'session-test-key', false);
    expect(await instance.get('local')).toBe('session-test-key');
    await expect(readFile(path)).rejects.toMatchObject({ code: 'ENOENT' });
    await expect(instance.set('local', 'key', true)).rejects.toThrow(/unavailable/);
  });

  it('persists only cipher output, restores and deletes it', async () => {
    const { instance, path } = await store();
    await instance.set('provider', 'secret-test-key', true);
    expect(await readFile(path, 'utf8')).not.toContain('secret-test-key');
    const restored = new SecretStore(path, cipher);
    await restored.init();
    expect(await restored.get('provider')).toBe('secret-test-key');
    await restored.delete('provider');
    expect(restored.has('provider')).toBe(false);
    expect(await readFile(path, 'utf8')).toBe('{}');
  });

  it('removes a persisted credential when switching to session-only', async () => {
    const { instance, path } = await store();
    await instance.set('provider', 'old-key', true);
    await instance.set('provider', 'temporary-key', false);
    expect(await readFile(path, 'utf8')).toBe('{}');
    expect(await instance.get('provider')).toBe('temporary-key');
  });
});
