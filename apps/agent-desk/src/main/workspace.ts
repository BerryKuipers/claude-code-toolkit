import { mkdir, readdir, realpath } from 'node:fs/promises';
import path from 'node:path';
import { parse as parseToml } from 'smol-toml';
import { z } from 'zod';
import type { AppSettings, ConfigDocument, ProviderProfile } from '../shared/types';
import {
  agentHomes,
  approvedAnchor,
  atomicWrite,
  canonicalWithin,
  ensureConfiguredRoot,
  ensureDirectoryWithin,
  inside,
  optionalText,
  readJson,
  revision,
  SerialWrites,
  stableId,
  writeRevision,
} from './file-store';
import { defaultProfiles, ProviderService, validateProfile } from './providers';
import { SkillService } from './skills';

const command = z
  .string()
  .trim()
  .min(1)
  .max(4096)
  .refine(
    (value) => !/[\0\r\n]/.test(value),
    'A command must be a single executable name or path.',
  );
const directory = z
  .string()
  .min(1)
  .max(4096)
  .refine(
    (value) => !value.includes('\0') && path.isAbsolute(value),
    'Choose an absolute directory path.',
  );
const settingsSchema = z.object({
  theme: z.enum(['system', 'light', 'dark']),
  fontSize: z.number().int().min(10).max(26),
  terminalScrollback: z.number().int().min(1000).max(100000),
  defaultProfileId: z.string().max(80),
  projects: z.array(directory).max(100),
  historyRoots: z
    .array(
      z.object({
        id: z.string().min(1).max(100),
        agent: z.enum(['claude', 'codex', 'gemini', 'antigravity']),
        path: directory,
      }),
    )
    .max(100),
  skillDirectories: z.array(directory).max(50),
  agentCommands: z.object({
    claude: command,
    codex: command,
    gemini: command,
    antigravity: command,
  }),
  proxyCommand: command,
  scanOnStart: z.boolean(),
  autoRefreshSeconds: z
    .number()
    .int()
    .min(0)
    .max(3600)
    .refine(
      (value) => value === 0 || value >= 10,
      'Automatic refresh must be off or at least 10 seconds.',
    ),
});

export function defaultSettings(): AppSettings {
  return {
    theme: 'system',
    fontSize: 13,
    terminalScrollback: 10000,
    defaultProfileId: 'claude-native',
    projects: [],
    historyRoots: [],
    skillDirectories: [],
    agentCommands: { claude: 'claude', codex: 'codex', gemini: 'gemini', antigravity: 'agy' },
    proxyCommand: 'claude-code-proxy',
    scanOnStart: true,
    autoRefreshSeconds: 30,
  };
}

type ConfigSpec = Omit<ConfigDocument, 'exists' | 'content' | 'revision'> & { root: string };

export class WorkspaceService {
  private state: AppSettings = defaultSettings();
  private providerProfiles: ProviderProfile[] = [];
  private writes = new SerialWrites();
  private readonly providerService: ProviderService;
  private readonly skillService: SkillService;

  constructor(
    private readonly options: {
      home: string;
      dataDir: string;
      secretStatus?: (id: string) => Promise<boolean>;
      secretValue?: (id: string) => Promise<string | undefined>;
    },
  ) {
    this.providerService = new ProviderService({ secretValue: options.secretValue });
    this.skillService = new SkillService({
      home: options.home,
      dataDir: options.dataDir,
      settings: () => this.settings(),
    });
  }

  async init(): Promise<void> {
    await mkdir(this.options.dataDir, { recursive: true, mode: 0o700 });
    const savedSettings = await readJson<Partial<AppSettings>>(
      path.join(this.options.dataDir, 'settings.json'),
      {},
    );
    this.state = settingsSchema.parse({
      ...defaultSettings(),
      ...savedSettings,
      agentCommands: { ...defaultSettings().agentCommands, ...savedSettings.agentCommands },
    });
    const profiles = await readJson<ProviderProfile[]>(
      path.join(this.options.dataDir, 'profiles.json'),
      defaultProfiles(),
    );
    if (!Array.isArray(profiles) || profiles.length > 200)
      throw new Error('Profile storage is invalid. Existing files were left intact.');
    this.providerProfiles = profiles.map(validateProfile);
    if (
      new Set(this.providerProfiles.map((profile) => profile.id)).size !==
      this.providerProfiles.length
    )
      throw new Error('Profile storage contains duplicate IDs.');
    if (!this.providerProfiles.some((profile) => profile.id === this.state.defaultProfileId))
      this.state.defaultProfileId = this.providerProfiles[0]?.id ?? '';
  }

