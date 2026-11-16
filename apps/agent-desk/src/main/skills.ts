import { lstat, mkdir, readdir, realpath, rename, stat } from 'node:fs/promises';
import path from 'node:path';
import { parse as parseYaml } from 'yaml';
import type { AppSettings, SkillDocument, SkillRecord, SkillRoot } from '../shared/types';
import {
  agentHomes,
  approvedAnchor,
  atomicWrite,
  canonicalWithin,
  ensureConfiguredRoot,
  ensureDirectoryWithin,
  inside,
  optionalText,
  readText,
  revision,
  SerialWrites,
  stableId,
  writeRevision,
} from './file-store';

function frontmatter(content: string): { name?: string; description?: string } {
  const match = content.match(/^\uFEFF?---\s*\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!match) return {};
  const parsed = parseYaml(match[1], { maxAliasCount: 10, strict: true });
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed))
    throw new Error('Skill frontmatter must be a YAML object.');
  return {
    name: typeof parsed.name === 'string' ? parsed.name.slice(0, 160) : undefined,
    description:
      typeof parsed.description === 'string' ? parsed.description.slice(0, 2000) : undefined,
  };
}

export function validateSkill(content: string): void {
  if (typeof content !== 'string' || !content.trim())
    throw new Error('Skill content cannot be empty.');
  if (Buffer.byteLength(content) > 2 * 1024 * 1024 || content.includes('\0'))
    throw new Error('Skill content is too large or contains binary data.');
  frontmatter(content);
}

export class SkillService {
  private records = new Map<string, SkillRecord>();
  private writes = new SerialWrites();

  constructor(
    private readonly options: { home: string; dataDir: string; settings: () => AppSettings },
  ) {}

  async roots(): Promise<SkillRoot[]> {
    const home = this.options.home;
    const homes = agentHomes(home);
    const roots: Omit<SkillRoot, 'id'>[] = [
      { path: path.join(homes.claude, 'skills'), agent: 'claude', scope: 'user', writable: true },
      { path: path.join(homes.codex, 'skills'), agent: 'codex', scope: 'user', writable: true },
      { path: path.join(homes.gemini, 'skills'), agent: 'gemini', scope: 'user', writable: true },
      {
        path: path.join(home, '.gemini', 'antigravity', 'skills'),
        agent: 'antigravity',
        scope: 'user',
        writable: true,
      },
      {
        path: path.join(home, '.gemini', 'antigravity', 'global_skills'),
        agent: 'antigravity',
        scope: 'user',
        writable: true,
      },
      {
        path: path.join(home, '.agents', 'skills'),
        agent: 'shared',
        scope: 'shared',
        writable: true,
      },
      {
        path: path.join(homes.claude, 'plugins'),
        agent: 'claude',
        scope: 'plugin',
        writable: false,
      },
      { path: path.join(homes.codex, 'plugins'), agent: 'codex', scope: 'plugin', writable: false },
    ];
    for (const project of this.options.settings().projects) {
      roots.push(
        {
          path: path.join(project, '.claude', 'skills'),
          agent: 'claude',
          scope: 'project',
          writable: true,
        },
        {
          path: path.join(project, '.codex', 'skills'),
          agent: 'codex',
          scope: 'project',
          writable: true,
        },
        {
          path: path.join(project, '.gemini', 'skills'),
          agent: 'gemini',
          scope: 'project',
          writable: true,
        },
        {
          path: path.join(project, '.agent', 'skills'),
          agent: 'antigravity',
          scope: 'project',
          writable: true,
        },
        {
          path: path.join(project, '.agents', 'skills'),
          agent: 'shared',
          scope: 'shared',
          writable: true,
        },
      );
    }
    const pluginPaths = [
      { path: path.join(homes.claude, 'plugins'), agent: 'claude' as const },
      { path: path.join(homes.codex, 'plugins'), agent: 'codex' as const },
    ];
    for (const directory of this.options.settings().skillDirectories) {
      const plugin = pluginPaths.find((root) => inside(root.path, directory));
      roots.push({
        path: directory,
        agent: plugin?.agent ?? 'shared',
        scope: plugin ? 'plugin' : 'shared',
        writable: !plugin,
      });
    }
    return [
      ...new Map(
        roots.map((root) => [
          path.resolve(root.path),
          { ...root, path: path.resolve(root.path), id: stableId('root', path.resolve(root.path)) },
        ]),
      ).values(),
    ];
  }

