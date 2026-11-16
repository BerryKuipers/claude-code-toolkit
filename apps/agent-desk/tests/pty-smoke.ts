import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import assert from 'node:assert/strict';
import { Terminal } from '@xterm/headless';
import { TerminalService } from '../src/main/terminals';
import type { TerminalEvent } from '../src/shared/types';

async function waitFor(check: () => boolean, diagnostic: () => string): Promise<void> {
  const deadline = Date.now() + 15000;
  while (!check()) {
    if (Date.now() > deadline) throw new Error(diagnostic());
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
}

async function run(): Promise<void> {
  const directory = await mkdtemp(join(tmpdir(), 'agent-desk-pty-'));
  const service = new TerminalService();
  const screen = new Terminal({ cols: 110, rows: 32, allowProposedApi: true });
  let terminalId: string | undefined;
  const visibleText = (): string =>
    Array.from(
      { length: screen.buffer.active.length },
      (_, index) => screen.buffer.active.getLine(index)?.translateToString(true) ?? '',
    ).join('\n');
  const diagnostic = (): string =>
    JSON.stringify({
      snapshot: terminalId ? service.snapshot(terminalId) : undefined,
      screen: visibleText(),
    });
  screen.onData((data) => {
    if (terminalId && service.snapshot(terminalId).status === 'running')
      service.write(terminalId, data);
  });
  try {
    const node = process.env.AGENT_DESK_SMOKE_NODE;
    assert.ok(node, 'Run this check through scripts/check-pty.mjs.');
    const file = join(directory, 'interactive.cjs');
    await writeFile(
      file,
      "const r=require('node:readline').createInterface({input:process.stdin});process.stdout.write('READY\\n');r.once('line',line=>process.stdout.write('ECHO:'+line+'\\n',()=>process.exit(0)));",
    );
    const events: TerminalEvent[] = [];
    service.on('event', (event: TerminalEvent) => {
      events.push(event);
      if (event.type === 'data' && event.data !== undefined) screen.write(event.data);
    });
    const env = Object.fromEntries(
      Object.entries(process.env).filter(
        (entry): entry is [string, string] => typeof entry[1] === 'string',
      ),
    );
    delete env.ELECTRON_RUN_AS_NODE;
    process.stdout.write('Native Electron PTY: starting an interactive Node CLI.\n');
    const terminal = await service.launch(
      { file: node, prefixArgs: [file] },
      { args: [], cwd: directory, env },
      { agent: 'claude', title: 'Native PTY smoke' },
    );
    terminalId = terminal.id;
    await waitFor(
      () => visibleText().includes('READY') || service.snapshot(terminal.id).status === 'exited',
      diagnostic,
    );
    assert.ok(visibleText().includes('READY'), diagnostic());
    screen.resize(90, 26);
    service.resize(terminal.id, 90, 26);
    service.write(terminal.id, 'agent-desk-input\r');
    process.stdout.write('Native Electron PTY: input sent; waiting for output and exit.\n');
    await waitFor(() => service.snapshot(terminal.id).status === 'exited', diagnostic);
    await new Promise<void>((resolve) => screen.write('', resolve));
    const snapshot = service.snapshot(terminal.id);
    assert.equal(snapshot.exitCode, 0, diagnostic());
    assert.ok(visibleText().includes('ECHO:agent-desk-input'), diagnostic());
    assert.equal(snapshot.sequence, events.at(-1)?.sequence);
    assert.deepEqual(
      events.map((event) => event.sequence),
      events.map((_event, index) => index + 1),
    );
    assert.equal(events.filter((event) => event.type === 'exit').length, 1);
    assert.equal(service.list()[0].status, 'exited');
    terminalId = undefined;
    service.close(terminal.id);
    assert.equal(service.list().length, 0);
    process.stdout.write(
      'Native Electron PTY: launch, input, output, resize, ordered snapshot, exit and cleanup passed.\n',
    );
  } finally {
    terminalId = undefined;
    service.dispose();
    screen.dispose();
    await rm(directory, { recursive: true, force: true });
  }
}

void run().catch((error) => {
  process.stderr.write(`${error.stack ?? error}\n`);
  process.exitCode = 1;
});
