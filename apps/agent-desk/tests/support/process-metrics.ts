import { execFile, spawn, type ChildProcess } from 'node:child_process';
import { readFile, readdir } from 'node:fs/promises';
import { promisify } from 'node:util';
import { setTimeout as delay } from 'node:timers/promises';

const execute = promisify(execFile);
let linuxUnits: Promise<{ ticks: number; pageSize: number }> | undefined;

export interface ProcessReading {
  pid: number;
  parentPid: number;
  name: string;
  started: string;
  cpuMs: number;
  rssBytes: number;
  privateBytes: number | null;
  pssBytes: number | null;
}

export interface TreeReading {
  measuredAt: string;
  monotonicMs: number;
  processes: ProcessReading[];
}

async function processList(): Promise<ProcessReading[]> {
  if (process.platform === 'win32') {
    const script = String.raw`
$ErrorActionPreference = 'Stop'
@(Get-CimInstance Win32_Process | ForEach-Object {
  [PSCustomObject]@{
    pid = [int]$_.ProcessId
    parentPid = [int]$_.ParentProcessId
    name = $_.Name
    started = if ($_.CreationDate) { $_.CreationDate.ToUniversalTime().ToString('o') } else { '' }
    cpuMs = ([double]$_.KernelModeTime + [double]$_.UserModeTime) / 10000
    rssBytes = [double]$_.WorkingSetSize
    privateBytes = [double]$_.PrivatePageCount
    pssBytes = $null
  }
}) | ConvertTo-Json -Compress
`;
    const { stdout } = await execute(
      'powershell.exe',
      ['-NoProfile', '-NonInteractive', '-Command', script],
      {
        windowsHide: true,
        maxBuffer: 4 * 1024 * 1024,
        timeout: 15000,
      },
    );
    return JSON.parse(stdout) as ProcessReading[];
  }
  if (process.platform !== 'linux')
    throw new Error('Process-tree measurements support Linux and Windows.');
  linuxUnits ??= Promise.all([
    execute('getconf', ['CLK_TCK']),
    execute('getconf', ['PAGESIZE']),
  ]).then(([ticks, pageSize]) => ({
    ticks: Number(ticks.stdout.trim()),
    pageSize: Number(pageSize.stdout.trim()),
  }));
  const { ticks, pageSize } = await linuxUnits;
  if (!(ticks > 0 && pageSize > 0))
    throw new Error('Could not determine Linux process accounting units.');
  const directories = (await readdir('/proc')).filter((entry) => /^\d+$/.test(entry));
  const results = await Promise.allSettled(
    directories.map(async (pid): Promise<ProcessReading> => {
      const stat = await readFile(`/proc/${pid}/stat`, 'utf8');
      const end = stat.lastIndexOf(')');
      const fields = stat
        .slice(end + 2)
        .trim()
        .split(/\s+/);
      return {
        pid: Number(pid),
        parentPid: Number(fields[1]),
        name: stat.slice(stat.indexOf('(') + 1, end),
        started: fields[19],
        cpuMs: ((Number(fields[11]) + Number(fields[12])) * 1000) / ticks,
        rssBytes: Math.max(0, Number(fields[21])) * pageSize,
        privateBytes: null,
        pssBytes: null,
      };
    }),
  );
  return results.flatMap((result) => (result.status === 'fulfilled' ? [result.value] : []));
}

function processStart(reading: ProcessReading, platform: NodeJS.Platform): bigint {
  if (platform === 'linux' && /^\d+$/.test(reading.started)) return BigInt(reading.started);
  if (platform === 'win32') {
    const parts = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,7}))?(Z|[+-]\d{2}:\d{2})$/.exec(
      reading.started,
    );
    if (parts) {
      const localClock = Date.parse(`${parts[1]}Z`);
      const utc = Date.parse(`${parts[1]}${parts[3]}`);
      if (
        Number.isFinite(utc) &&
        Number.isFinite(localClock) &&
        new Date(localClock).toISOString().slice(0, 19) === parts[1]
      )
        return BigInt(utc) * 10_000n + BigInt((parts[2] ?? '').padEnd(7, '0'));
    }
  }
  throw new Error(`The creation time of process ${reading.pid} could not be verified.`);
}