  settings(): AppSettings {
    return structuredClone(this.state);
  }

  async profiles(): Promise<ProviderProfile[]> {
    return Promise.all(
      this.providerProfiles.map(async (profile) => ({
        ...structuredClone(profile),
        hasSecret:
          Boolean(await this.options.secretStatus?.(profile.id)) ||
          Boolean(profile.apiKeyEnv && process.env[profile.apiKeyEnv]),
      })),
    );
  }

  async skillRoots() {
    return this.skillService.roots();
  }
  async skills() {
    return this.skillService.list();
  }
  async readSkill(id: string) {
    return this.skillService.read(id);
  }
  async saveSkill(input: { id: string; content: string; revision: string }) {
    return this.skillService.save(input);
  }
  async createSkill(input: { rootId: string; name: string; content: string }) {
    return this.skillService.create(input);
  }
  async setSkillEnabled(input: { id: string; enabled: boolean }) {
    return this.skillService.setEnabled(input);
  }

  async saveSettings(input: AppSettings): Promise<AppSettings> {
    return this.writes.run(async () => {
      const settings = settingsSchema.parse(input);
      if (!this.providerProfiles.some((profile) => profile.id === settings.defaultProfileId))
        throw new Error('Choose an existing default profile.');
      settings.projects = [...new Set(settings.projects.map((item) => path.resolve(item)))];
      settings.skillDirectories = [
        ...new Set(settings.skillDirectories.map((item) => path.resolve(item))),
      ];
      if (
        new Set(settings.historyRoots.map((root) => root.id)).size !== settings.historyRoots.length
      )
        throw new Error('History root IDs must be unique.');
      await atomicWrite(
        path.join(this.options.dataDir, 'settings.json'),
        `${JSON.stringify(settings, null, 2)}\n`,
      );
      this.state = settings;
      return this.settings();
    });
  }

  async saveProfile(input: ProviderProfile): Promise<ProviderProfile> {
    return this.writes.run(async () => {
      const profile = validateProfile(input);
      const index = this.providerProfiles.findIndex((item) => item.id === profile.id);
      if (index < 0 && this.providerProfiles.length >= 200)
        throw new Error('The profile limit has been reached.');
      const next = structuredClone(this.providerProfiles);
      if (index < 0) next.push(profile);
      else next[index] = profile;
      await atomicWrite(
        path.join(this.options.dataDir, 'profiles.json'),
        `${JSON.stringify(next, null, 2)}\n`,
      );
      this.providerProfiles = next;
      return {
        ...structuredClone(profile),
        hasSecret:
          Boolean(await this.options.secretStatus?.(profile.id)) ||
          Boolean(profile.apiKeyEnv && process.env[profile.apiKeyEnv]),
      };
    });
  }

  async deleteProfile(id: string): Promise<void> {
    return this.writes.run(async () => {
      if (!this.providerProfiles.some((profile) => profile.id === id))
        throw new Error('Profile does not exist.');
      if (this.providerProfiles.length === 1) throw new Error('Keep at least one launch profile.');
      const next = this.providerProfiles.filter((profile) => profile.id !== id);
      if (this.state.defaultProfileId === id) {
        const settings = { ...this.state, defaultProfileId: next[0].id };
        await atomicWrite(
          path.join(this.options.dataDir, 'settings.json'),
          `${JSON.stringify(settings, null, 2)}\n`,
        );
        this.state = settings;
      }
      await atomicWrite(
        path.join(this.options.dataDir, 'profiles.json'),
        `${JSON.stringify(next, null, 2)}\n`,
      );
      this.providerProfiles = next;
    });
  }

