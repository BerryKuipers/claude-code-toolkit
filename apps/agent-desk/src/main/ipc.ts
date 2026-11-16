import { app, dialog, ipcMain, shell, type BrowserWindow } from 'electron';
import { writeFile, access, stat } from 'node:fs/promises';
import { isAbsolute, join } from 'node:path';
import { z } from 'zod';
import { ipcSchemas, launchSchema, profileSchema, settingsSchema } from '../shared/schemas';
import type { Bootstrap, LaunchRequest, TerminalInfo } from '../shared/types';
import { AGENT_LABELS, detectAgents, resolveExecutable } from './executables';
import { buildLaunchPlan } from './launch-plan';
import type { SecretStore } from './secrets';
import type { SessionService } from './sessions';
import type { TerminalService } from './terminals';
import type { WorkspaceService } from './workspace';

interface Services {
  window: BrowserWindow;
  workspace: WorkspaceService;
  sessions: SessionService;
  terminals: TerminalService;
  secrets: SecretStore;
  home: string;
  developmentUrl?: string;
}

export function trustedRenderer(url: string, developmentUrl?: string): boolean {
  try {
    const parsed = new URL(url);
    if (parsed.protocol === 'agentdesk:' && parsed.host === 'app') return true;
    return Boolean(
      developmentUrl &&
      parsed.origin === new URL(developmentUrl).origin &&
      ['127.0.0.1', 'localhost'].includes(parsed.hostname),
    );
  } catch {
    return false;
  }
}

