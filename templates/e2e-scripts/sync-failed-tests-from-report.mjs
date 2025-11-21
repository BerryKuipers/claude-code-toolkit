#!/usr/bin/env node
/**
 * Sync failed tests from Playwright JSON reporter output.
 *
 * Reads test-results/{folder}/results.json files and updates e2e/failed-tests.json
 * to reflect current test status. Supports merging multiple folders from parallel agents.
 *
 * Usage:
 *   node scripts/sync-failed-tests-from-report.mjs --all
 *   node scripts/sync-failed-tests-from-report.mjs --folder test-results/api-smoke-test
 *   node scripts/sync-failed-tests-from-report.mjs test-results/results.json
 */

import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { resolve, join, basename } from 'node:path';

const FAILED_FILE = resolve('e2e/failed-tests.json');
const TEST_RESULTS_DIR = resolve('test-results');

function parseArgs(argv) {
  const args = { all: false, folder: null, file: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--all') {
      args.all = true;
    } else if (a === '--folder') {
      args.folder = argv[i + 1];
      i++;
    } else if (a.endsWith('.json')) {
      args.file = a;
    }
  }
  return args;
}

function findJsonReports() {
  const reports = [];

  if (!existsSync(TEST_RESULTS_DIR)) {
    return reports;
  }

  // Check for results.json directly in test-results
  const directReport = join(TEST_RESULTS_DIR, 'results.json');
  if (existsSync(directReport)) {
    reports.push(directReport);
  }

  // Check subdirectories for results.json
  const entries = readdirSync(TEST_RESULTS_DIR);
  for (const entry of entries) {
    const entryPath = join(TEST_RESULTS_DIR, entry);
    if (statSync(entryPath).isDirectory()) {
      const reportPath = join(entryPath, 'results.json');
      if (existsSync(reportPath)) {
        reports.push(reportPath);
      }
    }
  }

  return reports;
}

function parsePlaywrightJson(reportPath) {
  const failures = [];

  try {
    const raw = readFileSync(reportPath, 'utf-8');
    const report = JSON.parse(raw);

    // Playwright JSON format has suites with specs
    const processSpec = (spec, file) => {
      for (const test of spec.tests || []) {
        for (const result of test.results || []) {
          if (result.status === 'failed' || result.status === 'timedOut') {
            failures.push({
              id: `${basename(file)}:${spec.title}`,
              file: file,
              title: spec.title,
              project: test.projectName || 'chromium',
              lastStatus: result.status,
              lastRunAt: new Date().toISOString(),
              error: result.error?.message?.slice(0, 500),
            });
          }
        }
      }
    };

    const processSuite = (suite, parentFile = '') => {
      const file = suite.file || parentFile;

      for (const spec of suite.specs || []) {
        processSpec(spec, file);
      }

      for (const childSuite of suite.suites || []) {
        processSuite(childSuite, file);
      }
    };

    for (const suite of report.suites || []) {
      processSuite(suite);
    }

  } catch (err) {
    console.error(`Error parsing ${reportPath}:`, err.message);
  }

  return failures;
}

function loadExistingFailedTests() {
  if (!existsSync(FAILED_FILE)) {
    return [];
  }
  try {
    const raw = readFileSync(FAILED_FILE, 'utf-8');
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed.tests) ? parsed.tests : [];
  } catch {
    return [];
  }
}

function saveFailedTests(tests) {
  const payload = { tests, lastSynced: new Date().toISOString() };
  writeFileSync(FAILED_FILE, JSON.stringify(payload, null, 2));
}

function mergeFailures(existing, newFailures) {
  const byId = new Map();

  // Start with existing
  for (const t of existing) {
    byId.set(t.id, t);
  }

  // Update/add new failures
  for (const t of newFailures) {
    byId.set(t.id, t);
  }

  return Array.from(byId.values());
}

function main() {
  const args = parseArgs(process.argv);
  let reportPaths = [];

  if (args.all) {
    reportPaths = findJsonReports();
    if (reportPaths.length === 0) {
      console.log('No JSON reports found in test-results/');
      console.log('Run tests with: --reporter=json --output-folder=test-results/{suite-name}');
      process.exit(1);
    }
    console.log(`Found ${reportPaths.length} JSON report(s):`);
    for (const p of reportPaths) {
      console.log(`  - ${p}`);
    }
  } else if (args.folder) {
    const reportPath = join(resolve(args.folder), 'results.json');
    if (!existsSync(reportPath)) {
      console.error(`No results.json found in ${args.folder}`);
      process.exit(1);
    }
    reportPaths = [reportPath];
  } else if (args.file) {
    if (!existsSync(args.file)) {
      console.error(`File not found: ${args.file}`);
      process.exit(1);
    }
    reportPaths = [args.file];
  } else {
    // Default: look for any JSON reports
    reportPaths = findJsonReports();
    if (reportPaths.length === 0) {
      console.log('Usage:');
      console.log('  node scripts/sync-failed-tests-from-report.mjs --all');
      console.log('  node scripts/sync-failed-tests-from-report.mjs --folder test-results/suite-name');
      console.log('  node scripts/sync-failed-tests-from-report.mjs path/to/results.json');
      process.exit(1);
    }
  }

  // Collect all failures from all reports
  let allFailures = [];
  for (const reportPath of reportPaths) {
    console.log(`\nParsing: ${reportPath}`);
    const failures = parsePlaywrightJson(reportPath);
    console.log(`  Found ${failures.length} failure(s)`);
    allFailures = allFailures.concat(failures);
  }

  // Merge with existing
  const existing = loadExistingFailedTests();
  const merged = mergeFailures(existing, allFailures);

  // Save
  saveFailedTests(merged);

  console.log('\n─────────────────────────────────');
  console.log('Summary:');
  console.log(`  Reports processed: ${reportPaths.length}`);
  console.log(`  New failures found: ${allFailures.length}`);
  console.log(`  Total in failed-tests.json: ${merged.length}`);
  console.log('─────────────────────────────────');

  if (merged.length > 0) {
    console.log('\nFailing tests:');
    for (const t of merged.slice(0, 20)) {
      console.log(`  - ${t.id}`);
    }
    if (merged.length > 20) {
      console.log(`  ... and ${merged.length - 20} more`);
    }
  }
}

main();
