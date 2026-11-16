import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import assert from 'node:assert/strict';
import { TerminalService } from '../src/main/terminals';
import type { TerminalEvent } from '../src/shared/types';

async function run(): Promise<void> {
  const directory = await mkdtemp(join(tmpdir(), 'agent-desk-pty-'));
  const service = new TerminalService();
  try {
    const file = join(directory, 'interactive.cjs');
    await writeFile(
      file,
      "process.stdout.write('READY\\n');process.stdin.setEncoding('utf8');process.stdin.on('data',data=>{process.stdout.write('ECHO:'+data);process.exit(0)});",
    );
    const events: TerminalEvent[] = [];
    let completed: (() => void) | undefined;
    const exit = new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(
        () => reject(new Error('Native terminal smoke test timed out.')),
        10000,
      );
      completed = () => {
        clearTimeout(timeout);
        resolve();
      };
    });
    service.on('event', (event: TerminalEvent) => {
      events.push(event);
      if (event.type === 'exit') completed?.();
    });
    const terminal = await service.launch(
      { file: process.execPath, prefixArgs: [file] },
      {
        args: [],
        cwd: directory,
        env: {
          ...Object.fromEntries(
            Object.entries(process.env).filter(
              (entry): entry is [string, string] => typeof entry[1] === 'string',
            ),
          ),
          ELECTRON_RUN_AS_NODE: '1',
        },
      },
      { agent: 'claude', title: 'Native PTY smoke' },
    );
    service.resize(terminal.id, 90, 26);
    service.write(terminal.id, 'agent-desk-input\r');
    await exit;
    const snapshot = service.snapshot(terminal.id);
    assert.ok(snapshot.data.includes('READY'));
    assert.ok(snapshot.data.includes('ECHO:agent-desk-input'));
    assert.equal(snapshot.status, 'exited');
    assert.equal(snapshot.exitCode, 0);
    assert.equal(snapshot.sequence, events.at(-1)?.sequence);
    assert.deepEqual(
      events.map((event) => event.sequence),
      events.map((_event, index) => index + 1),
    );
    assert.equal(service.list()[0].status, 'exited');
    service.close(terminal.id);
    assert.equal(service.list().length, 0);
    process.stdout.write(
      'Native Electron PTY: launch, input, output, resize, ordered snapshot, exit and cleanup passed.\n',
    );
  } finally {
    service.dispose();
    await rm(directory, { recursive: true, force: true });
  }
}

void run().catch((error) => {
  process.stderr.write(`${error.stack ?? error}\n`);
  process.exitCode = 1;
});
