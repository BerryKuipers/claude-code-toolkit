import {
  test as base,
  expect,
  _electron,
  type ElectronApplication,
  type Page,
} from '@playwright/test';
import { chmod, mkdir, mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { createServer, type Server } from 'node:http';
import { createRequire } from 'node:module';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defaultSettings } from '../src/main/workspace';
import type { ProviderProfile } from '../src/shared/types';

const require = createRequire(import.meta.url);
const appDirectory = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const fixtureSessionId = '12345678-1234-4234-8234-123456789abc';
const packaged = process.env.AGENT_DESK_PACKAGED === '1';

function desktopExecutable(): string {
  if (!packaged) return require('electron') as string;
  if (process.platform === 'linux')
    return path.join(appDirectory, 'release', 'linux-unpacked', 'agent-desk');
  if (process.platform === 'win32')
    return path.join(appDirectory, 'release', 'win-unpacked', 'Agent Desk.exe');
  throw new Error('Packaged desktop checks currently support Linux and Windows.');
}

interface DesktopFixture {
  application: ElectronApplication;
  page: Page;
  home: string;
  data: string;
  project: string;
  claude: string;
  invocations: string;
  gatewayUrl: string;
  requests: Array<{ method: string; url: string }>;
}

const fakeAgent = String.raw`
const fs = require('node:fs');
const readline = require('node:readline');
const args = process.argv.slice(2);
if (args.includes('--version')) {
  process.stdout.write('Agent Desk fixture CLI 1.0.0\n');
  process.exit(0);
}
if (args[0] === 'app-server') {
  const input = readline.createInterface({ input: process.stdin, terminal: false });
  input.on('line', line => {
    const request = JSON.parse(line);
    if (request.id === undefined) return;
    const result = request.method === 'initialize'
      ? { userAgent: 'agent-desk-fixture' }
      : { data: [], nextCursor: null };
    process.stdout.write(JSON.stringify({ id: request.id, result }) + '\n');
  });
} else {
  const resume = args.indexOf('--resume');
  const nativeId = resume >= 0 ? args[resume + 1] : 'new';
  fs.appendFileSync(process.env.AGENT_DESK_FIXTURE_INVOCATIONS, JSON.stringify({ pid: process.pid, args, cwd: process.cwd(), nativeId }) + '\n');
  process.stdout.write('FAKE_AGENT_READY resume=' + nativeId + '\r\n');
  let statusCount = 0;
  let input = '';
  if (process.stdin.isTTY) process.stdin.setRawMode(true);
  process.stdin.setEncoding('utf8');
  process.stdin.resume();
  process.stdin.on('data', chunk => {
    for (const char of chunk) {
      if (char === '\u0003') process.exit(0);
      if (char === '\r' || char === '\n') {
        const command = input.trim();
        input = '';
        if (!command) continue;
        if (command === '/status') process.stdout.write('\r\nFAKE_STATUS_' + (++statusCount) + ' pid=' + process.pid + '\r\n');
        else if (command === '/exit') process.exit(0);
        else process.stdout.write('\r\nFAKE_ECHO ' + command + '\r\n');
      } else if (char === '\u007f' || char === '\b') {
        input = input.slice(0, -1);
      } else {
        input += char;
      }
    }
  });
}
`;

async function closeServer(server: Server): Promise<void> {
  server.closeAllConnections();
  await new Promise<void>((resolve, reject) =>
    server.close((error) => (error ? reject(error) : resolve())),
  );
}

