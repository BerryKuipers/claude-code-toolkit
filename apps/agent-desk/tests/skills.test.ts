import { mkdtemp, mkdir, readFile, readdir, rm, symlink, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { WorkspaceService } from '../src/main/workspace';

let temporary: string;
let home: string;
let service: WorkspaceService;
const content =
  '---\nname: Useful skill\ndescription: Helps with a real task\n---\n\n# Useful skill\nDo the work.\n';

beforeEach(async () => {
  vi.stubEnv('CLAUDE_CONFIG_DIR', undefined);
  vi.stubEnv('CODEX_HOME', undefined);
  vi.stubEnv('GEMINI_CLI_HOME', undefined);
  temporary = await mkdtemp(path.join(os.tmpdir(), 'agent-desk-skills-'));
  home = path.join(temporary, 'home');
  await mkdir(home);
  service = new WorkspaceService({ home, dataDir: path.join(temporary, 'data') });
  await service.init();
});
afterEach(async () => {
  vi.unstubAllEnvs();
  await rm(temporary, { recursive: true, force: true });
});

describe('skills library', () => {
  it('creates, discovers, edits, disables and restores a real skill', async () => {
    const root = (await service.skillRoots()).find(
      (item) => item.agent === 'claude' && item.scope === 'user',
    )!;
    const created = await service.createSkill({ rootId: root.id, name: 'useful-skill', content });
    expect(created.skill.name).toBe('Useful skill');
    expect(created.skill.editable).toBe(true);
    expect(created.skill.linked).toBe(false);
    const saved = await service.saveSkill({
      id: created.skill.id,
      content: content.replace('Do the work.', 'Finish the actual task.'),
      revision: created.revision,
    });
    expect(saved.revision).not.toBe(created.revision);
    await service.setSkillEnabled({ id: created.skill.id, enabled: false });
    expect((await service.readSkill(created.skill.id)).skill.disabled).toBe(true);
    expect(await readdir(path.dirname(created.skill.path))).toEqual(['SKILL.md.disabled']);
    await service.setSkillEnabled({ id: created.skill.id, enabled: true });
    expect((await service.readSkill(created.skill.id)).skill.disabled).toBe(false);
  });

  it('keeps ordinary skills editable and unlinked when the approved home resolves to another spelling', async () => {
    const alias = path.join(temporary, 'home-alias');
    await symlink(home, alias, 'junction');
    const aliased = new WorkspaceService({
      home: alias,
      dataDir: path.join(temporary, 'alias-data'),
    });
    await aliased.init();
    const root = (await aliased.skillRoots()).find(
      (item) => item.agent === 'claude' && item.scope === 'user',
    )!;
    const created = await aliased.createSkill({ rootId: root.id, name: 'ordinary-skill', content });
    expect(created.skill.linked).toBe(false);
    expect(created.skill.editable).toBe(true);
    await aliased.setSkillEnabled({ id: created.skill.id, enabled: false });
    expect(
      await readFile(
        path.join(home, '.claude', 'skills', 'ordinary-skill', 'SKILL.md.disabled'),
        'utf8',
      ),
    ).toBe(content);
    await aliased.setSkillEnabled({ id: created.skill.id, enabled: true });
    expect((await aliased.readSkill(created.skill.id)).skill.disabled).toBe(false);
  });

  it('rejects traversal and stale revisions without modifying content', async () => {
    const root = (await service.skillRoots()).find(
      (item) => item.agent === 'claude' && item.scope === 'user',
    )!;
    await expect(
      service.createSkill({ rootId: root.id, name: '../escape', content }),
    ).rejects.toThrow('lowercase name');
    const created = await service.createSkill({ rootId: root.id, name: 'safe', content });
    await writeFile(created.skill.path, `${content}\nExternal change.`);
    await expect(
      service.saveSkill({ id: created.skill.id, content, revision: created.revision }),
    ).rejects.toThrow('changed outside');
    expect(await readFile(created.skill.path, 'utf8')).toContain('External change.');
  });

  it('allows editing a shared link only when its target is also in a registered writable root', async () => {
    const shared = path.join(home, '.agents', 'skills', 'shared-task');
    const user = path.join(home, '.claude', 'skills');
    await mkdir(shared, { recursive: true });
    await mkdir(user, { recursive: true });
    await writeFile(path.join(shared, 'SKILL.md'), content);
    await symlink(shared, path.join(user, 'shared-task'), 'dir');
    const linked = (await service.skills()).skills.find((skill) => skill.agent === 'claude')!;
    expect(linked.linked).toBe(true);
    expect(linked.editable).toBe(true);
    const doc = await service.readSkill(linked.id);
    await service.saveSkill({
      id: linked.id,
      content: `${content}\nShared improvement.`,
      revision: doc.revision,
    });
    expect(await readFile(path.join(shared, 'SKILL.md'), 'utf8')).toContain('Shared improvement.');
    await expect(service.setSkillEnabled({ id: linked.id, enabled: false })).rejects.toThrow(
      'original location',
    );
  });

  it('marks external symlinks and installed plugin skills read-only', async () => {
    const outside = path.join(temporary, 'outside');
    const user = path.join(home, '.claude', 'skills');
    const plugin = path.join(
      home,
      '.claude',
      'plugins',
      'cache',
      'market',
      'plugin',
      '1.0',
      'skills',
      'example',
    );
    await mkdir(outside);
    await mkdir(user, { recursive: true });
    await mkdir(plugin, { recursive: true });
    await writeFile(path.join(outside, 'SKILL.md'), content);
    await writeFile(path.join(plugin, 'SKILL.md'), content);
    await symlink(outside, path.join(user, 'outside'), 'dir');
    const skills = (await service.skills()).skills;
    expect(skills.length).toBe(2);
    expect(skills.every((skill) => !skill.editable)).toBe(true);
    const doc = await service.readSkill(skills[0].id);
    await expect(
      service.saveSkill({ id: doc.skill.id, content: 'Changed', revision: doc.revision }),
    ).rejects.toThrow('read-only');
    expect(await readFile(path.join(outside, 'SKILL.md'), 'utf8')).toBe(content);
  });

  it('retains link protection when the entire skills root is a junction', async () => {
    const shared = path.join(home, '.agents', 'skills');
    await mkdir(path.join(shared, 'shared-task'), { recursive: true });
    await mkdir(path.join(home, '.claude'), { recursive: true });
    await writeFile(path.join(shared, 'shared-task', 'SKILL.md'), content);
    await symlink(shared, path.join(home, '.claude', 'skills'), 'junction');
    const linked = (await service.skills()).skills.find((skill) => skill.agent === 'claude')!;
    expect(linked.linked).toBe(true);
    expect(linked.editable).toBe(true);
    await expect(service.setSkillEnabled({ id: linked.id, enabled: false })).rejects.toThrow(
      'original location',
    );
    await expect(
      service.createSkill({ rootId: linked.rootId, name: 'unexpected', content }),
    ).rejects.toThrow('destination directory');
    expect(await readdir(shared)).toEqual(['shared-task']);
  });

  it('rechecks link state before disabling a skill that was replaced by a shared link', async () => {
    const root = (await service.skillRoots()).find(
      (item) => item.agent === 'claude' && item.scope === 'user',
    )!;
    const created = await service.createSkill({ rootId: root.id, name: 'task', content });
    const shared = path.join(home, '.agents', 'skills', 'shared-task');
    await mkdir(shared, { recursive: true });
    await writeFile(path.join(shared, 'SKILL.md'), content);
    await rm(path.dirname(created.skill.path), { recursive: true });
    await symlink(shared, path.dirname(created.skill.path), 'junction');
    await expect(service.setSkillEnabled({ id: created.skill.id, enabled: false })).rejects.toThrow(
      'original location',
    );
    expect(await readdir(shared)).toEqual(['SKILL.md']);
  });

  it('detects a link swap after indexing before writing', async () => {
    const root = (await service.skillRoots()).find(
      (item) => item.agent === 'claude' && item.scope === 'user',
    )!;
    const doc = await service.createSkill({ rootId: root.id, name: 'task', content });
    const outside = path.join(temporary, 'outside.md');
    await writeFile(outside, content);
    await rm(doc.skill.path);
    await symlink(outside, doc.skill.path);
    await expect(
      service.saveSkill({ id: doc.skill.id, content: 'Changed', revision: doc.revision }),
    ).rejects.toThrow('approved');
    expect(await readFile(outside, 'utf8')).toBe(content);
  });

  it('does not make installed plugin files writable through an additional root', async () => {
    const plugin = path.join(
      home,
      '.claude',
      'plugins',
      'cache',
      'market',
      'plugin',
      '1.0',
      'skills',
    );
    await mkdir(path.join(plugin, 'example'), { recursive: true });
    await writeFile(path.join(plugin, 'example', 'SKILL.md'), content);
    await service.saveSettings({ ...service.settings(), skillDirectories: [plugin] });
    const skills = (await service.skills()).skills;
    expect(skills.length).toBeGreaterThan(0);
    expect(skills.every((skill) => !skill.editable && skill.scope === 'plugin')).toBe(true);
  });

  it('creates skills and discovers plugins under overridden agent homes', async () => {
    const configured = path.join(temporary, 'configured');
    vi.stubEnv('CLAUDE_CONFIG_DIR', path.join(configured, 'claude'));
    vi.stubEnv('CODEX_HOME', path.join(configured, 'codex'));
    vi.stubEnv('GEMINI_CLI_HOME', path.join(configured, 'google'));
    const roots = await service.skillRoots();
    const expected = [
      { agent: 'claude', directory: path.join(configured, 'claude', 'skills') },
      { agent: 'codex', directory: path.join(configured, 'codex', 'skills') },
      { agent: 'gemini', directory: path.join(configured, 'google', '.gemini', 'skills') },
    ];
    for (const item of expected) {
      const root = roots.find((root) => root.agent === item.agent && root.scope === 'user')!;
      expect(root.path).toBe(item.directory);
      const created = await service.createSkill({
        rootId: root.id,
        name: 'configured-skill',
        content,
      });
      expect(created.skill.editable).toBe(true);
      expect(
        await readFile(path.join(item.directory, 'configured-skill', 'SKILL.md'), 'utf8'),
      ).toBe(content);
    }
    const plugin = path.join(
      configured,
      'claude',
      'plugins',
      'local',
      'example',
      'skills',
      'helper',
    );
    await mkdir(plugin, { recursive: true });
    await writeFile(path.join(plugin, 'SKILL.md'), content);
    const pluginSkill = (await service.skills()).skills.find(
      (skill) => skill.path === path.join(plugin, 'SKILL.md'),
    )!;
    expect(pluginSkill.scope).toBe('plugin');
    expect(pluginSkill.editable).toBe(false);
    expect(await readdir(home)).toEqual([]);
  });
});
