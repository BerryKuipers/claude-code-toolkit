import { build } from 'esbuild';
import { spawn } from 'node:child_process';
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
  env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' },
});
child.on('error', (error) => {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
});
child.on('exit', (code) => {
  process.exitCode = code ?? 1;
});
