import { contextBridge, ipcRenderer } from 'electron';
import type { DeskApi, TerminalEvent } from '../shared/types';

const invoke = <T>(name: string, ...args: unknown[]): Promise<T> =>
  ipcRenderer.invoke(`desk:${name}`, ...args);

const api: DeskApi = {
  bootstrap: () => invoke('bootstrap'),
  sessions: (refresh) => invoke('sessions', refresh),
  transcript: (id) => invoke('transcript', id),
  skills: () => invoke('skills'),
  readSkill: (id) => invoke('readSkill', id),
  saveSkill: (input) => invoke('saveSkill', input),
  createSkill: (input) => invoke('createSkill', input),
  setSkillEnabled: (input) => invoke('setSkillEnabled', input),
  configs: () => invoke('configs'),
  saveConfig: (input) => invoke('saveConfig', input),
  saveSettings: (settings) => invoke('saveSettings', settings),
  saveProfile: (profile) => invoke('saveProfile', profile),
  deleteProfile: (id) => invoke('deleteProfile', id),
  saveSecret: (input) => invoke('saveSecret', input),
  deleteSecret: (id) => invoke('deleteSecret', id),
  models: (id) => invoke('models', id),
  probe: (id) => invoke('probe', id),
  launch: (request) => invoke('launch', request),
  terminals: () => invoke('terminals'),
  terminalSnapshot: (id) => invoke('terminalSnapshot', id),
  terminalWrite: (id, data) => invoke('terminalWrite', id, data),
  terminalResize: (id, cols, rows) => invoke('terminalResize', id, cols, rows),
  terminalClose: (id) => invoke('terminalClose', id),
  onTerminal: (listener) => {
    const handler = (_event: Electron.IpcRendererEvent, event: TerminalEvent): void =>
      listener(event);
    ipcRenderer.on('desk:terminal-event', handler);
    return () => {
      ipcRenderer.removeListener('desk:terminal-event', handler);
    };
  },
  pickDirectory: () => invoke('pickDirectory'),
  revealPath: (path) => invoke('revealPath', path),
  openExternal: (url) => invoke('openExternal', url),
  exportSession: (id) => invoke('exportSession', id),
  proxyStart: () => invoke('proxyStart'),
  proxyAuthenticate: (provider) => invoke('proxyAuthenticate', provider),
  proxyMonitor: (id) => invoke('proxyMonitor', id),
};

contextBridge.exposeInMainWorld('desk', api);
