#!/usr/bin/env node
/**
 * Iterative Playwright runner
 * - Runs a target project/suite
 * - Parses JSON report to find first failure
 * - Re-runs only the failing test by file + title grep
 * - Repeats until green or max attempts reached
 */
import { spawnSync } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const PROJECT = process.env.PW_PROJECT || 'journey';
const GREP = process.env.PW_GREP || ''; // optional grep
const MAX_ATTEMPTS = parseInt(process.env.PW_MAX_ATTEMPTS || '5', 10);
const REPORT_FILE = resolve('playwright-report/results.json');

function runPlaywright(args = []) {
  const env = { ...process.env, PW_TAG_PROJECTS: process.env.PW_TAG_PROJECTS || '1', E2E_SKIP_DB_SYNC: process.env.E2E_SKIP_DB_SYNC || '1' };
  const result = spawnSync('npx', ['playwright', 'test', '--project', PROJECT, '--reporter', 'json', ...args], {
    stdio: 'inherit',
    env,
    shell: process.platform === 'win32',
  });
  return result.status ?? result.signal ?? 1;
}

function parseReport() {
  if (!existsSync(REPORT_FILE)) return null;
  try {
    const json = JSON.parse(readFileSync(REPORT_FILE, 'utf-8'));
    return json;
  } catch (e) {
    console.error('Failed to parse JSON report:', e);
    return null;
  }
}

function findFirstFailure(report) {
  if (!report?.suites) return null;
  // Flatten all tests
  const tests = [];
  const stack = [...report.suites];
  while (stack.length) {
    const n = stack.shift();
    if (n.suites) stack.push(...n.suites);
    if (n.specs) {
      for (const s of n.specs) {
        tests.push(...(s.tests || []));
      }
    }
  }
  // Find first non-passed
  for (const t of tests) {
    const outcome = t.results?.some(r => r.status !== 'passed') ? 'failed' : 'passed';
    if (outcome === 'failed') {
      const title = t.title || t.titlePath?.slice(-1)?.[0] || '';
      const file = t.location?.file || t.file || '';
      return { title, file };
    }
  }
  return null;
}

function main() {
  let attempt = 1;
  while (attempt <= MAX_ATTEMPTS) {
    console.log(`\n▶️  Attempt ${attempt}/${MAX_ATTEMPTS} — running project=${PROJECT} grep=${GREP || '(none)'}`);
    const args = [];
    if (GREP) args.push('-g', GREP);
    const code = runPlaywright(args);

    const report = parseReport();
    const failure = findFirstFailure(report);
    if (!failure) {
      console.log('\n✅ No failures found — suite is green.');
      process.exit(0);
    }

    console.log(`\n❌ First failing test:`);
    console.log(`   file:  ${failure.file}`);
    console.log(`   title: ${failure.title}`);

    // Re-run only this test by file + title grep
    const rerunArgs = [failure.file, '-g', failure.title];
    console.log(`\n🔁 Re-running failing test…`);
    const rerunCode = runPlaywright(rerunArgs);
    if (rerunCode === 0) {
      console.log('✅ Flaky test passed on rerun. Continuing…');
      attempt++;
      continue; // Next global run would be ideal, but keep loop bounded
    } else {
      console.log('❗ Still failing on focused rerun. Please inspect trace and logs.');
      process.exit(rerunCode);
    }
  }
  console.log(`\n⚠️  Gave up after ${MAX_ATTEMPTS} attempts.`);
  process.exit(1);
}

main();

