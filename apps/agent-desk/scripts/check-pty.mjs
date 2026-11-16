import { build } from 'esbuild';
import { execFile, spawn } from 'node:child_process';
import electron from 'electron';

await build({
  entryPoints: ['tests/pty-smoke.ts'],
  bundle: true,
  platform: 'node',
  format: 'cjs',
  target: 'node24',
  outfile: 'dist/tests/pty-smoke.cjs',
  external: ['node-pty'],
});
const child = spawn(electron, ['dist/tests/pty-smoke.cjs'], {
  stdio: 'inherit',
  env: { ...process.env, ELECTRON_RUN_AS_NODE: '1', AGENT_DESK_SMOKE_NODE: process.execPath },
});
let timedOut = false;
const watchdog = setTimeout(() => {
  timedOut = true;
  process.stderr.write('Native Electron PTY did not finish within 60 seconds.\n');
  if (process.platform === 'win32' && child.pid)
    execFile('taskkill.exe', ['/pid', String(child.pid), '/T', '/F'], () => child.kill('SIGKILL'));
  else child.kill('SIGKILL');
}, 60000);
child.on('error', (error) => {
  clearTimeout(watchdog);
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
});
child.on('exit', (code) => {
  clearTimeout(watchdog);
  process.exitCode = timedOut ? 1 : (code ?? 1);
});
