import { EventEmitter } from 'node:events';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { runInNewContext } from 'node:vm';
import type { IPty } from 'node-pty';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const require = createRequire(import.meta.url);
const library = path.join(path.dirname(require.resolve('node-pty/package.json')), 'lib');

class MockSocket extends EventEmitter {
  readable = true;
  writable = true;
  destroyed = false;
  write = vi.fn();

  setEncoding(): this {
    return this;
  }

  destroy(): this {
    if (!this.destroyed) {
      this.destroyed = true;
      queueMicrotask(() => this.emit('close'));
    }
    return this;
  }
}

class MockConnection {
  private readonly events = new EventEmitter();
  dispose = vi.fn();
  connectSocket = vi.fn();

  onReady(listener: () => void): void {
    this.events.on('ready', listener);
  }

  onError(listener: (error: Error) => void): void {
    this.events.on('connectionError', listener);
  }

  ready(): void {
    this.events.emit('ready');
  }

  fail(): void {
    this.events.emit('connectionError', new Error('The worker connection failed.'));
  }
}

function createTerminal() {
  const sockets: MockSocket[] = [];
  const connections: MockConnection[] = [];
  let nativeExit: ((code: number) => void) | undefined;
  const native = {
    startProcess: vi.fn(() => ({ pty: 7, fd: -1, conin: 'input-pipe', conout: 'output-pipe' })),
    connect: vi.fn(
      (
        _id: number,
        _command: string,
        _cwd: string,
        _env: string[],
        _useDll: boolean,
        onExit: (code: number) => void,
      ) => {
        nativeExit = onExit;
        return { pid: 4321 };
      },
    ),
    kill: vi.fn(),
    resize: vi.fn(),
    clear: vi.fn(),
  };
  const cache = new Map<string, { exports: Record<string, unknown> }>();
  const load = (filename: string): Record<string, unknown> => {
    const existing = cache.get(filename);
    if (existing) return existing.exports;
    const module = { exports: {} };
    cache.set(filename, module);
    const localRequire = (name: string): unknown => {
      if (name === './utils')
        return { assign: Object.assign, loadNativeModule: () => ({ module: native }) };
      if (name === 'fs') return { openSync: vi.fn(() => 100) };
      if (name === 'net') {
        return {
          Socket: class extends MockSocket {
            constructor() {
              super();
              sockets.push(this);
            }
          },
        };
      }
      if (name === 'child_process') return { fork: vi.fn() };
      if (name === './windowsConoutConnection') {
        return {
          ConoutConnection: class extends MockConnection {
            constructor() {
              super();
              connections.push(this);
            }
          },
        };
      }
      if (name.startsWith('.')) return load(path.resolve(path.dirname(filename), `${name}.js`));
      return require(name);
    };
    runInNewContext(
      readFileSync(filename, 'utf8'),
      {
        module,
        exports: module.exports,
        require: localRequire,
        __dirname: path.dirname(filename),
        __filename: filename,
        process: { env: {}, platform: 'win32', arch: 'x64', kill: vi.fn() },
        console,
        setTimeout,
        clearTimeout,
      },
      { filename, timeout: 1000 },
    );
    return module.exports;
  };
  const { WindowsTerminal } = load(path.join(library, 'windowsTerminal.js')) as {
    WindowsTerminal: new (
      file: string,
      args: string[],
      options: { cwd: string; env: Record<string, string>; useConptyDll: boolean },
    ) => IPty;
  };
  const terminal = new WindowsTerminal('node.exe', ['fixture.cjs'], {
    cwd: process.cwd(),
    env: { TERM: 'xterm-256color' },
    useConptyDll: true,
  });
  const [output, input] = sockets;
  const [connection] = connections;
  const events: Array<{ type: 'data'; data: string } | { type: 'exit'; code: number }> = [];
  terminal.onData((data) => events.push({ type: 'data', data }));
  terminal.onExit(({ exitCode }) => events.push({ type: 'exit', code: exitCode }));
  return {
    terminal,
    native,
    output,
    input,
    connection,
    events,
    start() {
      connection.ready();
      if (!output.destroyed) output.emit('connect');
    },
    exit(code: number) {
      if (!nativeExit) throw new Error('The native process has not connected.');
      nativeExit(code);
    },
    async closeOutput() {
      output.destroy();
      await Promise.resolve();
    },
  };
}

beforeEach(() => vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] }));
afterEach(() => {
  vi.clearAllTimers();
  vi.useRealTimers();
});

