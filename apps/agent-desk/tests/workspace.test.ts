import { mkdtemp, mkdir, readFile, readdir, rm, symlink, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { WorkspaceService } from '../src/main/workspace';

let temporary: string;
let home: string;
let dataDir: string;
let service: WorkspaceService;

beforeEach(async () => {
  vi.stubEnv('CLAUDE_CONFIG_DIR', undefined);
  vi.stubEnv('CODEX_HOME', undefined);
  vi.stubEnv('GEMINI_CLI_HOME', undefined);
  temporary = await mkdtemp(path.join(os.tmpdir(), 'agent-desk-workspace-'));
  home = path.join(temporary, 'home');
  dataDir = path.join(temporary, 'data');
  await mkdir(home);
  service = new WorkspaceService({ home, dataDir, secretStatus: async id => id === 'claude-openrouter' });
  await service.init();
});
afterEach(async () => { vi.unstubAllEnvs(); await rm(temporary, { recursive: true, force: true }); });

describe('workspace persistence', () => {
  it('persists profiles and settings, keeps secrets out of JSON, and returns isolated snapshots', async () => {
    const profiles = await service.profiles();
    const profile = profiles.find(item => item.provider === 'openrouter')!;
    expect(profile.hasSecret).toBe(true);
    await service.saveProfile({ ...profile, model: 'vendor/coder' });
    await service.saveSettings({ ...service.settings(), defaultProfileId: profile.id, theme: 'dark' });
    const disk = await readFile(path.join(dataDir, 'profiles.json'), 'utf8');
    expect(disk).not.toContain('hasSecret');
    const next = new WorkspaceService({ home, dataDir });
    await next.init();
    expect(next.settings().theme).toBe('dark');
    expect((await next.profiles()).find(item => item.id === profile.id)?.model).toBe('vendor/coder');
    const snapshot = next.settings();
    snapshot.agentCommands.claude = 'unexpected';
    expect(next.settings().agentCommands.claude).toBe('claude');
  });

  it('serializes concurrent mutations so both profiles survive', async () => {
    const first = (await service.profiles())[0];
    await Promise.all([service.saveProfile({ ...first, id: 'new-a', name: 'A' }), service.saveProfile({ ...first, id: 'new-b', name: 'B' })]);
    expect((await service.profiles()).filter(item => item.id.startsWith('new-')).length).toBe(2);
  });

  it('validates JSON/TOML, backs up exact bytes, and detects external changes', async () => {
    const directory = path.join(home, '.claude');
    await mkdir(directory);
    const original = '{"unknown":{"keep":true},"model":"original"}\n';
    await writeFile(path.join(directory, 'settings.json'), original);
    const doc = (await service.configs()).find(item => item.label === 'Claude Code settings')!;
    await expect(service.saveConfig({ id: doc.id, content: '{bad}', revision: doc.revision })).rejects.toThrow('valid JSON');
    const changed = original.replace('original', 'new-model');
    const saved = await service.saveConfig({ id: doc.id, content: changed, revision: doc.revision });
    expect(JSON.parse(saved.content).unknown.keep).toBe(true);
    const backups = await readdir(path.join(dataDir, 'backups', 'configs'));
    expect(await readFile(path.join(dataDir, 'backups', 'configs', backups[0]), 'utf8')).toBe(original);
    await writeFile(doc.path, '{"external":true}');
    await expect(service.saveConfig({ id: doc.id, content: changed, revision: saved.revision })).rejects.toThrow('changed outside');
    const toml = (await service.configs()).find(item => item.format === 'toml')!;
    await expect(service.saveConfig({ id: toml.id, content: 'key = [', revision: toml.revision })).rejects.toThrow('valid TOML');
  });

  it('creates a missing configuration only at its approved path', async () => {
    const doc = (await service.configs()).find(item => item.label === 'Codex settings')!;
    expect(doc.exists).toBe(false);
    const saved = await service.saveConfig({ id: doc.id, content: 'model_reasoning_effort = "medium"\n', revision: doc.revision });
    expect(saved.exists).toBe(true);
    expect(await readFile(saved.path, 'utf8')).toContain('medium');
    await expect(service.saveConfig({ id: '../../outside', content: '{}', revision: doc.revision })).rejects.toThrow('approved');
  });

  it('rejects symlink escapes before creating directories or replacing files', async () => {
    const outside = path.join(temporary, 'outside');
    await mkdir(outside);
    await symlink(outside, path.join(home, '.claude'), 'dir');
    const doc = (await service.configs()).find(item => item.label === 'Claude Code settings')!;
    await expect(service.saveConfig({ id: doc.id, content: '{}', revision: doc.revision })).rejects.toThrow('link');
    expect(await readdir(outside)).toEqual([]);
  });

  it('does not overwrite corrupted persisted state with defaults', async () => {
    await writeFile(path.join(dataDir, 'settings.json'), '{broken');
    await expect(new WorkspaceService({ home, dataDir }).init()).rejects.toThrow('invalid JSON');
    expect(await readFile(path.join(dataDir, 'settings.json'), 'utf8')).toBe('{broken');
  });

  it('reads and creates configs in explicitly overridden agent homes outside the user home', async () => {
    const claude = path.join(temporary, 'configured', 'claude');
    const codex = path.join(temporary, 'configured', 'codex');
    const geminiParent = path.join(temporary, 'configured', 'google');
    vi.stubEnv('CLAUDE_CONFIG_DIR', claude);
    vi.stubEnv('CODEX_HOME', codex);
    vi.stubEnv('GEMINI_CLI_HOME', geminiParent);
    const docs = await service.configs();
    const expected = [
      { label: 'Claude Code settings', file: path.join(claude, 'settings.json'), content: '{"model":"configured"}' },
      { label: 'Codex settings', file: path.join(codex, 'config.toml'), content: 'model_provider = "custom"\n' },
      { label: 'Gemini settings', file: path.join(geminiParent, '.gemini', 'settings.json'), content: '{"theme":"custom"}' },
    ];
    for (const item of expected) {
      const doc = docs.find(candidate => candidate.label === item.label)!;
      expect(doc.path).toBe(item.file);
      expect(doc.exists).toBe(false);
      await service.saveConfig({ id: doc.id, content: item.content, revision: doc.revision });
      expect(await readFile(item.file, 'utf8')).toBe(item.content);
    }
    expect(await readdir(home)).toEqual([]);
    await mkdir(path.join(claude, 'profiles'));
    await writeFile(path.join(claude, 'profiles', 'custom.settings.json'), '{"model":"custom"}');
    expect((await service.configs()).some(doc => doc.path === path.join(claude, 'profiles', 'custom.settings.json'))).toBe(true);
  });

  it('keeps file symlinks inside an overridden root from escaping it', async () => {
    const configured = path.join(temporary, 'configured');
    await mkdir(configured);
    vi.stubEnv('CLAUDE_CONFIG_DIR', configured);
    const doc = (await service.configs()).find(item => item.label === 'Claude Code settings')!;
    const target = path.join(temporary, 'outside.json');
    await writeFile(target, '{}');
    await symlink(target, doc.path);
    await expect(service.saveConfig({ id: doc.id, content: '{"changed":true}', revision: doc.revision })).rejects.toThrow('approved');
    expect(await readFile(target, 'utf8')).toBe('{}');
  });

  it('distinguishes a missing file from an empty file created by another editor', async () => {
    const doc = (await service.configs()).find(item => item.label === 'Claude Code instructions')!;
    await mkdir(path.dirname(doc.path));
    await writeFile(doc.path, '');
    await expect(service.saveConfig({ id: doc.id, content: 'New instructions', revision: doc.revision })).rejects.toThrow('changed outside');
    expect(await readFile(doc.path, 'utf8')).toBe('');
  });

  it('accepts only one concurrent writer using the same original revision', async () => {
    await mkdir(path.join(home, '.claude'));
    await writeFile(path.join(home, '.claude', 'settings.json'), '{"model":"original"}');
    const other = new WorkspaceService({ home, dataDir });
    await other.init();
    const doc = (await service.configs()).find(item => item.label === 'Claude Code settings')!;
    const results = await Promise.allSettled([
      service.saveConfig({ id: doc.id, content: '{"model":"first"}', revision: doc.revision }),
      other.saveConfig({ id: doc.id, content: '{"model":"second"}', revision: doc.revision }),
    ]);
    expect(results.filter(result => result.status === 'fulfilled')).toHaveLength(1);
    expect(results.filter(result => result.status === 'rejected')).toHaveLength(1);
    const winner = results.find(result => result.status === 'fulfilled');
    expect(await readFile(doc.path, 'utf8')).toBe(winner?.status === 'fulfilled' ? winner.value.content : '');
  });
});
