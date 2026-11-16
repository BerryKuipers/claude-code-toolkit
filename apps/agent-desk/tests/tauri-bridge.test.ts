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

function deferred() {
  let resolve!: () => void;
  let reject!: (cause: unknown) => void;
  const promise = new Promise<void>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}

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

  it('preserves keyboard input order with one native write at a time across listener teardown', async () => {
    const input = [...'/status\r'];
    const gates = input.map(() => deferred());
    const sent: string[] = [];
    native.invoke.mockImplementation((_command, payload) => {
      sent.push(payload.args[1]);
      return gates[sent.length - 1].promise;
    });
    const api = createTauriApi();
    const unsubscribe = api.onTerminal(vi.fn());
    const writes = input.map((data) => api.terminalWrite(terminal.id, data));
    const completed = Promise.all(writes);
    unsubscribe();
    api.onTerminal(vi.fn());
    expect(sent).toEqual(['/']);
    for (let index = 0; index < gates.length; index++) {
      expect(sent).toEqual(input.slice(0, index + 1));
      gates[index].resolve();
      if (index + 1 < gates.length) await vi.waitFor(() => expect(sent).toHaveLength(index + 2));
    }
    await completed;
    expect(sent.join('')).toBe('/status\r');
  });

  it('lets independent terminals write while another terminal is blocked', async () => {
    const blocked = deferred();
    native.invoke.mockImplementation((_command, payload) =>
      payload.args[1] === 'blocked' ? blocked.promise : Promise.resolve(),
    );
    const api = createTauriApi();
    const first = api.terminalWrite('first', 'blocked');
    const queued = api.terminalWrite('first', 'queued');
    await api.terminalWrite('second', 'independent');
    expect(native.invoke.mock.calls.map(([, payload]) => payload.args)).toEqual([
      ['first', 'blocked'],
      ['second', 'independent'],
    ]);
    blocked.resolve();
    await Promise.all([first, queued]);
    expect(native.invoke.mock.calls.at(-1)?.[1].args).toEqual(['first', 'queued']);
  });

  it.each(['close-first', 'write-first'])(
    'closes immediately during a blocked write and settles callers without sending queued input (%s)',
    async (order) => {
      const writing = deferred();
      const closing = deferred();
      native.invoke.mockImplementation((_command, payload) => {
        if (payload.method === 'terminalClose') return closing.promise;
        return payload.args[1] === 'blocked'
          ? writing.promise
          : Promise.reject('Unknown terminal.');
      });
      const api = createTauriApi();
      const writes = Promise.allSettled([
        api.terminalWrite(terminal.id, 'blocked'),
        api.terminalWrite(terminal.id, 'unsent'),
      ]);
      const close = api.terminalClose(terminal.id);
      expect(api.terminalClose(terminal.id)).toBe(close);
      expect(native.invoke.mock.calls.map(([, payload]) => payload.method)).toEqual([
        'terminalWrite',
        'terminalClose',
      ]);
      for (const result of await writes) {
        expect(result.status).toBe('rejected');
        if (result.status === 'rejected') expect(result.reason.message).toMatch(/closing/);
      }
      await expect(api.terminalWrite(terminal.id, 'during close')).rejects.toThrow('closing');
      if (order === 'close-first') {
        closing.resolve();
        await close;
        await expect(api.terminalWrite(terminal.id, 'old write still pending')).rejects.toThrow(
          'closing',
        );
        writing.reject('The closed writer was interrupted.');
      } else {
        writing.resolve();
        await writing.promise;
        await expect(api.terminalWrite(terminal.id, 'close still pending')).rejects.toThrow(
          'closing',
        );
        closing.resolve();
        await close;
      }
      await vi.waitFor(async () => {
        await expect(api.terminalWrite(terminal.id, 'after close')).rejects.toThrow(
          'Unknown terminal.',
        );
      });
      expect(native.invoke.mock.calls.map(([, payload]) => payload.args)).toEqual([
        [terminal.id, 'blocked'],
        [terminal.id],
        [terminal.id, 'after close'],
      ]);
    },
  );

  it('allows an explicit close retry after a native close failure', async () => {
    const writing = deferred();
    let closeAttempts = 0;
    native.invoke.mockImplementation((_command, payload) => {
      if (payload.method === 'terminalWrite') return writing.promise;
      return ++closeAttempts === 1 ? Promise.reject('Close failed.') : Promise.resolve();
    });
    const api = createTauriApi();
    const active = Promise.allSettled([api.terminalWrite(terminal.id, 'blocked')]);
    await expect(api.terminalClose(terminal.id)).rejects.toThrow('Close failed.');
    const queued = Promise.allSettled([api.terminalWrite(terminal.id, 'after failed close')]);
    await expect(api.terminalClose(terminal.id)).resolves.toBeUndefined();
    expect((await active)[0].status).toBe('rejected');
    expect((await queued)[0].status).toBe('rejected');
    expect(native.invoke.mock.calls.map(([, payload]) => payload.method)).toEqual([
      'terminalWrite',
      'terminalClose',
      'terminalClose',
    ]);
    writing.resolve();
    await writing.promise;
  });

  it('bounds UTF-8 bytes and explicitly rejects unsent input on overflow', async () => {
    const writing = deferred();
    native.invoke.mockImplementation((_command, payload) =>
      payload.args[1] === 'a' ? writing.promise : Promise.resolve(),
    );
    const api = createTauriApi();
    await expect(api.terminalWrite(terminal.id, '🙂'.repeat(250_001))).rejects.toThrow('buffer');
    expect(native.invoke).not.toHaveBeenCalled();
    const active = api.terminalWrite(terminal.id, 'a');
    const queued = api.terminalWrite(terminal.id, '🙂'.repeat(249_999));
    const queuedResult = Promise.allSettled([queued]);
    await expect(api.terminalWrite(terminal.id, '🙂')).rejects.toThrow('buffer');
    const [result] = await queuedResult;
    expect(result.status).toBe('rejected');
    if (result.status === 'rejected') expect(result.reason.message).toMatch(/buffer/);
    expect(native.invoke).toHaveBeenCalledTimes(1);
    writing.resolve();
    await active;
    await api.terminalWrite(terminal.id, 'fresh input');
    expect(native.invoke.mock.calls.map(([, payload]) => payload.args[1])).toEqual([
      'a',
      'fresh input',
    ]);
  });

  it('bounds outstanding item count even when queued writes contain no bytes', async () => {
    const writing = deferred();
    native.invoke.mockReturnValue(writing.promise);
    const api = createTauriApi();
    const active = api.terminalWrite(terminal.id, 'a');
    const queued = Array.from({ length: 1023 }, () => api.terminalWrite(terminal.id, ''));
    const settled = Promise.allSettled(queued);
    await expect(api.terminalWrite(terminal.id, 'overflow')).rejects.toThrow('buffer');
    const results = await settled;
    expect(results).toHaveLength(1023);
    expect(results.every((result) => result.status === 'rejected')).toBe(true);
    expect(native.invoke).toHaveBeenCalledTimes(1);
    writing.resolve();
    await active;
  });

  it('rejects the active and all unsent callers after a native write failure without retrying', async () => {
    const writing = deferred();
    native.invoke.mockImplementation((_command, payload) =>
      payload.args[1] === 'first' ? writing.promise : Promise.resolve(),
    );
    const api = createTauriApi();
    const writes = Promise.allSettled(
      ['first', 'second', 'third'].map((data) => api.terminalWrite(terminal.id, data)),
    );
    writing.reject('The terminal pipe closed.');
    const results = await writes;
    expect(results).toHaveLength(3);
    for (const result of results) {
      expect(result.status).toBe('rejected');
      if (result.status === 'rejected') {
        expect(result.reason).toBeInstanceOf(Error);
        expect(result.reason.message).toBe('The terminal pipe closed.');
      }
    }
    expect(native.invoke).toHaveBeenCalledTimes(1);
    await api.terminalWrite(terminal.id, 'new explicit input');
    expect(native.invoke).toHaveBeenCalledTimes(2);
  });
});