  private getProfile(id: string): ProviderProfile {
    const profile = this.providerProfiles.find((item) => item.id === id);
    if (!profile) throw new Error('Profile does not exist.');
    return profile;
  }

  async models(profileId: string) {
    return this.providerService.models(this.getProfile(profileId));
  }
  async probe(profileId: string) {
    return this.providerService.probe(this.getProfile(profileId));
  }
  async proxyMonitor(profileId: string) {
    return this.providerService.proxyMonitor(this.getProfile(profileId));
  }

  private async configSpecs(): Promise<ConfigSpec[]> {
    const home = this.options.home;
    const homes = agentHomes(home);
    const specs: Omit<ConfigSpec, 'id'>[] = [
      {
        agent: 'claude',
        label: 'Claude Code settings',
        path: path.join(homes.claude, 'settings.json'),
        root: homes.claude,
        format: 'json',
      },
      {
        agent: 'claude',
        label: 'Claude Code keybindings',
        path: path.join(homes.claude, 'keybindings.json'),
        root: homes.claude,
        format: 'json',
      },
      {
        agent: 'claude',
        label: 'Claude Code instructions',
        path: path.join(homes.claude, 'CLAUDE.md'),
        root: homes.claude,
        format: 'markdown',
      },
      {
        agent: 'codex',
        label: 'Codex settings',
        path: path.join(homes.codex, 'config.toml'),
        root: homes.codex,
        format: 'toml',
      },
      {
        agent: 'codex',
        label: 'Codex instructions',
        path: path.join(homes.codex, 'AGENTS.md'),
        root: homes.codex,
        format: 'markdown',
      },
      {
        agent: 'gemini',
        label: 'Gemini settings',
        path: path.join(homes.gemini, 'settings.json'),
        root: homes.gemini,
        format: 'json',
      },
      {
        agent: 'gemini',
        label: 'Gemini instructions',
        path: path.join(homes.gemini, 'GEMINI.md'),
        root: homes.gemini,
        format: 'markdown',
      },
      {
        agent: 'antigravity',
        label: 'Antigravity CLI settings',
        path: path.join(home, '.gemini', 'antigravity-cli', 'settings.json'),
        root: path.join(home, '.gemini', 'antigravity-cli'),
        format: 'json',
      },
      {
        agent: 'antigravity',
        label: 'Antigravity CLI keybindings',
        path: path.join(home, '.gemini', 'antigravity-cli', 'keybindings.json'),
        root: path.join(home, '.gemini', 'antigravity-cli'),
        format: 'json',
      },
    ];
    for (const project of this.state.projects) {
      const name = path.basename(project);
      specs.push(
        {
          agent: 'claude',
          label: `${name} · Claude settings`,
          path: path.join(project, '.claude', 'settings.json'),
          root: project,
          format: 'json',
        },
        {
          agent: 'claude',
          label: `${name} · local Claude settings`,
          path: path.join(project, '.claude', 'settings.local.json'),
          root: project,
          format: 'json',
        },
        {
          agent: 'claude',
          label: `${name} · Claude instructions`,
          path: path.join(project, 'CLAUDE.md'),
          root: project,
          format: 'markdown',
        },
        {
          agent: 'codex',
          label: `${name} · agent instructions`,
          path: path.join(project, 'AGENTS.md'),
          root: project,
          format: 'markdown',
        },
        {
          agent: 'codex',
          label: `${name} · Codex settings`,
          path: path.join(project, '.codex', 'config.toml'),
          root: project,
          format: 'toml',
        },
        {
          agent: 'gemini',
          label: `${name} · Gemini settings`,
          path: path.join(project, '.gemini', 'settings.json'),
          root: project,
          format: 'json',
        },
      );
    }
    for (const profile of this.providerProfiles) {
      if (!profile.settingsFile || !path.isAbsolute(profile.settingsFile)) continue;
      const allowed = [path.join(homes.claude, 'profiles'), ...this.state.projects];
      const root = allowed.find((candidate) => inside(candidate, profile.settingsFile!));
      if (root && profile.settingsFile.endsWith('.json'))
        specs.push({
          agent: profile.agent,
          label: `${profile.name} · settings overlay`,
          path: profile.settingsFile,
          root,
          format: 'json',
        });
    }
    const profileRoot = path.join(homes.claude, 'profiles');
    try {
      for (const entry of (await readdir(profileRoot, { withFileTypes: true })).slice(0, 100)) {
        if (!entry.isFile() || !entry.name.endsWith('.json')) continue;
        specs.push({
          agent: 'claude',
          label: `Claude profile · ${entry.name.replace(/\.settings\.json$|\.json$/, '')}`,
          path: path.join(profileRoot, entry.name),
          root: profileRoot,
          format: 'json',
        });
      }
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT')
        throw new Error('Could not list Claude profile overlays. Check directory permissions.');
    }
    return [
      ...new Map(
        specs.map((spec) => [spec.path, { ...spec, id: stableId('config', spec.path) }]),
      ).values(),
    ];
  }