export function selectProcessTree(
  rootPid: number,
  all: ProcessReading[],
  platform: NodeJS.Platform = process.platform,
): ProcessReading[] {
  const root = all.find((reading) => reading.pid === rootPid);
  if (!root) throw new Error('The application exited before its process tree could be measured.');
  const starts = new Map([[rootPid, processStart(root, platform)]]);
  let changed = true;
  while (changed) {
    changed = false;
    for (const reading of all) {
      const parentStart = starts.get(reading.parentPid);
      if (parentStart === undefined || starts.has(reading.pid)) continue;
      const childStart = processStart(reading, platform);
      if (childStart >= parentStart) {
        starts.set(reading.pid, childStart);
        changed = true;
      }
    }
  }
  return all.filter((reading) => starts.has(reading.pid));
}

export async function sampleProcessTree(rootPid: number): Promise<TreeReading> {
  const processes = selectProcessTree(rootPid, await processList());
  if (process.platform === 'linux') {
    await Promise.all(
      processes.map(async (process) => {
        try {
          const memory = await readFile(`/proc/${process.pid}/smaps_rollup`, 'utf8');
          const value = (name: string): number | null => {
            const match = memory.match(new RegExp(`^${name}:\\s+(\\d+) kB`, 'm'));
            return match ? Number(match[1]) * 1024 : null;
          };
          process.pssBytes = value('Pss');
          const clean = value('Private_Clean');
          const dirty = value('Private_Dirty');
          process.privateBytes = clean === null || dirty === null ? null : clean + dirty;
          process.rssBytes = value('Rss') ?? process.rssBytes;
        } catch {
          process.pssBytes = null;
          process.privateBytes = null;
        }
      }),
    );
  }
  return { measuredAt: new Date().toISOString(), monotonicMs: performance.now(), processes };
}

export function summarizeReadings(readings: TreeReading[]): {
  durationMs: number;
  sampleCount: number;
  cpuPercentOfOneCore: number;
  averageRssBytes: number;
  peakRssBytes: number;
  averagePrivateBytes: number | null;
  peakPrivateBytes: number | null;
  averagePssBytes: number | null;
  peakPssBytes: number | null;
  peakProcesses: number;
} {
  if (readings.length < 2) throw new Error('At least two process samples are required.');
  const durationMs = readings.at(-1)!.monotonicMs - readings[0].monotonicMs;
  const lastCpu = new Map(
    readings[0].processes.map((process) => [`${process.pid}:${process.started}`, process.cpuMs]),
  );
  let cpuMs = 0;
  for (const reading of readings.slice(1)) {
    for (const process of reading.processes) {
      const key = `${process.pid}:${process.started}`;
      const previous = lastCpu.get(key) ?? 0;
      cpuMs += Math.max(0, process.cpuMs - previous);
      lastCpu.set(key, process.cpuMs);
    }
  }
  const totals = (key: 'rssBytes' | 'privateBytes' | 'pssBytes'): Array<number | null> =>
    readings.map((reading) =>
      reading.processes.some((process) => process[key] === null)
        ? null
        : reading.processes.reduce((sum, process) => sum + (process[key] ?? 0), 0),
    );
  const aggregate = (
    values: Array<number | null>,
  ): { average: number | null; peak: number | null } =>
    values.some((value) => value === null)
      ? { average: null, peak: null }
      : {
          average: values.reduce<number>((sum, value) => sum + value!, 0) / values.length,
          peak: Math.max(...(values as number[])),
        };
  const rss = aggregate(totals('rssBytes'));
  const privateMemory = aggregate(totals('privateBytes'));
  const pss = aggregate(totals('pssBytes'));
  return {
    durationMs,
    sampleCount: readings.length,
    cpuPercentOfOneCore: durationMs > 0 ? (cpuMs / durationMs) * 100 : 0,
    averageRssBytes: rss.average!,
    peakRssBytes: rss.peak!,
    averagePrivateBytes: privateMemory.average,
    peakPrivateBytes: privateMemory.peak,
    averagePssBytes: pss.average,
    peakPssBytes: pss.peak,
    peakProcesses: Math.max(...readings.map((reading) => reading.processes.length)),
  };
}

export async function stopMeasuredProcess(child: ChildProcess): Promise<void> {
  if (!child.pid || child.exitCode !== null) return;
  if (process.platform === 'win32') {
    await new Promise<void>((resolve) => {
      const task = spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], { stdio: 'ignore' });
      task.once('error', () => resolve());
      task.once('exit', () => resolve());
    });
    return;
  }
  try {
    process.kill(-child.pid, 'SIGTERM');
  } catch {
    child.kill('SIGTERM');
  }
  const deadline = Date.now() + 3000;
  while (child.exitCode === null && child.signalCode === null && Date.now() < deadline)
    await delay(100);
  if (child.exitCode === null && child.signalCode === null) {
    try {
      process.kill(-child.pid, 'SIGKILL');
    } catch {
      child.kill('SIGKILL');
    }
  }
}
