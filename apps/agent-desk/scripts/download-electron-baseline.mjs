import { execFile } from 'node:child_process';
import { appendFile, mkdir, readdir, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { promisify } from 'node:util';

const execute = promisify(execFile);
const repository = process.env.GITHUB_REPOSITORY;
const runId = '43842438534';
const artifactName =
  process.platform === 'win32' ? 'agent-desk-windows-latest' : 'agent-desk-ubuntu-latest';
const directory = path.join(
  process.env.RUNNER_TEMP ?? os.tmpdir(),
  `agent-desk-electron-baseline-${process.pid}`,
);
const evidenceDirectory = path.resolve(import.meta.dirname, '..', 'test-results', 'resources');
await mkdir(evidenceDirectory, { recursive: true });
const evidenceFile = path.join(evidenceDirectory, 'electron-baseline-provenance.json');
const provenance = {
  runtime: 'Electron',
  repository: repository ?? null,
  runId,
  artifactName,
  requestedAt: new Date().toISOString(),
};

async function findFiles(root, depth = 0) {
  if (depth > 8) return [];
  const result = [];
  for (const entry of await readdir(root, { withFileTypes: true })) {
    const filename = path.join(root, entry.name);
    if (entry.isDirectory() && entry.name !== 'node_modules')
      result.push(...(await findFiles(filename, depth + 1)));
    else if (entry.isFile()) result.push(filename);
  }
  return result;
}

try {
  if (!repository) throw new Error('GITHUB_REPOSITORY is not set.');
  await mkdir(directory, { recursive: true });
  const options = { timeout: 180000, maxBuffer: 4 * 1024 * 1024, windowsHide: true };
  const run = JSON.parse(
    (
      await execute(
        'gh',
        [
          'run',
          'view',
          runId,
          '--repo',
          repository,
          '--json',
          'databaseId,headSha,url,createdAt,updatedAt',
        ],
        options,
      )
    ).stdout,
  );
  const listing = JSON.parse(
    (await execute('gh', ['api', `repos/${repository}/actions/runs/${runId}/artifacts`], options))
      .stdout,
  );
  const artifact = listing.artifacts.find((item) => item.name === artifactName);
  if (!artifact || artifact.expired)
    throw new Error('The preserved Electron artifact has expired or is unavailable.');
  await execute(
    'gh',
    ['run', 'download', runId, '--repo', repository, '--name', artifactName, '--dir', directory],
    options,
  );
  const files = await findFiles(directory);
  const archive = files.find((file) =>
    file.endsWith(process.platform === 'win32' ? '.zip' : '.tar.gz'),
  );
  if (!archive) throw new Error('The Electron artifact contains no supported portable archive.');
  const extracted = path.join(directory, 'extracted');
  await mkdir(extracted, { recursive: true });
  if (process.platform === 'win32') {
    await execute(
      'powershell.exe',
      [
        '-NoProfile',
        '-NonInteractive',
        '-Command',
        'Expand-Archive -LiteralPath $env:AGENT_DESK_BASELINE_ARCHIVE -DestinationPath $env:AGENT_DESK_BASELINE_DIRECTORY -Force',
      ],
      {
        ...options,
        env: {
          ...process.env,
          AGENT_DESK_BASELINE_ARCHIVE: archive,
          AGENT_DESK_BASELINE_DIRECTORY: extracted,
        },
      },
    );
  } else {
    await execute('tar', ['-xzf', archive, '-C', extracted], options);
  }
  const expected = process.platform === 'win32' ? 'Agent Desk.exe' : 'agent-desk';
  const binary = (await findFiles(extracted)).find((file) => path.basename(file) === expected);
  if (!binary) throw new Error(`The extracted Electron executable ${expected} was not found.`);
  Object.assign(provenance, {
    status: 'downloaded',
    headSha: run.headSha,
    runUrl: run.url,
    runCreatedAt: run.createdAt,
    artifactId: artifact.id,
    artifactCreatedAt: artifact.created_at,
    artifactExpiresAt: artifact.expires_at,
    artifactDigest: artifact.digest ?? null,
    archive: path.basename(archive),
    binary,
  });
  if (process.env.GITHUB_ENV) {
    await appendFile(
      process.env.GITHUB_ENV,
      `AGENT_DESK_ELECTRON_BASELINE=${binary}\nAGENT_DESK_ELECTRON_BASELINE_ROOT=${path.dirname(binary)}\n`,
    );
  }
  console.log(`Preserved Electron baseline ready from ${run.url}, ${run.headSha}.`);
} catch (cause) {
  Object.assign(provenance, {
    status: 'unavailable',
    reason: cause instanceof Error ? cause.message : String(cause),
  });
  console.log(`Electron comparison is optional: ${provenance.reason}`);
}
await writeFile(evidenceFile, JSON.stringify(provenance, null, 2) + '\n');