  private async writableRoots(roots: SkillRoot[]): Promise<string[]> {
    const result: string[] = [];
    const plugins = await Promise.all(
      roots
        .filter((root) => root.scope === 'plugin')
        .map(async (root) => realpath(root.path).catch(() => path.resolve(root.path))),
    );
    for (const root of roots.filter((item) => item.writable)) {
      try {
        const canonical = await realpath(root.path);
        const anchor = approvedAnchor(
          root.path,
          this.options.home,
          this.options.settings().projects,
          [
            ...agentHomes(this.options.home).configured,
            ...this.options.settings().skillDirectories,
          ],
        );
        const expected = path.join(await realpath(anchor), path.relative(anchor, root.path));
        if (canonical === expected && !plugins.some((plugin) => inside(plugin, canonical)))
          result.push(canonical);
      } catch {}
    }
    return result;
  }

  async list(): Promise<{ skills: SkillRecord[]; roots: SkillRoot[]; warnings: string[] }> {
    const roots = await this.roots();
    const allowed = await this.writableRoots(roots);
    const skills: SkillRecord[] = [];
    const warnings: string[] = [];
    let visited = 0;
    const ignore = new Set(['node_modules', '.git', '.trash', '__pycache__', 'dist', 'build']);
    for (const root of roots) {
      const seen = new Set<string>();
      const walk = async (
        directory: string,
        depth: number,
        inheritedLink = false,
      ): Promise<void> => {
        if (++visited > 12_000 || skills.length >= 3000) return;
        let canonical: string;
        let entries;
        try {
          canonical = await realpath(directory);
          if (seen.has(canonical)) return;
          seen.add(canonical);
          entries = await readdir(directory, { withFileTypes: true });
        } catch (error) {
          if ((error as NodeJS.ErrnoException).code !== 'ENOENT')
            warnings.push(`Could not read ${directory}.`);
          return;
        }
        const linkedDirectory = inheritedLink || canonical !== path.resolve(directory);
        const skillFiles = entries
          .filter((entry) => entry.isFile() || entry.isSymbolicLink())
          .filter((entry) => entry.name === 'SKILL.md' || entry.name === 'SKILL.md.disabled');
        for (const entry of skillFiles) {
          try {
            const file = path.join(directory, entry.name);
            const target = await realpath(file);
            const content = await readText(file);
            const info = frontmatter(content);
            const linked = linkedDirectory || entry.isSymbolicLink();
            skills.push({
              id: stableId('skill', `${root.id}:${path.join(directory, 'SKILL.md')}`),
              name: info.name || path.basename(directory),
              description: info.description || '',
              path: file,
              agent: root.agent,
              scope: root.scope,
              rootId: root.id,
              editable: root.writable && allowed.some((approved) => inside(approved, target)),
              linked,
              disabled: entry.name.endsWith('.disabled'),
            });
          } catch (error) {
            warnings.push(
              `Could not read ${path.join(directory, entry.name)}: ${error instanceof Error ? error.message : 'invalid skill'}`,
            );
          }
        }
        if (skillFiles.length || depth <= 0) return;
        for (const entry of entries) {
          if (ignore.has(entry.name) || entry.name.startsWith('.')) continue;
          if (entry.isDirectory())
            await walk(path.join(directory, entry.name), depth - 1, linkedDirectory);
          else if (entry.isSymbolicLink()) {
            const candidate = path.join(directory, entry.name);
            try {
              if ((await stat(candidate)).isDirectory()) await walk(candidate, depth - 1, true);
            } catch {}
          }
        }
      };
      await walk(root.path, root.scope === 'plugin' ? 8 : 4);
      if (visited > 12_000 || skills.length >= 3000) break;
    }
    if (visited > 12_000 || skills.length >= 3000)
      warnings.push('The scan reached its safety limit. Use more specific skill directories.');
    this.records = new Map(skills.map((skill) => [skill.id, skill]));
    return {
      skills: skills.sort((a, b) => a.name.localeCompare(b.name)),
      roots,
      warnings: warnings.slice(0, 100),
    };
  }