export function registerIpc(services: Services): void {
  const { window, workspace, sessions, terminals, secrets, home, developmentUrl } = services;
  const handle = <T extends unknown[], R>(
    name: string,
    schema: z.ZodType<T>,
    operation: (...args: T) => Promise<R> | R,
  ): void => {
    ipcMain.handle(`desk:${name}`, async (event, ...input) => {
      if (
        event.sender.id !== window.webContents.id ||
        !event.senderFrame ||
        event.senderFrame !== event.sender.mainFrame ||
        !trustedRenderer(event.senderFrame.url, developmentUrl)
      )
        throw new Error('Untrusted renderer request.');
      const args = schema.parse(input);
      return await operation(...args);
    });
  };

  const launch = async (request: LaunchRequest): Promise<TerminalInfo> => {
    const profiles = await workspace.profiles();
    const profile = profiles.find(
      (item) => item.id === (request.profileId || workspace.settings().defaultProfileId),
    );
    if (!profile) throw new Error('Choose an existing connection profile.');
    let session;
    if (request.sessionId) {
      const index = await sessions.index();
      session = index.sessions.find((item) => item.id === request.sessionId);
    }
    const key = await secrets.get(profile.id);
    const plan = buildLaunchPlan(request, profile, process.env, key, session);
    if (!isAbsolute(plan.cwd) || !(await stat(plan.cwd)).isDirectory())
      throw new Error('Choose an existing absolute project folder.');
    if (profile.settingsFile) {
      if (!isAbsolute(profile.settingsFile))
        throw new Error('The additional settings file must use an absolute path.');
      await access(profile.settingsFile);
    }
    const executable = await resolveExecutable(
      workspace.settings().agentCommands[request.agent],
      plan.env,
      home,
    );
    const settings = workspace.settings();
    if (!settings.projects.includes(plan.cwd))
      await workspace.saveSettings({
        ...settings,
        projects: [...settings.projects, plan.cwd].slice(-100),
      });
    const info = await terminals.launch(executable, plan, {
      agent: request.agent,
      title: session?.title || `${AGENT_LABELS[request.agent]} · ${profile.name}`,
      profileId: profile.id,
      sessionId: session?.id,
    });
    return info;
  };

  handle('bootstrap', ipcSchemas.none, async (): Promise<Bootstrap> => ({
    settings: workspace.settings(),
    profiles: await workspace.profiles(),
    agents: await detectAgents(workspace.settings(), home),
    skillRoots: await workspace.skillRoots(),
    appVersion: app.getVersion(),
    platform: process.platform,
    home,
    secureStorageAvailable: secrets.available(),
  }));
  handle('sessions', z.tuple([z.boolean().optional()]), (refresh?: boolean) =>
    sessions.index(refresh),
  );
  handle('transcript', ipcSchemas.id, (id) => sessions.transcript(id));
  handle('skills', ipcSchemas.none, () => workspace.skills());
  handle('readSkill', ipcSchemas.id, (id) => workspace.readSkill(id));
  handle('saveSkill', ipcSchemas.edit, (input) => workspace.saveSkill(input));
  handle('createSkill', ipcSchemas.skillCreate, (input) => workspace.createSkill(input));
  handle('setSkillEnabled', ipcSchemas.skillToggle, (input) => workspace.setSkillEnabled(input));
  handle('configs', ipcSchemas.none, () => workspace.configs());
  handle('saveConfig', ipcSchemas.edit, (input) => workspace.saveConfig(input));
  handle('saveSettings', z.tuple([settingsSchema]), (input) => workspace.saveSettings(input));
  handle('saveProfile', z.tuple([profileSchema]), (input) => workspace.saveProfile(input));
  handle('deleteProfile', ipcSchemas.id, async (id) => {
    await workspace.deleteProfile(id);
    await secrets.delete(id);
  });
  handle('saveSecret', ipcSchemas.secret, async (input) => {
    if (!(await workspace.profiles()).some((profile) => profile.id === input.profileId))
      throw new Error('Save the connection profile before adding its key.');
    await secrets.set(input.profileId, input.secret, input.persist);
  });
  handle('deleteSecret', ipcSchemas.id, (id) => secrets.delete(id));
  handle('models', ipcSchemas.id, (id) => workspace.models(id));
  handle('probe', ipcSchemas.id, (id) => workspace.probe(id));
  handle('launch', z.tuple([launchSchema]), launch);
  handle('terminals', ipcSchemas.none, () => terminals.list());
  handle('terminalSnapshot', ipcSchemas.id, (id) => terminals.snapshot(id));
  handle('terminalWrite', ipcSchemas.terminalInput, (id, data) => terminals.write(id, data));
  handle('terminalResize', ipcSchemas.resize, (id, cols, rows) => terminals.resize(id, cols, rows));
  handle('terminalClose', ipcSchemas.id, (id) => terminals.close(id));
  handle('pickDirectory', ipcSchemas.none, async () => {
    const result = await dialog.showOpenDialog(window, {
      properties: ['openDirectory', 'createDirectory'],
      title: 'Choose project folder',
    });
    return result.canceled ? null : (result.filePaths[0] ?? null);
  });
  handle('revealPath', ipcSchemas.text, async (path) => {
    if (!isAbsolute(path)) throw new Error('An absolute file path is required.');
    await access(path);
    shell.showItemInFolder(path);
  });
  handle('openExternal', ipcSchemas.text, async (value) => {
    const url = new URL(value);
    if (!['https:', 'http:'].includes(url.protocol) || url.username || url.password)
      throw new Error('Only HTTP(S) links without embedded credentials can be opened.');
    await shell.openExternal(url.toString());
  });
  handle('exportSession', ipcSchemas.id, async (id) => {
    const transcript = await sessions.transcript(id);
    const filename =
      transcript.session.title.replace(/[^\p{L}\p{N} _-]/gu, '').slice(0, 100) || 'session';
    const selection = await dialog.showSaveDialog(window, {
      defaultPath: join(app.getPath('documents'), `${filename}.md`),
      filters: [{ name: 'Markdown', extensions: ['md'] }],
    });
    if (selection.canceled || !selection.filePath) return null;
    const content = [
      `# ${transcript.session.title}`,
      '',
      `Agent: ${AGENT_LABELS[transcript.session.agent]}`,
      `Project: ${transcript.session.projectPath}`,
      '',
      ...transcript.messages.flatMap((message) => [
        `## ${message.role}${message.toolName ? ` · ${message.toolName}` : ''}`,
        '',
        message.content,
        '',
      ]),
      ...transcript.warnings.map((warning) => `> ${warning}`),
    ].join('\n');
    await writeFile(selection.filePath, content, { mode: 0o600 });
    return selection.filePath;
  });
  handle('proxyStart', ipcSchemas.none, async () => {
    const active = terminals
      .list()
      .find((terminal) => terminal.agent === 'proxy' && terminal.status === 'running');
    if (active) return active;
    const executable = await resolveExecutable(
      workspace.settings().proxyCommand,
      process.env,
      home,
    );
    const env = Object.fromEntries(
      Object.entries(process.env).filter(
        (entry): entry is [string, string] =>
          typeof entry[1] === 'string' && !entry[0].startsWith('ELECTRON_'),
      ),
    );
    delete env.NODE_OPTIONS;
    return await terminals.launch(
      executable,
      { args: ['serve', '--no-monitor'], env, cwd: home },
      { agent: 'proxy', title: 'Local model proxy' },
    );
  });
  handle('proxyMonitor', ipcSchemas.id, (id) => workspace.proxyMonitor(id));
  handle(
    'proxyAuthenticate',
    z.tuple([z.enum(['codex', 'kimi', 'grok', 'cursor'])]),
    async (provider) => {
      const executable = await resolveExecutable(
        workspace.settings().proxyCommand,
        process.env,
        home,
      );
      const env = Object.fromEntries(
        Object.entries(process.env).filter(
          (entry): entry is [string, string] =>
            typeof entry[1] === 'string' && !entry[0].startsWith('ELECTRON_'),
        ),
      );
      delete env.NODE_OPTIONS;
      return await terminals.launch(
        executable,
        { args: [provider, 'auth', provider === 'grok' ? 'device' : 'login'], env, cwd: home },
        { agent: 'proxy', title: `Proxy · ${provider} sign-in` },
      );
    },
  );
}
