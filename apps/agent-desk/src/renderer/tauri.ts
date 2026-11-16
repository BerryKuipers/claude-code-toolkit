import { Channel, invoke, isTauri } from '@tauri-apps/api/core';
import type { DeskApi, TerminalEvent } from '../shared/types';

export const IS_TAURI = isTauri();

const MAX_TERMINAL_INPUT_BYTES = 1_000_000;
const MAX_TERMINAL_INPUT_ITEMS = 1024;

interface TerminalWrite {
  data: string;
  bytes: number;
  resolve(): void;
  reject(cause: Error): void;
}

interface TerminalInput {
  pending: TerminalWrite[];
  active?: TerminalWrite;
  bytes: number;
  closing: boolean;
  closePending: boolean;
  closeRequest?: Promise<void>;
}

function asError(cause: unknown): Error {
  if (cause instanceof Error) return cause;
  if (typeof cause === 'string') return new Error(cause);
  if (cause && typeof cause === 'object' && 'message' in cause)
    return new Error(String(cause.message));
  return new Error('The desktop operation could not be completed.');
}

export function createTauriApi(): DeskApi {
  const listeners = new Set<(event: TerminalEvent) => void>();
  const terminalInputs = new Map<string, TerminalInput>();
  const encoder = new TextEncoder();
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
  const inputFor = (id: string): TerminalInput => {
    let state = terminalInputs.get(id);
    if (!state) {
      state = { pending: [], bytes: 0, closing: false, closePending: false };
      terminalInputs.set(id, state);
    }
    return state;
  };
  const releaseInput = (id: string, state: TerminalInput): void => {
    if (
      !state.active &&
      !state.pending.length &&
      !state.closePending &&
      terminalInputs.get(id) === state
    )
      terminalInputs.delete(id);
  };
  const rejectPending = (state: TerminalInput, cause: Error): void => {
    for (const write of state.pending.splice(0)) {
      state.bytes -= write.bytes;
      write.reject(cause);
    }
  };
  const writeNext = (id: string, state: TerminalInput): void => {
    if (state.active || state.closing) return;
    const write = state.pending.shift();
    if (!write) {
      releaseInput(id, state);
      return;
    }
    state.active = write;
    void call<void>('terminalWrite', id, write.data)
      .then(write.resolve, (cause) => {
        const error = asError(cause);
        write.reject(error);
        rejectPending(state, error);
      })
      .finally(() => {
        state.active = undefined;
        state.bytes -= write.bytes;
        if (!state.closing) writeNext(id, state);
        releaseInput(id, state);
      });
  };
  const terminalWrite = (id: string, data: string): Promise<void> => {
    const existing = terminalInputs.get(id);
    if (existing?.closing) return Promise.reject(new Error('The terminal is closing.'));
    const bytes =
      data.length > MAX_TERMINAL_INPUT_BYTES
        ? MAX_TERMINAL_INPUT_BYTES + 1
        : encoder.encode(data).byteLength;
    if (
      bytes + (existing?.bytes ?? 0) > MAX_TERMINAL_INPUT_BYTES ||
      (existing?.pending.length ?? 0) + Number(Boolean(existing?.active)) >=
        MAX_TERMINAL_INPUT_ITEMS
    ) {
      const error = new Error(
        'The terminal input buffer exceeded its byte or item limit. Unsent input was rejected.',
      );
      if (existing) {
        rejectPending(existing, error);
        releaseInput(id, existing);
      }
      return Promise.reject(error);
    }
    const state = existing ?? inputFor(id);
    return new Promise<void>((resolve, reject) => {
      state.pending.push({ data, bytes, resolve, reject });
      state.bytes += bytes;
      writeNext(id, state);
    });
  };
  const terminalClose = (id: string): Promise<void> => {
    const state = inputFor(id);
    if (state.closing && state.closeRequest) return state.closeRequest;
    state.closing = true;
    state.closePending = true;
    const error = new Error('The terminal is closing; input delivery was interrupted.');
    rejectPending(state, error);
    state.active?.reject(error);
    state.closeRequest = call<void>('terminalClose', id)
      .catch((cause) => {
        state.closing = false;
        throw cause;
      })
      .finally(() => {
        state.closePending = false;
        if (!state.closing) state.closeRequest = undefined;
        releaseInput(id, state);
      });
    return state.closeRequest;
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
    terminalWrite,
    terminalResize: (id, cols, rows) => call('terminalResize', id, cols, rows),
    terminalClose,
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