describe('patched Windows terminal lifecycle', () => {
  it('drains final data before reporting a native exit and then releases input and the worker', async () => {
    const fixture = createTerminal();
    fixture.start();
    fixture.output.emit('data', 'first output\r\n');
    fixture.exit(23);
    expect(fixture.events).toEqual([{ type: 'data', data: 'first output\r\n' }]);
    expect(fixture.input.destroyed).toBe(false);
    expect(fixture.connection.dispose).not.toHaveBeenCalled();
    fixture.output.emit('data', 'final output\r\n');
    await fixture.closeOutput();
    expect(fixture.events).toEqual([
      { type: 'data', data: 'first output\r\n' },
      { type: 'data', data: 'final output\r\n' },
      { type: 'exit', code: 23 },
    ]);
    expect(fixture.input.destroyed).toBe(true);
    expect(fixture.connection.dispose).toHaveBeenCalledTimes(1);
    fixture.output.emit('close');
    fixture.exit(23);
    expect(fixture.events.filter((event) => event.type === 'exit')).toHaveLength(1);
    expect(fixture.native.kill).not.toHaveBeenCalled();
  });

  it('waits for the native exit code when the output pipe closes first', async () => {
    const fixture = createTerminal();
    fixture.start();
    fixture.output.emit('data', 'all output');
    await fixture.closeOutput();
    expect(fixture.events).toEqual([{ type: 'data', data: 'all output' }]);
    expect(fixture.input.destroyed).toBe(true);
    expect(fixture.connection.dispose).toHaveBeenCalledTimes(1);
    fixture.exit(17);
    expect(fixture.events.at(-1)).toEqual({ type: 'exit', code: 17 });
    fixture.output.emit('close');
    expect(fixture.events.filter((event) => event.type === 'exit')).toHaveLength(1);
  });

  it('reports a process creation failure once and releases both pipes and the worker', async () => {
    const fixture = createTerminal();
    fixture.native.connect.mockImplementationOnce(() => {
      throw new Error('Cannot create process, error code: 2');
    });
    fixture.start();
    await Promise.resolve();
    expect(fixture.events).toEqual([{ type: 'exit', code: 2 }]);
    expect(fixture.input.destroyed).toBe(true);
    expect(fixture.output.destroyed).toBe(true);
    expect(fixture.connection.dispose).toHaveBeenCalled();
    expect(fixture.native.kill).toHaveBeenCalledWith(7, true);
    fixture.connection.fail();
    expect(fixture.events).toHaveLength(1);
  });

  it('cleans up a failed worker before the native process has connected', async () => {
    const fixture = createTerminal();
    fixture.connection.fail();
    await Promise.resolve();
    expect(fixture.native.connect).not.toHaveBeenCalled();
    expect(fixture.native.kill).toHaveBeenCalledWith(7, true);
    expect(fixture.input.destroyed).toBe(true);
    expect(fixture.output.destroyed).toBe(true);
    expect(fixture.connection.dispose).toHaveBeenCalled();
    expect(fixture.events).toEqual([{ type: 'exit', code: -1 }]);
    fixture.connection.ready();
    expect(fixture.native.connect).not.toHaveBeenCalled();
  });

  it('bounds startup waits and ignores readiness delivered after a connection timeout', async () => {
    const fixture = createTerminal();
    vi.advanceTimersByTime(5000);
    await Promise.resolve();
    expect(fixture.events).toEqual([{ type: 'exit', code: -1 }]);
    expect(fixture.input.destroyed).toBe(true);
    expect(fixture.output.destroyed).toBe(true);
    expect(fixture.connection.dispose).toHaveBeenCalled();
    fixture.connection.ready();
    expect(fixture.native.connect).not.toHaveBeenCalled();
    expect(fixture.events).toHaveLength(1);
  });

  it('kills a connected silent process without waiting for its first output', async () => {
    const fixture = createTerminal();
    fixture.start();
    fixture.terminal.kill();
    fixture.terminal.kill();
    expect(fixture.native.kill).toHaveBeenCalledTimes(1);
    expect(fixture.native.kill).toHaveBeenCalledWith(7, true);
    fixture.exit(1);
    await fixture.closeOutput();
    expect(fixture.events).toEqual([{ type: 'exit', code: 1 }]);
  });

  it('defers an early kill until connection and discards queued input and resize operations', async () => {
    const fixture = createTerminal();
    fixture.terminal.write('should not reach the child');
    fixture.terminal.resize(90, 30);
    fixture.terminal.kill();
    fixture.terminal.kill();
    expect(fixture.native.kill).not.toHaveBeenCalled();
    fixture.start();
    expect(fixture.native.connect).toHaveBeenCalledTimes(1);
    expect(fixture.native.kill).toHaveBeenCalledTimes(1);
    fixture.output.emit('data', 'late output');
    expect(fixture.input.write).not.toHaveBeenCalled();
    expect(fixture.native.resize).not.toHaveBeenCalled();
    fixture.exit(1);
    await fixture.closeOutput();
    expect(fixture.events).toEqual([
      { type: 'data', data: 'late output' },
      { type: 'exit', code: 1 },
    ]);
  });
});
