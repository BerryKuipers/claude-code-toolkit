import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { TerminalEvent, TerminalInfo } from '../src/shared/types';

const native = vi.hoisted(() => ({
  invoke: vi.fn(),
  deliver: undefined as ((event: TerminalEvent) => void) | undefined,
}));

vi.mock('@tauri-apps/api/core', () => ({
  isTauri: () => true,
  invoke: native.invoke,
  Channel: class {
    constructor(listener: (event: TerminalEvent) => void) {
      native.deliver = listener;
    }
  },
}));

import { createTauriApi } from '../src/renderer/tauri';

const terminal: TerminalInfo = {
  id: 'terminal-fixture',
  agent: 'claude',
  title: 'Fixture',
  projectPath: '/fixture',
  startedAt: '2026-01-01T00:00:00Z',
  status: 'running',
};

beforeEach(() => {
  native.invoke.mockReset();
  native.deliver = undefined;
});

describe('Tauri terminal bridge', () => {
  it('subscribes once before launching or taking a snapshot and synchronously removes listeners', async () => {
    let subscribed!: () => void;
    const subscription = new Promise<void>((resolve) => {
      subscribed = resolve;
    });
    native.invoke.mockImplementation((command, payload) => {
      if (command === 'terminal_subscribe') return subscription;
      return Promise.resolve(
        payload.method === 'launch' ? terminal : { data: '', sequence: 0, status: 'running' },
      );
    });
    const api = createTauriApi();
    const first = vi.fn();
    const second = vi.fn();
    const unsubscribe = api.onTerminal(first);
    api.onTerminal(second);
    const launch = api.launch({ agent: 'claude', projectPath: '/fixture' });
    const snapshot = api.terminalSnapshot('terminal-fixture');
    expect(native.invoke.mock.calls.map(([command]) => command)).toEqual(['terminal_subscribe']);
    subscribed();
    expect(await launch).toEqual(terminal);
    await snapshot;
    expect(
      native.invoke.mock.calls.filter(([command]) => command === 'terminal_subscribe'),
    ).toHaveLength(1);
    const event: TerminalEvent = { id: terminal.id, sequence: 1, type: 'data', data: 'ready' };
    native.deliver!(event);
    expect(first).toHaveBeenCalledWith(event);
    expect(second).toHaveBeenCalledWith(event);
    unsubscribe();
    native.deliver!({ ...event, sequence: 2 });
    expect(first).toHaveBeenCalledTimes(1);
    expect(second).toHaveBeenCalledTimes(2);
  });

  it('surfaces a failed subscription and can retry without launching an unobserved process', async () => {
    let attempts = 0;
    native.invoke.mockImplementation((command) => {
      if (command === 'terminal_subscribe') {
        attempts++;
        return attempts === 1
          ? Promise.reject('The desktop stream disconnected.')
          : Promise.resolve();
      }
      return Promise.resolve(terminal);
    });
    const api = createTauriApi();
    await expect(api.launch({ agent: 'claude', projectPath: '/fixture' })).rejects.toThrow(
      'The desktop stream disconnected.',
    );
    expect(native.invoke).toHaveBeenCalledTimes(1);
    await expect(api.launch({ agent: 'claude', projectPath: '/fixture' })).resolves.toEqual(
      terminal,
    );
    expect(attempts).toBe(2);
    expect(native.invoke.mock.calls.filter(([command]) => command === 'desk_invoke')).toHaveLength(
      1,
    );
  });
});
