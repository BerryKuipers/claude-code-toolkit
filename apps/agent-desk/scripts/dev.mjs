import { spawn } from 'node:child_process';
import { createServer } from 'vite';
import electron from 'electron';

await import('./build-main.mjs');
const server = await createServer();
await server.listen();
server.printUrls();
const child = spawn(electron, ['.'], {
  stdio: 'inherit',
  env: { ...process.env, AGENT_DESK_DEV_URL: 'http://127.0.0.1:5178' },
});
const stop = async (code) => {
  await server.close();
  process.exit(code ?? 0);
};
child.on('exit', stop);
child.on('error', (error) => {
  process.stderr.write(`${error.message}\n`);
  void stop(1);
});
for (const signal of ['SIGINT', 'SIGTERM'])
  process.on(signal, () => {
    child.kill(signal);
  });
