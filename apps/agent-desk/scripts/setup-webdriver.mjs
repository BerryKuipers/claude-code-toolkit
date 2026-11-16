import { execFile } from 'node:child_process';
import { access, appendFile, mkdir, readdir, writeFile } from 'node:fs/promises';
import { constants } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { promisify } from 'node:util';

const execute = promisify(execFile);

async function onPath(name) {
  for (const directory of (process.env.PATH ?? process.env.Path ?? '').split(path.delimiter)) {
    const candidate = path.join(directory, name);
    try {
      await access(candidate, process.platform === 'win32' ? constants.F_OK : constants.X_OK);
      return candidate;
    } catch {}
  }
  throw new Error(`${name} is not on PATH.`);
}

async function publish(name, value) {
  if (/[\r\n]/.test(value)) throw new Error(`Invalid environment value for ${name}.`);
  if (process.env.GITHUB_ENV) await appendFile(process.env.GITHUB_ENV, `${name}=${value}\n`);
  console.log(`${name}=${value}`);
}

const tauriDriver =
  process.env.TAURI_DRIVER ??
  (await onPath(process.platform === 'win32' ? 'tauri-driver.exe' : 'tauri-driver'));
const version = await execute(tauriDriver, ['--version'], { timeout: 10000, windowsHide: true });
console.log(version.stdout.trim());
await publish('TAURI_DRIVER', tauriDriver);

