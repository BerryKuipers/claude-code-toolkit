import { describe, expect, it } from 'vitest';
import {
  selectProcessTree,
  summarizeReadings,
  type ProcessReading,
} from './support/process-metrics';

function reading(pid: number, parentPid: number, started: string): ProcessReading {
  return {
    pid,
    parentPid,
    started,
    name: `process-${pid}`,
    cpuMs: 0,
    rssBytes: 100,
    privateBytes: 50,
    pssBytes: null,
  };
}

describe('Resource measurement process ancestry', () => {
  it('excludes the observed Windows compiler orphan whose parent PID was reused by Electron', () => {
    const compiler = {
      ...reading(1660, 2112, '2026-11-16T11:44:30.5139570Z'),
      name: 'vctip.exe',
      rssBytes: 17_174_528,
      privateBytes: 38_723_584,
    };
    const processes = selectProcessTree(
      9044,
      [
        reading(1661, 1660, '2026-11-16T11:54:23.0000000Z'),
        compiler,
        reading(2112, 9044, '2026-11-16T11:54:22.1823430Z'),
        reading(9044, 8160, '2026-11-16T11:54:21.9655230Z'),
        reading(9932, 9044, '2026-11-16T11:54:22.6845100Z'),
        reading(5860, 9932, '2026-11-16T11:54:22.6932460Z'),
      ],
      'win32',
    );
    expect(processes.map(({ pid }) => pid).sort((a, b) => a - b)).toEqual([2112, 5860, 9044, 9932]);
    const summary = summarizeReadings([
      { measuredAt: 'fixture', monotonicMs: 0, processes },
      { measuredAt: 'fixture', monotonicMs: 1000, processes },
    ]);
    expect(summary.averageRssBytes).toBe(400);
    expect(summary.averagePrivateBytes).toBe(200);
    expect(summary.peakProcesses).toBe(4);
  });

  it('preserves Windows sub-millisecond precision and normalizes timezone offsets', () => {
    const processes = selectProcessTree(
      1,
      [
        reading(1, 0, '2026-11-16T11:54:22.1823430Z'),
        reading(2, 1, '2026-11-16T11:54:22.1823429Z'),
        reading(3, 1, '2026-11-16T11:54:22.1823430Z'),
        reading(4, 1, '2026-11-16T12:54:22.1823431+01:00'),
        reading(5, 1, '2026-11-16T12:54:22.1823429+01:00'),
      ],
      'win32',
    );
    expect(processes.map(({ pid }) => pid)).toEqual([1, 3, 4]);
  });

  it('compares Linux boot ticks exactly and validates every parent edge, not only the root', () => {
    const processes = selectProcessTree(
      1,
      [
        reading(6, 4, '9007199254740999'),
        reading(5, 4, '9007199254740996'),
        reading(4, 1, '9007199254740997'),
        reading(3, 1, '9007199254740993'),
        reading(2, 1, '9007199254740992'),
        reading(1, 0, '9007199254740993'),
      ],
      'linux',
    );
    expect(processes.map(({ pid }) => pid).sort((a, b) => a - b)).toEqual([1, 3, 4, 6]);
  });

  it.each([
    ['linux', ''],
    ['linux', 'unknown'],
    ['linux', '12.5'],
    ['win32', ''],
    ['win32', 'unknown'],
    ['win32', '2026-02-30T11:54:22.0000000Z'],
  ] as const)('rejects an unverifiable %s root creation time: %s', (platform, started) => {
    expect(() => selectProcessTree(1, [reading(1, 0, started)], platform)).toThrow(
      'creation time of process 1 could not be verified',
    );
  });

  it.each([
    ['linux', '100'],
    ['win32', '2026-11-16T11:54:22.1823430Z'],
  ] as const)(
    'fails incomplete %s descendant identity without rejecting unrelated inaccessible processes',
    (platform, started) => {
      const root = reading(1, 0, started);
      const unrelated = reading(10, 99, '');
      expect(selectProcessTree(1, [root, unrelated], platform)).toEqual([root]);
      expect(() => selectProcessTree(1, [root, unrelated, reading(2, 1, '')], platform)).toThrow(
        'creation time of process 2 could not be verified',
      );
    },
  );

  it('does not measure a tree whose application process has exited', () => {
    expect(() => selectProcessTree(1, [reading(2, 1, '100')], 'linux')).toThrow(
      'application exited',
    );
  });
});
