import { app, BrowserWindow, dialog, net, protocol, safeStorage, session } from 'electron';
import { join, resolve, sep } from 'node:path';
import { homedir } from 'node:os';
import { pathToFileURL } from 'node:url';
import { registerIpc, trustedRenderer } from './ipc';
import { SecretStore } from './secrets';
import { SessionService } from './sessions';
import { TerminalService } from './terminals';
import { WorkspaceService } from './workspace';
import type { TerminalEvent } from '../shared/types';

protocol.registerSchemesAsPrivileged([
  {
    scheme: 'agentdesk',
    privileges: { standard: true, secure: true, supportFetchAPI: true, corsEnabled: true },
  },
]);

const developmentUrl = !app.isPackaged ? process.env.AGENT_DESK_DEV_URL : undefined;
if (developmentUrl && !/^http:\/\/(?:127\.0\.0\.1|localhost):\d+\/?$/.test(developmentUrl))
  throw new Error('Development URL must point to a loopback Vite server.');
if (process.env.AGENT_DESK_DATA_DIR)
  app.setPath('userData', resolve(process.env.AGENT_DESK_DATA_DIR));
const home = process.env.AGENT_DESK_HOME ? resolve(process.env.AGENT_DESK_HOME) : homedir();
let mainWindow: BrowserWindow | null = null;
let terminals: TerminalService | undefined;
let sessions: SessionService | undefined;
let allowClose = false;
let closeDialogOpen = false;

async function start(): Promise<void> {
  const dataDir = app.getPath('userData');
  const encryptionAvailable = await safeStorage.isAsyncEncryptionAvailable();
  const secrets = new SecretStore(join(dataDir, 'credentials.json'), {
    available: () =>
      encryptionAvailable &&
      (process.platform !== 'linux' ||
        !['basic_text', 'unknown'].includes(safeStorage.getSelectedStorageBackend())),
    encrypt: (value) => safeStorage.encryptStringAsync(value),
    decrypt: async (value) => (await safeStorage.decryptStringAsync(value)).result,
  });
  await secrets.init();
  const workspace = new WorkspaceService({
    home,
    dataDir,
    secretStatus: async (id) => secrets.has(id),
    secretValue: (id) => secrets.get(id),
  });
  await workspace.init();
  sessions = new SessionService({ home, settings: () => workspace.settings() });
  terminals = new TerminalService();
  const rendererRoot = resolve(__dirname, '../renderer');
  protocol.handle('agentdesk', async (request) => {
    const url = new URL(request.url);
    if (url.host !== 'app' || request.method !== 'GET')
      return new Response('Not found', { status: 404 });
    let filename: string;
    try {
      filename = resolve(
        rendererRoot,
        `.${decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname)}`,
      );
    } catch {
      return new Response('Bad request', { status: 400 });
    }
    if (!filename.startsWith(`${rendererRoot}${sep}`))
      return new Response('Not found', { status: 404 });
    const response = await net.fetch(pathToFileURL(filename).toString());
    const headers = new Headers(response.headers);
    headers.set(
      'Content-Security-Policy',
      "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-src 'none'; form-action 'none'",
    );
    return new Response(response.body, { status: response.status, headers });
  });
  session.defaultSession.setPermissionRequestHandler((_contents, _permission, callback) =>
    callback(false),
  );
  session.defaultSession.setPermissionCheckHandler(() => false);
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 940,
    minWidth: 960,
    minHeight: 640,
    title: 'Agent Desk',
    backgroundColor: '#f6f4ef',
    show: false,
    webPreferences: {
      preload: join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
      webSecurity: true,
      spellcheck: false,
    },
  });
  mainWindow.removeMenu();
  mainWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!trustedRenderer(url, developmentUrl)) event.preventDefault();
  });
  mainWindow.webContents.on('will-attach-webview', (event) => event.preventDefault());
  mainWindow.webContents.on('will-prevent-unload', (event) => {
    const choice = dialog.showMessageBoxSync(mainWindow!, {
      type: 'question',
      buttons: ['Keep editing', 'Discard changes and quit'],
      defaultId: 0,
      cancelId: 0,
      title: 'Unsaved changes',
      message: 'Some edits have not been saved.',
      detail: 'Keep editing to save your changes, or discard these unsaved drafts and quit.',
    });
    if (choice === 1) event.preventDefault();
    else allowClose = false;
  });
  registerIpc({
    window: mainWindow,
    workspace,
    sessions,
    terminals,
    secrets,
    home,
    developmentUrl,
  });
  terminals.on('event', (event: TerminalEvent) => {
    if (mainWindow && !mainWindow.isDestroyed())
      mainWindow.webContents.send('desk:terminal-event', event);
  });
  mainWindow.on('close', (event) => {
    const count = terminals?.list().filter((terminal) => terminal.status === 'running').length ?? 0;
    if (allowClose || count === 0) return;
    event.preventDefault();
    if (closeDialogOpen) return;
    closeDialogOpen = true;
    void dialog
      .showMessageBox(mainWindow!, {
        type: 'question',
        buttons: ['Keep working', 'Close agents and quit'],
        defaultId: 0,
        cancelId: 0,
        title: 'Close running agents?',
        message: `${count} terminal${count === 1 ? ' is' : 's are'} still running.`,
        detail: 'Quitting stops these processes. Saved agent sessions remain available to resume.',
      })
      .then((result) => {
        if (result.response === 1) {
          allowClose = true;
          mainWindow?.close();
        }
      })
      .finally(() => {
        closeDialogOpen = false;
      });
  });
  mainWindow.once('ready-to-show', () => mainWindow?.show());
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
  if (developmentUrl) await mainWindow.loadURL(developmentUrl);
  else await mainWindow.loadURL('agentdesk://app/');
}

if (!app.requestSingleInstanceLock()) app.quit();
else {
  app.on('second-instance', () => {
    if (mainWindow?.isMinimized()) mainWindow.restore();
    mainWindow?.focus();
  });
  app
    .whenReady()
    .then(start)
    .catch((error) => {
      dialog.showErrorBox(
        'Agent Desk could not start',
        error instanceof Error ? error.message : String(error),
      );
      app.exit(1);
    });
  app.on('window-all-closed', () => app.quit());
  app.on('will-quit', () => {
    terminals?.dispose();
    sessions?.close();
  });
}
