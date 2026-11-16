import { spawn } from 'node:child_process';
import { mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import { arch, cpus, platform, release, totalmem } from 'node:os';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { parseArgs } from 'node:util';
import { createDesktopFixture } from '../tests/support/desktop-fixture.ts';
import {
  sampleProcessTree,
  stopMeasuredProcess,
  summarizeReadings,
} from '../tests/support/process-metrics.ts';

const { values } = parseArgs({
  options: {
    binary: { type: 'string' },
    runtime: { type: 'string', default: 'tauri' },
    baseline: { type: 'string', default: process.env.AGENT_DESK_ELECTRON_BASELINE },
    'app-root': { type: 'string' },
    'baseline-root': { type: 'string', default: process.env.AGENT_DESK_ELECTRON_BASELINE_ROOT },
    'baseline-provenance': { type: 'string' },
    'allow-baseline-failure': { type: 'boolean', default: false },
    output: { type: 'string', default: 'test-results/resources.json' },
    'warmup-ms': { type: 'string', default: '20000' },
    'duration-ms': { type: 'string', default: '15000' },
    'interval-ms': { type: 'string', default: '1000' },
  },
});
if (!values.binary)
  throw new Error(
    'Use --binary with the compiled release executable. Optionally add --baseline with the preserved Electron executable.',
  );
if (!['tauri', 'electron'].includes(values.runtime))
  throw new Error('--runtime must be tauri or electron.');
const warmupMs = Number(values['warmup-ms']);
const durationMs = Number(values['duration-ms']);
const intervalMs = Number(values['interval-ms']);
if (
  ![warmupMs, durationMs, intervalMs].every(Number.isInteger) ||
  warmupMs < 5000 ||
  warmupMs > 60000 ||
  durationMs < 3000 ||
  durationMs > 60000 ||
  intervalMs < 100 ||
  intervalMs > 5000
)
  throw new Error('Use warmup 5000–60000 ms, duration 3000–60000 ms, and interval 100–5000 ms.');

async function directoryBytes(directory) {
  let bytes = 0;
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const item = path.join(directory, entry.name);
    if (entry.isDirectory()) bytes += await directoryBytes(item);
    else if (entry.isFile()) bytes += (await stat(item)).size;
  }
  return bytes;
}

async function waitForStartup(runtime, child, fixture, alive, startedAt) {
  const timeoutMs = 90000;
  const deadline = startedAt + timeoutMs;
  let marker;
  let processes = [];
  while (performance.now() < deadline) {
    alive();
    marker = (await readFile(fixture.readiness, 'utf8'))
      .split('\n')
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .find((entry) => entry.method === 'thread/list');
    processes = (await sampleProcessTree(child.pid)).processes;
    const rootName = processes.find((entry) => entry.pid === child.pid)?.name.toLowerCase();
    const browserProcesses = processes.filter((entry) =>
      runtime === 'electron'
        ? entry.name.toLowerCase() === rootName
        : process.platform === 'win32'
          ? entry.name.toLowerCase() === 'msedgewebview2.exe'
          : /^WebKitWebProc/.test(entry.name),
    );
    if (marker && browserProcesses.length >= (runtime === 'electron' ? 2 : 1)) {
      return {
        startupReadinessMs: Math.round(performance.now() - startedAt),
        readiness: {
          condition:
            runtime === 'electron'
              ? 'Fixture app-server thread/list request and at least two Electron executable processes.'
              : process.platform === 'win32'
                ? 'Fixture app-server thread/list request and a descendant msedgewebview2.exe process.'
                : 'Fixture app-server thread/list request and a descendant WebKitWebProcess (WebKitWebProc comm prefix).',
          marker,
          observedAt: new Date().toISOString(),
          browserProcesses: browserProcesses.map(({ pid, name }) => ({ pid, name })),
          timeoutMs,
        },
      };
    }
    await delay(Math.min(1000, Math.max(0, deadline - performance.now())));
  }
  throw new Error(
    `${runtime} startup readiness was not reached within ${timeoutMs} ms. Fixture thread/list observed: ${Boolean(marker)}. Process tree: ${JSON.stringify(processes.map(({ pid, name }) => ({ pid, name })))}.`,
  );
}

