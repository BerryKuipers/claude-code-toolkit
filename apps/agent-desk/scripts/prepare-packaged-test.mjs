import { execFile } from 'node:child_process';
import { access, appendFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { constants } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { promisify } from 'node:util';

const execute = promisify(execFile);
const appDirectory = path.resolve(import.meta.dirname, '..');
const releaseDirectory = path.join(appDirectory, 'release');
const manifest = JSON.parse(await readFile(path.join(releaseDirectory, 'manifest.json'), 'utf8'));
const packages = manifest.artifacts.map((artifact) => artifact.name);
const destination = path.join(
  process.env.RUNNER_TEMP ?? os.tmpdir(),
  `agent-desk-installed-${process.pid}`,
);
await mkdir(destination, { recursive: true });
let binary;
let mode;
let packageName;

if (process.platform === 'win32') {
  packageName = packages.find((name) => name.endsWith('-Setup.exe'));
  if (!packageName) throw new Error('The Windows installer was not prepared.');
  await execute(path.join(releaseDirectory, packageName), ['/S', `/D=${destination}`], {
    windowsHide: true,
    timeout: 180000,
  });
  binary = path.join(destination, 'agent-desk.exe');
  await access(binary);
  mode = 'Windows NSIS installer, silent installation into an isolated directory';
} else if (process.platform === 'linux') {
  packageName = packages.find((name) => name.endsWith('.AppImage'));
  if (!packageName) throw new Error('The Linux AppImage was not prepared.');
  const env = { ...process.env };
  delete env.APPIMAGE_EXTRACT_AND_RUN;
  await execute(path.join(releaseDirectory, packageName), ['--appimage-extract'], {
    cwd: destination,
    env,
    timeout: 60000,
    maxBuffer: 16 * 1024 * 1024,
  });
  binary = path.join(destination, 'squashfs-root', 'AppRun');
  await access(binary, constants.X_OK);
  mode = 'Linux AppImage extracted without FUSE, launched through its packaged AppRun entrypoint';
} else {
  throw new Error('Packaged native tests support Linux and Windows.');
}

for (const [name, value] of Object.entries({
  AGENT_DESK_BINARY: binary,
  AGENT_DESK_PACKAGED: '1',
})) {
  if (/[\r\n]/.test(value)) throw new Error('Invalid packaged test path.');
  if (process.env.GITHUB_ENV) await appendFile(process.env.GITHUB_ENV, `${name}=${value}\n`);
  console.log(`${name}=${value}`);
}
const evidence = path.join(appDirectory, 'test-results', 'packaged');
await mkdir(evidence, { recursive: true });
await writeFile(
  path.join(evidence, 'installation.json'),
  JSON.stringify(
    {
      package: packageName,
      mode,
      binary,
      preparedAt: new Date().toISOString(),
    },
    null,
    2,
  ) + '\n',
);
console.log(mode);