const test = base.extend<{ desktop: DesktopFixture }>({
  desktop: async ({}, use, testInfo) => {
    const temporary = await mkdtemp(path.join(os.tmpdir(), 'agent-desk-desktop-'));
    const home = path.join(temporary, 'home');
    const data = path.join(temporary, 'app-data');
    const project = path.join(temporary, 'projects', 'desktop-fixture');
    const claude = path.join(temporary, 'agent-config', 'claude');
    const codex = path.join(temporary, 'agent-config', 'codex');
    const geminiParent = path.join(temporary, 'agent-config', 'google');
    const executable = path.join(temporary, 'fixture-agent.cjs');
    const invocations = path.join(temporary, 'invocations.jsonl');
    const requests: DesktopFixture['requests'] = [];
    const errors: string[] = [];
    let processOutput = '';
    let application: ElectronApplication | undefined;
    let page: Page | undefined;
    let serverListening = false;
    const server = createServer((request, response) => {
      requests.push({ method: request.method ?? '', url: request.url ?? '' });
      response.setHeader('content-type', 'application/json');
      if (request.method !== 'GET') {
        response.writeHead(405).end('{"error":"This fixture never generates model output."}');
      } else if (request.url === '/healthz') {
        response.end('{"ok":true}');
      } else if (request.url === '/v1/models') {
        response.end(
          JSON.stringify({
            data: [
              {
                id: 'fixture/coder',
                display_name: 'Fixture coder',
                context_length: 128000,
                pricing: { prompt: '0', completion: '0' },
              },
              {
                id: 'fixture/reasoner',
                display_name: 'Fixture reasoner',
                context_length: 256000,
                pricing: { prompt: '0.000001', completion: '0.000002' },
              },
            ],
            has_more: false,
          }),
        );
      } else if (request.url === '/monitor') {
        response.end(
          '{"version":1,"snapshot":{"sessions":[],"active_requests":[],"recent_requests":[]}}',
        );
      } else {
        response.writeHead(404).end('{"error":"Unknown fixture route"}');
      }
    });
    try {
      for (const directory of [
        home,
        data,
        project,
        claude,
        codex,
        path.join(geminiParent, '.gemini'),
      ])
        await mkdir(directory, { recursive: true });
      await writeFile(executable, fakeAgent);
      await chmod(executable, 0o755);
      await writeFile(invocations, '');
      await writeFile(
        path.join(claude, 'settings.json'),
        JSON.stringify(
          {
            model: 'fixture-native',
            effortLevel: 'medium',
            statusLine: { type: 'command', command: 'fixture-status-line' },
            fixtureUnrecognizedSetting: { keep: true },
          },
          null,
          2,
        ),
      );
      const settings = {
        ...defaultSettings(),
        theme: 'light' as const,
        projects: [project],
        agentCommands: {
          claude: executable,
          codex: executable,
          gemini: executable,
          antigravity: executable,
        },
        proxyCommand: executable,
        autoRefreshSeconds: 0,
      };
      await writeFile(path.join(data, 'settings.json'), JSON.stringify(settings));
      const transcriptDirectory = path.join(claude, 'projects', 'fixture-project');
      await mkdir(transcriptDirectory, { recursive: true });
      const timestamp = new Date().toISOString();
      for (const [id, title, prompt] of [
        [fixtureSessionId, 'Desktop resume fixture', 'Continue the desktop layout'],
        [
          '87654321-4321-4321-8321-123456789abc',
          'Unrelated fixture conversation',
          'Inspect another project',
        ],
      ]) {
        const records = [
          {
            type: 'user',
            uuid: `${id}-user`,
            parentUuid: null,
            sessionId: id,
            cwd: project,
            timestamp,
            message: { role: 'user', content: prompt },
          },
          {
            type: 'assistant',
            uuid: `${id}-assistant`,
            parentUuid: `${id}-user`,
            sessionId: id,
            cwd: project,
            timestamp,
            message: {
              role: 'assistant',
              model: 'fixture-model',
              content: [
                { type: 'text', text: 'Recorded fixture answer with a working transcript.' },
              ],
            },
          },
          { type: 'custom-title', customTitle: title },
        ];
        await writeFile(
          path.join(transcriptDirectory, `${id}.jsonl`),
          records.map((record) => JSON.stringify(record)).join('\n') + '\n',
        );
      }
      await new Promise<void>((resolve, reject) => {
        server.once('error', reject);
        server.listen(0, '127.0.0.1', () => {
          serverListening = true;
          resolve();
        });
      });
      const address = server.address();
      if (!address || typeof address === 'string')
        throw new Error('The fixture gateway did not receive a port.');
      const gatewayUrl = `http://127.0.0.1:${address.port}`;
      const env = Object.fromEntries(
        Object.entries(process.env).filter(
          (entry): entry is [string, string] =>
            typeof entry[1] === 'string' &&
            !/(?:API_KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)/i.test(entry[0]),
        ),
      );
      delete env.ELECTRON_RUN_AS_NODE;
      delete env.AGENT_DESK_DEV_URL;
      Object.assign(env, {
        AGENT_DESK_HOME: home,
        AGENT_DESK_DATA_DIR: data,
        AGENT_DESK_FIXTURE_INVOCATIONS: invocations,
        CLAUDE_CONFIG_DIR: claude,
        CODEX_HOME: codex,
        GEMINI_CLI_HOME: geminiParent,
      });
      const args = [
        ...(process.platform === 'linux' && process.env.CI
          ? ['--no-sandbox', '--disable-dev-shm-usage']
          : []),
        ...(packaged ? [] : [appDirectory]),
      ];
      application = await _electron.launch({
        executablePath: desktopExecutable(),
        args,
        cwd: appDirectory,
        env,
        timeout: 45000,
      });
      const capture = (chunk: Buffer): void => {
        processOutput = `${processOutput}${chunk.toString()}`.slice(-20000);
      };
      application.process().stdout?.on('data', capture);
      application.process().stderr?.on('data', capture);
      expect(
        await application.evaluate(({ app }) => app.isPackaged),
        'Electron packaging mode',
      ).toBe(packaged);
      await application
        .context()
        .tracing.start({ screenshots: true, snapshots: true, sources: true });
      page = await application.firstWindow();
      page.on('pageerror', (error) => errors.push(error.message));
      await expect(page.getByLabel('Search sessions')).toBeVisible();
      await expect(page.getByRole('button', { name: /Desktop resume fixture/ })).toBeVisible();
      expect(
        await page.evaluate(() => ({
          hasBridge: Boolean(window.desk),
          nodeAvailable:
            typeof (window as unknown as { require?: unknown }).require !== 'undefined',
        })),
      ).toEqual({ hasBridge: true, nodeAvailable: false });
      await use({
        application,
        page,
        home,
        data,
        project,
        claude,
        invocations,
        gatewayUrl,
        requests,
      });
      expect(errors, 'renderer JavaScript errors').toEqual([]);
    } finally {
      if (page && !page.isClosed()) {
        const screenshot = testInfo.outputPath('desktop.png');
        await page
          .screenshot({ path: screenshot, fullPage: true })
          .then(() => testInfo.attach('Desktop', { path: screenshot, contentType: 'image/png' }))
          .catch(() => undefined);
        await page
          .evaluate(async () => {
            for (const terminal of await window.desk.terminals())
              await window.desk.terminalClose(terminal.id);
          })
          .catch(() => undefined);
      }
      if (application) {
        if (testInfo.status !== testInfo.expectedStatus) {
          const trace = testInfo.outputPath('trace.zip');
          await application
            .context()
            .tracing.stop({ path: trace })
            .then(() => testInfo.attach('Trace', { path: trace, contentType: 'application/zip' }))
            .catch(() => undefined);
          await testInfo.attach('Electron output', {
            body: processOutput,
            contentType: 'text/plain',
          });
        } else {
          await application
            .context()
            .tracing.stop()
            .catch(() => undefined);
        }
        await application
          .evaluate(({ BrowserWindow }) => {
            for (const window of BrowserWindow.getAllWindows()) window.destroy();
          })
          .catch(() => undefined);
        await application.close().catch(() => undefined);
      }
      if (serverListening) await closeServer(server);
      await rm(temporary, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
    }
  },
});

async function navigation(page: Page, name: string): Promise<void> {
  await page
    .getByRole('navigation', { name: 'Main navigation' })
    .getByRole('button', { name: new RegExp(`^${name}`) })
    .click();
}

async function enterTerminal(page: Page, command: string): Promise<void> {
  const input = page.locator('.terminal-surface:visible .xterm-helper-textarea');
  await input.focus();
  await input.pressSequentially(command);
  await input.press('Enter');
}

test('finds and resumes a local session through the real PTY, preserving it across views', async ({
  desktop,
}, testInfo) => {
  const { page, invocations, project } = desktop;
  await page.getByLabel('Search sessions').fill('not-a-fixture');
  await expect(page.getByText('No matching sessions', { exact: true })).toBeVisible();
  await page.getByLabel('Search sessions').fill('Desktop resume fixture');
  await page.getByLabel('Filter sessions by agent').selectOption('claude');
  await page.getByRole('button', { name: /Desktop resume fixture/ }).click();
  await expect(page.getByRole('region', { name: 'Session conversation' })).toContainText(
    'Recorded fixture answer',
  );
  await page.getByRole('button', { name: 'Resume session', exact: true }).click();
  const live = page.getByRole('region', { name: 'Live agent workspace' });
  await expect(live).toBeVisible();
  await expect(live.locator('.xterm-accessibility-tree')).toContainText('FAKE_AGENT_READY');
  const original = await page.evaluate(async () => (await window.desk.terminals())[0]);
  expect(original.status).toBe('running');
  const invocation = JSON.parse((await readFile(invocations, 'utf8')).trim().split('\n').at(-1)!);
  expect(invocation.nativeId).toBe(fixtureSessionId);
  expect(invocation.cwd).toBe(project);
  await enterTerminal(page, '/status');
  await expect(live.locator('.xterm-accessibility-tree')).toContainText('FAKE_STATUS_1');
  await navigation(page, 'Skills');
  await expect(page.getByRole('heading', { name: /^Skills/ })).toBeVisible();
  await navigation(page, 'Workspace');
  await expect(live.locator('.xterm-accessibility-tree')).toContainText('FAKE_STATUS_1');
  await enterTerminal(page, '/status');
  await expect(live.locator('.xterm-accessibility-tree')).toContainText('FAKE_STATUS_2');
  const current = await page.evaluate(async () => (await window.desk.terminals())[0]);
  expect(current.id).toBe(original.id);
  expect((await readFile(invocations, 'utf8')).trim().split('\n')).toHaveLength(1);
  const terminalScreenshot = testInfo.outputPath('live-terminal.png');
  await page.screenshot({ path: terminalScreenshot, fullPage: true });
  await testInfo.attach('Live terminal after resume', {
    path: terminalScreenshot,
    contentType: 'image/png',
  });
  await live.locator('.terminal-tabs button[aria-label^="Close "]').click();
  await page
    .getByRole('dialog', { name: 'Stop this running session?' })
    .getByRole('button', { name: 'Stop and close', exact: true })
    .click();
  await expect
    .poll(() => page.evaluate(async () => (await window.desk.terminals()).length))
    .toBe(0);
});

test('creates and edits a skill, then disables and restores its original file', async ({
  desktop,
}) => {
  const { page, claude } = desktop;
  await navigation(page, 'Skills');
  await page.getByRole('button', { name: 'Create skill', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Create a skill', exact: true });
  await dialog.getByLabel('Name', { exact: true }).fill('desktop-smoke-skill');
  await dialog
    .getByLabel('Save in', { exact: true })
    .selectOption({ label: path.join(claude, 'skills') });
  await dialog
    .getByLabel('Description', { exact: true })
    .fill('A fixture skill for desktop integration checks.');
  await dialog
    .getByLabel('Instructions · Markdown', { exact: true })
    .fill('# Fixture instructions\n\nKeep this skill local.');
  await dialog.getByRole('button', { name: 'Create skill', exact: true }).click();
  await expect(dialog).not.toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'desktop-smoke-skill', exact: true }),
  ).toBeVisible();
  const file = path.join(claude, 'skills', 'desktop-smoke-skill', 'SKILL.md');
  await expect.poll(() => readFile(file, 'utf8')).toContain('Keep this skill local.');
  await page.getByRole('button', { name: 'Edit', exact: true }).click();
  const editor = page.getByLabel('Skill Markdown source', { exact: true });
  const edited = (await editor.inputValue()) + '\n\nVerified desktop editing survives a reload.\n';
  await editor.fill(edited);
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect.poll(() => readFile(file, 'utf8')).toBe(edited);
  await page.getByRole('button', { name: 'Disable skill', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Restore skill', exact: true })).toBeVisible();
  expect(await readdir(path.dirname(file))).toEqual(['SKILL.md.disabled']);
  await page.getByRole('button', { name: 'Restore skill', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Disable skill', exact: true })).toBeVisible();
  expect(await readFile(file, 'utf8')).toBe(edited);
});

test('validates and saves native settings with a backup and retains unknown fields', async ({
  desktop,
}) => {
  const { page, claude, data } = desktop;
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('tab', { name: 'Native configuration', exact: true }).click();
  const source = page.getByLabel('Claude Code settings source', { exact: true });
  await expect(source).toBeVisible();
  const original = await readFile(path.join(claude, 'settings.json'), 'utf8');
  await source.fill('{not valid json');
  await page.getByRole('button', { name: 'Save file', exact: true }).click();
  await expect(page.getByRole('alert').first()).toBeVisible();
  expect(await readFile(path.join(claude, 'settings.json'), 'utf8')).toBe(original);
  const updated = JSON.stringify({ ...JSON.parse(original), effortLevel: 'high' }, null, 2);
  await source.fill(updated);
  await page.getByRole('button', { name: 'Save file', exact: true }).click();
  await expect.poll(() => readFile(path.join(claude, 'settings.json'), 'utf8')).toBe(updated);
  expect(JSON.parse(updated).fixtureUnrecognizedSetting.keep).toBe(true);
  const backups = await readdir(path.join(data, 'backups', 'configs'));
  expect(backups).toHaveLength(1);
  expect(await readFile(path.join(data, 'backups', 'configs', backups[0]), 'utf8')).toBe(original);
  await navigation(page, 'Sessions');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('tab', { name: 'Native configuration', exact: true }).click();
  await expect(page.getByLabel('Claude Code settings source', { exact: true })).toHaveValue(
    updated,
  );
});

test('saves a connection, tests a local endpoint and chooses a model from its real catalogue', async ({
  desktop,
}) => {
  const { page, data, gatewayUrl, requests } = desktop;
  await navigation(page, 'Models & connections');
  await page.getByRole('button', { name: 'Add connection', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'A new connection', exact: true });
  await dialog.getByLabel('Profile name', { exact: true }).fill('Desktop mock gateway');
  await dialog.getByLabel('Connect through', { exact: true }).selectOption('local-proxy');
  await dialog.getByLabel('Endpoint URL', { exact: true }).fill(gatewayUrl);
  await dialog.getByLabel('API key', { exact: true }).fill('fixture-secret-only');
  const remember = dialog.getByRole('checkbox', { name: /Remember using this computer/ });
  if (await remember.isEnabled()) await remember.uncheck();
  await dialog.getByRole('button', { name: 'Save connection', exact: true }).click();
  await expect(dialog).not.toBeVisible();
  const card = page
    .getByRole('article')
    .filter({ has: page.getByRole('heading', { name: 'Desktop mock gateway', exact: true }) });
  await expect(card).toBeVisible();
  await card.getByRole('button', { name: 'Test connection', exact: true }).click();
  await expect(card).toContainText('Proxy is running');
  await card.getByRole('button', { name: 'Models', exact: true }).click();
  const catalog = page.getByRole('dialog', { name: 'Explore available models', exact: true });
  await catalog.getByLabel('Search models', { exact: true }).fill('Fixture coder');
  await catalog.getByRole('checkbox', { name: 'Free only', exact: true }).check();
  await catalog.getByRole('button', { name: /Fixture coder/ }).click();
  const edit = page.getByRole('dialog', { name: 'Edit connection', exact: true });
  await expect(edit.getByLabel('Model ID', { exact: true })).toHaveValue('fixture/coder');
  await edit.getByRole('button', { name: 'Save connection', exact: true }).click();
  await expect(card).toContainText('fixture/coder');
  const profileFile = await readFile(path.join(data, 'profiles.json'), 'utf8');
  const profiles = JSON.parse(profileFile) as ProviderProfile[];
  expect(profiles.find((profile) => profile.name === 'Desktop mock gateway')).toMatchObject({
    provider: 'local-proxy',
    route: 'anthropic',
    baseUrl: gatewayUrl,
    model: 'fixture/coder',
  });
  expect(profileFile).not.toContain('fixture-secret-only');
  expect(profileFile).not.toContain('hasSecret');
  expect(requests).toContainEqual({ method: 'GET', url: '/healthz' });
  expect(requests).toContainEqual({ method: 'GET', url: '/v1/models' });
  expect(requests.every((request) => request.method === 'GET')).toBe(true);
});
