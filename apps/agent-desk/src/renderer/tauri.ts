import { Channel, invoke, isTauri } from '@tauri-apps/api/core';
import type { DeskApi, TerminalEvent } from '../shared/types';

export const IS_TAURI = isTauri();

function asError(cause: unknown): Error {
  if (cause instanceof Error) return cause;
  if (typeof cause === 'string') return new Error(cause);
  if (cause && typeof cause === 'object' && 'message' in cause)
    return new Error(String(cause.message));
  return new Error('The desktop operation could not be completed.');
}

export function createTauriApi(): DeskApi {
  const listeners = new Set<(event: TerminalEvent) => void>();
  const onEvent = new Channel<TerminalEvent>((event) => {
    for (const listener of listeners) listener(event);
  });
  let subscription: Promise<void> | undefined;
  const ready = (): Promise<void> => {
    subscription ??= invoke<void>('terminal_subscribe', { onEvent }).catch((cause) => {
      subscription = undefined;
      throw asError(cause);
    });
    return subscription;
  };
  const call = async <T>(method: string, ...args: unknown[]): Promise<T> => {
    try {
      return await invoke<T>('desk_invoke', { method, args });
    } catch (cause) {
      throw asError(cause);
    }
  };
  const streamed = async <T>(method: string, ...args: unknown[]): Promise<T> => {
    await ready();
    return await call<T>(method, ...args);
  };
  return {
    bootstrap: () => streamed('bootstrap'),
    sessions: (refresh) => call('sessions', refresh ?? false),
    transcript: (id) => call('transcript', id),
    skills: () => call('skills'),
    readSkill: (id) => call('readSkill', id),
    saveSkill: (input) => call('saveSkill', input),
    createSkill: (input) => call('createSkill', input),
    setSkillEnabled: (input) => call('setSkillEnabled', input),
    configs: () => call('configs'),
    saveConfig: (input) => call('saveConfig', input),
    saveSettings: (settings) => call('saveSettings', settings),
    saveProfile: (profile) => call('saveProfile', profile),
    deleteProfile: (id) => call('deleteProfile', id),
    saveSecret: (input) => call('saveSecret', input),
    deleteSecret: (id) => call('deleteSecret', id),
    models: (id) => call('models', id),
    probe: (id) => call('probe', id),
    launch: (request) => streamed('launch', request),
    terminals: () => call('terminals'),
    terminalSnapshot: (id) => streamed('terminalSnapshot', id),
    terminalWrite: (id, data) => call('terminalWrite', id, data),
    terminalResize: (id, cols, rows) => call('terminalResize', id, cols, rows),
    terminalClose: (id) => call('terminalClose', id),
    onTerminal: (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    pickDirectory: () => call('pickDirectory'),
    revealPath: (path) => call('revealPath', path),
    openExternal: (url) => call('openExternal', url),
    exportSession: (id) => call('exportSession', id),
    proxyStart: () => streamed('proxyStart'),
    proxyAuthenticate: (provider) => streamed('proxyAuthenticate', provider),
    proxyMonitor: (id) => call('proxyMonitor', id),
  };
}

export async function closeDesktop(): Promise<void> {
  try {
    await invoke('desktop_close');
  } catch (cause) {
    throw asError(cause);
  }
}