async function measure(runtime, executable, packageRoot) {
  const binary = path.resolve(executable);
  const binaryInfo = await stat(binary);
  const fixture = await createDesktopFixture();
  let child;
  let output = '';
  try {
    const args =
      runtime === 'electron' && process.platform === 'linux'
        ? ['--no-sandbox', '--disable-dev-shm-usage']
        : [];
    const startedAt = performance.now();
    child = spawn(binary, args, {
      env: fixture.env,
      cwd: path.dirname(binary),
      detached: process.platform !== 'win32',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    const capture = (data) => {
      output = (output + data.toString()).slice(-12000);
    };
    child.stdout?.on('data', capture);
    child.stderr?.on('data', capture);
    await new Promise((resolve, reject) => {
      child.once('spawn', resolve);
      child.once('error', reject);
    });
    const alive = () => {
      if (child.exitCode !== null || child.signalCode !== null)
        throw new Error(`${runtime} exited before the measurement completed: ${output}`);
    };
    console.log(`Waiting for ${runtime} renderer session indexing and its browser processes.`);
    const readiness = await waitForStartup(runtime, child, fixture, alive, startedAt);
    console.log(
      `${runtime} startup readiness observed after ${readiness.startupReadinessMs} ms; warming for ${warmupMs} ms.`,
    );
    const warmDeadline = Date.now() + warmupMs;
    while (Date.now() < warmDeadline) {
      alive();
      await delay(Math.min(1000, warmDeadline - Date.now()));
    }
    alive();
    if ((await readFile(fixture.invocations, 'utf8')).trim())
      throw new Error('Idle measurement unexpectedly launched an interactive agent.');
    const readings = [await sampleProcessTree(child.pid)];
    const deadline = Date.now() + durationMs;
    while (Date.now() < deadline) {
      await delay(Math.min(intervalMs, deadline - Date.now()));
      alive();
      readings.push(await sampleProcessTree(child.pid));
    }
    const summary = summarizeReadings(readings);
    console.log(
      `${runtime}: ${(summary.averageRssBytes / 1048576).toFixed(1)} MiB process-tree RSS; ${summary.cpuPercentOfOneCore.toFixed(2)}% of one CPU core idle.`,
    );
    return {
      runtime,
      executable: binary,
      executableBytes: binaryInfo.size,
      packagedDirectoryBytes: packageRoot ? await directoryBytes(path.resolve(packageRoot)) : null,
      ...readiness,
      warmupMs,
      summary,
      readings,
    };
  } finally {
    if (child) await stopMeasuredProcess(child);
    await fixture.cleanup();
  }
}

const primary = await measure(values.runtime, values.binary, values['app-root']);
let baseline = null;
let baselineError = null;
if (values.baseline) {
  try {
    baseline = await measure('electron', values.baseline, values['baseline-root']);
  } catch (cause) {
    baselineError = cause instanceof Error ? cause.message : String(cause);
    console.error(`Electron baseline measurement did not complete: ${baselineError}`);
    if (!values['allow-baseline-failure']) process.exitCode = 1;
  }
}
const baselineProvenance = values['baseline-provenance']
  ? JSON.parse(await readFile(values['baseline-provenance'], 'utf8'))
  : null;
const packageManifest = await readFile(
  path.resolve(import.meta.dirname, '../release/manifest.json'),
  'utf8',
)
  .then((content) => JSON.parse(content))
  .catch(() => null);
const report = {
  schemaVersion: 1,
  measuredAt: new Date().toISOString(),
  environment: {
    os: platform(),
    osRelease: release(),
    arch: arch(),
    logicalCpus: cpus().length,
    cpu: cpus()[0]?.model,
    physicalMemoryBytes: totalmem(),
    node: process.version,
    webviewVersion: process.env.AGENT_DESK_WEBVIEW_VERSION ?? null,
  },
  scenario: {
    name: 'Warmed idle desktop',
    seed: 'The same two recorded sessions and local fixture agents as the native desktop tests; fresh equivalent data directories for each runtime.',
    automaticHistoryRefreshSeconds: 0,
    interactiveAgents: 0,
    readiness:
      'Wait up to 90 seconds for the fixture app-server thread/list request from renderer session indexing and the runtime browser processes; only then begin the configured warmup and idle measurement.',
  },
  metricNotes: [
    'Includes the application and observed descendant processes, including WebView and discovery helpers. Excludes the measurement process and test drivers.',
    'RSS sums shared pages across processes; Linux PSS is the more representative total when every process allows reading smaps_rollup. Missing PSS or private readings remain null.',
    process.platform === 'win32'
      ? 'Windows private memory is committed private bytes, not a resident-memory measurement.'
      : 'Linux private memory is private resident clean and dirty pages.',
    'CPU is sampled user plus kernel CPU time as a percentage of one logical core; very short lived processes between samples can be missed.',
    'This is an idle desktop measurement. No claim is made about GPU memory, model inference, cold startup, or total external agent resource usage.',
    'WebView2/WebKit are shared system dependencies. Their installed runtime size is not included in application directory sizes.',
  ],
  primary,
  baseline,
  baselineError,
  baselineProvenance,
  packageManifest,
  commit: process.env.GITHUB_SHA ?? null,
};
const target = path.resolve(values.output);
await mkdir(path.dirname(target), { recursive: true });
await writeFile(target, JSON.stringify(report, null, 2) + '\n');
console.log(`Resource measurements saved to ${target}`);
