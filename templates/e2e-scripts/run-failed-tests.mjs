#!/usr/bin/env node
/**
 * Run a curated list of failing Playwright tests one by one.
 *
 * - Reads e2e/failed-tests.json
 * - Runs each test (file + title) sequentially
 * - Removes tests that pass from the JSON
 * - Keeps tests that are still failing, with lastStatus/lastRunAt
 *
 * Usage:
 *   node scripts/run-failed-tests.mjs
 *
 * Notes:
 * - Uses `npx playwright test` under the hood
 * - Defaults to `--project=<project>` from the JSON (chromium for most)
 * - Sets `E2E_SKIP_DB_SYNC=1` by default for faster E2E runs
 */

import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const FAILED_FILE = resolve('e2e/failed-tests.json');

function parseArgs(argv) {
  const args = { limit: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--limit') {
      const v = parseInt(argv[i + 1] || '', 10);
      if (!Number.isNaN(v) && v > 0) {
        args.limit = v;
      }
    }
  }
  return args;
}

function loadFailedTests() {
  if (!existsSync(FAILED_FILE)) {
    console.error(`Failed tests file not found: ${FAILED_FILE}`);
    process.exit(1);
  }

  try {
    const raw = readFileSync(FAILED_FILE, 'utf-8');
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed.tests) ? parsed.tests : [];
  } catch (err) {
    console.error('Error reading failed-tests.json:', err);
    process.exit(1);
  }
}

function saveFailedTests(tests) {
  const payload = { tests };
  writeFileSync(FAILED_FILE, JSON.stringify(payload, null, 2));
}

function runTest(test) {
  const project = test.project || 'chromium';
  const args = [
    'playwright',
    'test',
    test.file,
    '-g',
    test.title,
    '--project',
    project,
    '--reporter',
    'json',
  ];

  console.log('\n──────────────────────────────────────────────');
  console.log(`▶ Running: ${test.id}`);
  console.log(`   file:   ${test.file}`);
  console.log(`   title:  ${test.title}`);
  console.log(`   proj:   ${project}`);
  console.log('──────────────────────────────────────────────\n');

  const env = {
    ...process.env,
    E2E_SKIP_DB_SYNC: process.env.E2E_SKIP_DB_SYNC || '1',
    // Prevent HTML report server from blocking the process
    PW_TEST_HTML_REPORT_OPEN: 'never',
    PLAYWRIGHT_HTML_REPORT: 'none',
  };

  const result = spawnSync('npx', args, {
    stdio: 'inherit',
    env,
    shell: process.platform === 'win32',
  });
  const status = result.status ?? result.signal ?? 1;
  return status === 0;
}

function main() {
  const { limit } = parseArgs(process.argv);
  const tests = loadFailedTests();
  if (tests.length === 0) {
    console.log('No failing tests listed in e2e/failed-tests.json.');
    return;
  }

  const maxBatch = limit || tests.length;
  const toRun = tests.slice(0, maxBatch);
  const notRun = tests.slice(maxBatch);

  console.log(
      `Running up to ${maxBatch} test(s) this batch (of ${tests.length} total listed).`
  );

  const stillFailing = [];

  for (const test of toRun) {
    const now = new Date().toISOString();
    try {
      const passed = runTest(test);
      if (passed) {
        console.log(`✅ Passed: ${test.id}`);
      } else {
        console.log(`❌ Still failing: ${test.id}`);
        stillFailing.push({
          ...test,
          lastStatus: 'failed',
          lastRunAt: now,
        });
      }
    } catch (err) {
      console.error(`⚠️  Error running ${test.id}:`, err);
      stillFailing.push({
        ...test,
        lastStatus: 'error',
        lastError: String(err),
        lastRunAt: now,
      });
    }
  }

  // Tests we didn't touch at all remain as-is.
  const updated = [...stillFailing, ...notRun];
  saveFailedTests(updated);

  console.log('\nSummary:');
  console.log(`  Original failing tests: ${tests.length}`);
  console.log(`  Still failing after this run: ${updated.length}`);

  if (updated.length > 0) {
    console.log('  Remaining failing test IDs:');
    for (const t of updated) {
      console.log(`   - ${t.id}`);
    }
    process.exitCode = 1;
  } else {
    console.log('  All listed tests passed 🎉');
  }
}

main();