if (process.platform === 'linux') {
  await publish(
    'TAURI_NATIVE_DRIVER',
    process.env.TAURI_NATIVE_DRIVER ?? (await onPath('WebKitWebDriver')),
  );
  try {
    const webkitVersion = await execute('pkg-config', ['--modversion', 'webkit2gtk-4.1']);
    await publish('AGENT_DESK_WEBVIEW_VERSION', webkitVersion.stdout.trim());
  } catch {}
} else if (process.platform === 'win32') {
  const versions = new Set();
  for (const key of [
    'HKCU\\SOFTWARE\\Microsoft\\EdgeUpdate\\Clients\\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
    'HKLM\\SOFTWARE\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients\\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
    'HKLM\\SOFTWARE\\Microsoft\\EdgeUpdate\\Clients\\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}',
  ]) {
    try {
      const { stdout } = await execute('reg.exe', ['query', key, '/v', 'pv'], {
        windowsHide: true,
        timeout: 10000,
      });
      const value = stdout.match(/REG_SZ\s+(\d+\.\d+\.\d+\.\d+)/)?.[1];
      if (value && value !== '0.0.0.0') versions.add(value);
    } catch {}
  }
  const locations = [
    process.env['ProgramFiles(x86)'],
    process.env.ProgramFiles,
    process.env.LOCALAPPDATA,
  ]
    .filter(Boolean)
    .map((directory) => path.join(directory, 'Microsoft', 'EdgeWebView', 'Application'));
  let runtimeFolder = process.env.WEBVIEW2_BROWSER_EXECUTABLE_FOLDER;
  let runtimeVersion;
  if (runtimeFolder) {
    await access(path.join(runtimeFolder, 'msedgewebview2.exe'));
    const { stdout } = await execute(
      'powershell.exe',
      [
        '-NoProfile',
        '-NonInteractive',
        '-Command',
        "(Get-Item -LiteralPath (Join-Path $env:WEBVIEW2_BROWSER_EXECUTABLE_FOLDER 'msedgewebview2.exe')).VersionInfo.ProductVersion",
      ],
      { windowsHide: true, timeout: 10000 },
    );
    runtimeVersion = stdout.match(/\d+\.\d+\.\d+\.\d+/)?.[0];
  } else {
    const candidates = [];
    for (const location of locations) {
      for (const directory of await readdir(location).catch(() => [])) {
        if (!/^\d+\.\d+\.\d+\.\d+$/.test(directory)) continue;
        try {
          await access(path.join(location, directory, 'msedgewebview2.exe'));
          candidates.push({ folder: path.join(location, directory), version: directory });
        } catch {}
      }
    }
    candidates.sort((left, right) => {
      const a = left.version.split('.').map(Number);
      const b = right.version.split('.').map(Number);
      for (let index = 0; index < a.length; index++)
        if (a[index] !== b[index]) return b[index] - a[index];
      return 0;
    });
    const chosen = candidates.find((candidate) => versions.has(candidate.version)) ?? candidates[0];
    runtimeFolder = chosen?.folder;
    runtimeVersion = chosen?.version;
  }
  if (!runtimeVersion || !runtimeFolder)
    throw new Error(
      'A WebView2 Runtime was not found. Install the Evergreen Runtime or provide WEBVIEW2_BROWSER_EXECUTABLE_FOLDER.',
    );
  const architecture =
    process.arch === 'arm64' ? 'arm64' : process.arch === 'ia32' ? 'win32' : 'win64';
  const archiveName = `edgedriver_${architecture}.zip`;
  const base = 'https://msedgedriver.microsoft.com';
  let driverVersion = runtimeVersion;
  let response = await fetch(`${base}/${driverVersion}/${archiveName}`, {
    signal: AbortSignal.timeout(60000),
  });
  if (response.status === 404) {
    const latest = await fetch(`${base}/LATEST_RELEASE_${runtimeVersion.split('.')[0]}_WINDOWS`, {
      signal: AbortSignal.timeout(30000),
    });
    if (!latest.ok)
      throw new Error(
        `Could not locate an EdgeDriver for WebView2 ${runtimeVersion}: HTTP ${latest.status}.`,
      );
    const raw = Buffer.from(await latest.arrayBuffer());
    const text = raw.includes(0) ? raw.toString('utf16le') : raw.toString('utf8');
    driverVersion = text.match(/\d+\.\d+\.\d+\.\d+/)?.[0] ?? '';
    if (
      driverVersion.split('.').slice(0, 3).join('.') !==
      runtimeVersion.split('.').slice(0, 3).join('.')
    )
      throw new Error(
        `Available EdgeDriver ${driverVersion} does not match WebView2 ${runtimeVersion}.`,
      );
    response = await fetch(`${base}/${driverVersion}/${archiveName}`, {
      signal: AbortSignal.timeout(60000),
    });
  }
  if (!response.ok) throw new Error(`EdgeDriver download failed: HTTP ${response.status}.`);
  const directory = path.join(
    process.env.RUNNER_TEMP ?? os.tmpdir(),
    'agent-desk-webdriver',
    driverVersion,
  );
  await mkdir(directory, { recursive: true });
  const archive = path.join(directory, archiveName);
  await writeFile(archive, Buffer.from(await response.arrayBuffer()));
  await execute(
    'powershell.exe',
    [
      '-NoProfile',
      '-NonInteractive',
      '-Command',
      'Expand-Archive -LiteralPath $env:AGENT_DESK_DRIVER_ARCHIVE -DestinationPath $env:AGENT_DESK_DRIVER_DIRECTORY -Force',
    ],
    {
      env: {
        ...process.env,
        AGENT_DESK_DRIVER_ARCHIVE: archive,
        AGENT_DESK_DRIVER_DIRECTORY: directory,
      },
      windowsHide: true,
      timeout: 30000,
    },
  );
  const executable = path.join(directory, 'msedgedriver.exe');
  const actual = (await execute(executable, ['--version'], { windowsHide: true, timeout: 10000 }))
    .stdout;
  if (!actual.includes(driverVersion))
    throw new Error(`Downloaded EdgeDriver did not report version ${driverVersion}.`);
  await publish('TAURI_NATIVE_DRIVER', executable);
  await publish('WEBVIEW2_BROWSER_EXECUTABLE_FOLDER', runtimeFolder);
  await publish('AGENT_DESK_WEBVIEW_VERSION', runtimeVersion);
  console.log(actual.trim());
} else {
  throw new Error('Native desktop WebDriver checks support Linux and Windows.');
}