  async configs(): Promise<ConfigDocument[]> {
    const documents: ConfigDocument[] = [];
    for (const spec of await this.configSpecs()) {
      let content: string | undefined;
      try {
        content = await optionalText(spec.path);
        if (content !== undefined) {
          const anchor = approvedAnchor(
            spec.path,
            this.options.home,
            this.state.projects,
            agentHomes(this.options.home).configured,
          );
          const root = await realpath(spec.root);
          if (!inside(await realpath(anchor), root))
            throw new Error('Configuration directory points outside its home or project.');
          await canonicalWithin(spec.path, [root]);
        }
      } catch (error) {
        throw new Error(
          `Cannot read ${spec.label}: ${error instanceof Error ? error.message : 'read failed'}`,
        );
      }
      const { root: _root, ...document } = spec;
      documents.push({
        ...document,
        exists: content !== undefined,
        content: content ?? '',
        revision: revision(content),
      });
    }
    return documents;
  }

  async saveConfig(input: {
    id: string;
    content: string;
    revision: string;
  }): Promise<ConfigDocument> {
    return this.writes.run(async () => {
      const spec = (await this.configSpecs()).find((item) => item.id === input.id);
      if (!spec) throw new Error('This configuration file is not in the approved workspace.');
      if (typeof input.content !== 'string' || input.content.includes('\0'))
        throw new Error('Configuration must be text.');
      if (spec.format === 'json') {
        let value: unknown;
        try {
          value = JSON.parse(input.content);
        } catch {
          throw new Error('The configuration is not valid JSON.');
        }
        if (
          !value ||
          typeof value !== 'object' ||
          (Array.isArray(value) && !spec.path.endsWith('keybindings.json'))
        )
          throw new Error('Settings must be a JSON object.');
      } else if (spec.format === 'toml') {
        try {
          parseToml(input.content);
        } catch (error) {
          throw new Error(
            `The configuration is not valid TOML: ${error instanceof Error ? error.message : 'parse failed'}`,
          );
        }
      }
      const configuredHomes = agentHomes(this.options.home).configured;
      const trustedAnchor = approvedAnchor(
        spec.path,
        this.options.home,
        this.state.projects,
        configuredHomes,
      );
      if (configuredHomes.includes(trustedAnchor)) await ensureConfiguredRoot(trustedAnchor);
      const canonicalRoot = await ensureDirectoryWithin(spec.root, trustedAnchor);
      await ensureDirectoryWithin(path.dirname(spec.path), trustedAnchor);
      await writeRevision({
        file: spec.path,
        content: input.content,
        expectedRevision: input.revision,
        roots: [canonicalRoot],
        backupDir: path.join(this.options.dataDir, 'backups', 'configs'),
      });
      const { root: _root, ...document } = spec;
      return {
        ...document,
        exists: true,
        content: input.content,
        revision: revision(input.content),
      };
    });
  }
}