  private async find(id: string): Promise<SkillRecord> {
    if (!this.records.has(id)) await this.list();
    const found = this.records.get(id);
    if (!found) throw new Error('Skill is no longer available. Refresh the list.');
    return found;
  }

  async read(id: string): Promise<SkillDocument> {
    const skill = await this.find(id);
    const content = await readText(skill.path);
    return { skill: { ...skill }, content, revision: revision(content) };
  }

  async save(input: { id: string; content: string; revision: string }): Promise<SkillDocument> {
    return this.writes.run(async () => {
      validateSkill(input.content);
      const skill = await this.find(input.id);
      const roots = await this.roots();
      if (!skill.editable || !roots.find((root) => root.id === skill.rootId)?.writable)
        throw new Error(
          'Installed plugin skills are read-only. Create a personal copy to customize one.',
        );
      await writeRevision({
        file: skill.path,
        content: input.content,
        expectedRevision: input.revision,
        roots: await this.writableRoots(roots),
        backupDir: path.join(this.options.dataDir, 'backups', 'skills'),
      });
      await this.list();
      return this.read(input.id);
    });
  }

  async create(input: { rootId: string; name: string; content: string }): Promise<SkillDocument> {
    return this.writes.run(async () => {
      if (!/^[a-z0-9][a-z0-9_-]{0,79}$/.test(input.name))
        throw new Error('Use a lowercase name with letters, numbers, hyphens, or underscores.');
      validateSkill(input.content);
      const roots = await this.roots();
      const root = roots.find((item) => item.id === input.rootId);
      if (!root?.writable)
        throw new Error('Choose a writable personal or project skills directory.');
      const explicit = this.options
        .settings()
        .skillDirectories.some((directory) => path.resolve(directory) === root.path);
      if (explicit && (await lstat(root.path)).isSymbolicLink())
        throw new Error('Create the skill in the linked directory’s original location.');
      const configuredHomes = agentHomes(this.options.home).configured;
      const anchor = explicit
        ? root.path
        : approvedAnchor(
            root.path,
            this.options.home,
            this.options.settings().projects,
            configuredHomes,
          );
      if (configuredHomes.includes(anchor)) await ensureConfiguredRoot(anchor);
      await ensureDirectoryWithin(root.path, anchor);
      const canonicalRoot = await realpath(root.path);
      const directory = path.join(canonicalRoot, input.name);
      try {
        await lstat(directory);
        throw new Error('A skill with this directory name already exists.');
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
      }
      await mkdir(directory, { mode: 0o700 });
      if (!inside(canonicalRoot, await realpath(directory)))
        throw new Error('The selected directory changed. Refresh and try again.');
      const file = path.join(directory, 'SKILL.md');
      await atomicWrite(file, input.content);
      const list = await this.list();
      const found = list.skills.find(
        (skill) =>
          skill.rootId === root.id && path.basename(path.dirname(skill.path)) === input.name,
      );
      if (!found)
        throw new Error(
          'The skill was created but the directory could not be indexed. Refresh the list.',
        );
      return this.read(found.id);
    });
  }

  async setEnabled(input: { id: string; enabled: boolean }): Promise<void> {
    return this.writes.run(async () => {
      const skill = await this.find(input.id);
      if (
        !skill.editable ||
        !(await this.roots()).find((root) => root.id === skill.rootId)?.writable
      )
        throw new Error(
          'Installed plugin skills are read-only. Manage their plugin in agent settings.',
        );
      if (skill.linked)
        throw new Error(
          'Change the enabled state at this linked skill’s original location. This avoids disabling it for other agents.',
        );
      if (Boolean(skill.disabled) === !input.enabled) return;
      const allowed = await this.writableRoots(await this.roots());
      const source = await canonicalWithin(skill.path, allowed);
      const target = path.join(
        path.dirname(source),
        input.enabled ? 'SKILL.md' : 'SKILL.md.disabled',
      );
      if ((await optionalText(target)) !== undefined)
        throw new Error(
          'Both enabled and disabled versions already exist. Resolve the duplicate before switching.',
        );
      await canonicalWithin(target, allowed, true);
      await rename(source, target);
      await this.list();
    });
  }
}
