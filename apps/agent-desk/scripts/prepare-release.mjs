import { execFile } from 'node:child_process';
import { createHash } from 'node:crypto';
import { copyFile, mkdir, readFile, readdir, rm, stat, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { promisify } from 'node:util';

const execute = promisify(execFile);
const appDirectory = path.resolve(import.meta.dirname, '..');
const metadata = JSON.parse(await readFile(path.join(appDirectory, 'package.json'), 'utf8'));
const releaseDirectory = path.join(appDirectory, 'release');
await mkdir(releaseDirectory, { recursive: true });

async function files(directory) {
  const result = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const filename = path.join(directory, entry.name);
    if (entry.isDirectory()) result.push(...(await files(filename)));
    else if (entry.isFile()) result.push(filename);
  }
  return result;
}

const platform = process.platform === 'win32' ? 'windows' : process.platform;
const prefix = `Agent-Desk-${metadata.version}-${platform}-${process.arch}`;
const bundleDirectory = path.join(appDirectory, 'src-tauri', 'target', 'release', 'bundle');
const bundled = await files(bundleDirectory);
const artifacts = [];
const copy = async (source, name) => {
  if (!source) throw new Error(`The expected package ${name} was not produced.`);
  const target = path.join(releaseDirectory, name);
  await copyFile(source, target);
  artifacts.push(target);
};

if (process.platform === 'linux') {
  await copy(
    bundled.find((file) => file.endsWith('.AppImage')),
    `${prefix}.AppImage`,
  );
  await copy(
    bundled.find((file) => file.endsWith('.deb')),
    `${prefix}.deb`,
  );
} else if (process.platform === 'win32') {
  await copy(
    bundled.find((file) => file.endsWith('-setup.exe')),
    `${prefix}-Setup.exe`,
  );
  const staging = path.join(
    process.env.RUNNER_TEMP ?? os.tmpdir(),
    `agent-desk-portable-${process.pid}`,
  );
  await mkdir(staging, { recursive: true });
  try {
    await copyFile(
      path.join(appDirectory, 'src-tauri', 'target', 'release', 'agent-desk.exe'),
      path.join(staging, 'agent-desk.exe'),
    );
    await copyFile(path.join(appDirectory, 'LICENSE'), path.join(staging, 'LICENSE.txt'));
    await writeFile(
      path.join(staging, 'README.txt'),
      `Agent Desk ${metadata.version}\n\nRun agent-desk.exe to open the portable application.\nMicrosoft Edge WebView2 Runtime must be installed. Use the Setup.exe installer if you need automatic runtime installation.\n\nYour coding agents keep their own installations, accounts, and saved sessions. Configure their executable paths in Settings when needed.\n`,
    );
    const archive = path.join(releaseDirectory, `${prefix}.zip`);
    await rm(archive, { force: true });
    await execute(
      'powershell.exe',
      [
        '-NoProfile',
        '-NonInteractive',
        '-Command',
        'Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory($env:AGENT_DESK_PORTABLE_DIRECTORY, $env:AGENT_DESK_PORTABLE_ARCHIVE)',
      ],
      {
        env: {
          ...process.env,
          AGENT_DESK_PORTABLE_DIRECTORY: staging,
          AGENT_DESK_PORTABLE_ARCHIVE: archive,
        },
        windowsHide: true,
        timeout: 60000,
      },
    );
    artifacts.push(archive);
  } finally {
    await rm(staging, { recursive: true, force: true });
  }
} else {
  throw new Error('Release preparation currently supports Linux and Windows.');
}

const manifest = {
  product: 'Agent Desk',
  version: metadata.version,
  runtime: 'Tauri 2 / Rust',
  platform,
  architecture: process.arch,
  commit: process.env.GITHUB_SHA ?? null,
  builtAt: new Date().toISOString(),
  artifacts: await Promise.all(
    artifacts.map(async (file) => ({
      name: path.basename(file),
      bytes: (await stat(file)).size,
      sha256: createHash('sha256')
        .update(await readFile(file))
        .digest('hex'),
    })),
  ),
};
await writeFile(
  path.join(releaseDirectory, 'manifest.json'),
  JSON.stringify(manifest, null, 2) + '\n',
);
for (const artifact of manifest.artifacts)
  console.log(`${artifact.name} (${artifact.bytes} bytes)`);
