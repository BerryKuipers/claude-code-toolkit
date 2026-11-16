import { defineConfig } from '@playwright/test';

const resultsDirectory =
  process.env.AGENT_DESK_PACKAGED === '1' ? 'test-results/packaged' : 'test-results/native';

export default defineConfig({
  testDir: 'tests',
  testMatch: 'desktop.spec.ts',
  timeout: 90000,
  expect: { timeout: 10000 },
  workers: 1,
  fullyParallel: false,
  reporter: [['list'], ['html', { open: 'never', outputFolder: `${resultsDirectory}/report` }]],
  outputDir: `${resultsDirectory}/desktop`,
});
