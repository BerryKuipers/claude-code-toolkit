import { randomUUID } from 'node:crypto';
import { EventEmitter } from 'node:events';
import { stat } from 'node:fs/promises';
import { spawn, type IPty } from 'node-pty';
import type { TerminalEvent, TerminalInfo, TerminalSnapshot } from '../shared/types';
import type { Executable } from './executables';
import type { LaunchPlan } from './launch-plan';

interface RunningTerminal {
  info: TerminalInfo;
  process: IPty;
  chunks: string[];
  length: number;
  sequence: number;
}

export class TerminalService extends EventEmitter {
  private readonly running = new Map<string, RunningTerminal>();

  async launch(
    executable: Executable,
    plan: LaunchPlan,
    details: Pick<TerminalInfo, 'agent' | 'title' | 'profileId' | 'sessionId'>,
  ): Promise<TerminalInfo> {
    if (this.running.size >= 24)
      throw new Error('Close an existing terminal before opening another one (24 maximum).');
    if (!(await stat(plan.cwd)).isDirectory())
      throw new Error('The project folder no longer exists. Choose an existing folder.');
    const process = spawn(executable.file, [...executable.prefixArgs, ...plan.args], {
      name: 'xterm-256color',
      cols: 110,
      rows: 32,
      cwd: plan.cwd,
      env: plan.env,
      useConpty: true,
    });
    const info: TerminalInfo = {
      id: randomUUID(),
      ...details,
      projectPath: plan.cwd,
      startedAt: new Date().toISOString(),
      status: 'running',
    };
    const terminal: RunningTerminal = { info, process, chunks: [], length: 0, sequence: 0 };
    this.running.set(info.id, terminal);
    process.onData((data) => {
      terminal.chunks.push(data);
      terminal.length += data.length;
      while (terminal.length > 2_000_000 && terminal.chunks.length > 1)
        terminal.length -= terminal.chunks.shift()!.length;
      this.emit('event', {
        id: info.id,
        sequence: ++terminal.sequence,
        type: 'data',
        data,
      } satisfies TerminalEvent);
    });
    process.onExit(({ exitCode }) => {
      terminal.info = { ...terminal.info, status: 'exited', exitCode };
      this.emit('event', {
        id: info.id,
        sequence: ++terminal.sequence,
        type: 'exit',
        exitCode,
      } satisfies TerminalEvent);
    });
    return { ...info };
  }

  list(): TerminalInfo[] {
    return [...this.running.values()].map((terminal) => ({ ...terminal.info }));
  }

  snapshot(id: string): TerminalSnapshot {
    const terminal = this.require(id);
    return {
      data: terminal.chunks.join(''),
      sequence: terminal.sequence,
      status: terminal.info.status,
      exitCode: terminal.info.exitCode,
    };
  }

  write(id: string, data: string): void {
    const terminal = this.require(id);
    if (terminal.info.status !== 'running')
      throw new Error('This terminal has exited. Resume the saved session to continue.');
    if (data.length > 1_000_000) throw new Error('Terminal input is too large.');
    terminal.process.write(data);
  }

  resize(id: string, cols: number, rows: number): void {
    const terminal = this.require(id);
    if (terminal.info.status !== 'running') return;
    if (
      !Number.isInteger(cols) ||
      !Number.isInteger(rows) ||
      cols < 2 ||
      rows < 1 ||
      cols > 600 ||
      rows > 300
    )
      throw new Error('Invalid terminal dimensions.');
    terminal.process.resize(cols, rows);
  }

  close(id: string): void {
    const terminal = this.require(id);
    if (terminal.info.status === 'running') terminal.process.kill();
    this.running.delete(id);
  }

  dispose(): void {
    for (const [id] of this.running) this.close(id);
    this.removeAllListeners();
  }

  private require(id: string): RunningTerminal {
    const terminal = this.running.get(id);
    if (!terminal) throw new Error('This terminal is no longer available.');
    return terminal;
  }
}
