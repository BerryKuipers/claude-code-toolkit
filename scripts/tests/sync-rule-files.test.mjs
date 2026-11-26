import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { cp, lstat, mkdir, mkdtemp, readFile, readdir, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

const toolkit = dirname(dirname(dirname(fileURLToPath(import.meta.url))));
const helper = join(toolkit, 'scripts/sync-rule-files.sh');
const legacyNames = (await readdir(join(toolkit, 'docs/archive/2026-11-26-rules'))).filter((name) => name.endsWith('.mdc'));
const legacyName = legacyNames[0];

async function fixture(run) {
  const temporary = await mkdtemp(join(tmpdir(), 'toolkit-rules-'));
  const source = join(temporary, 'source');
  const target = join(temporary, 'target');
  try {
    await mkdir(join(source, 'rules'), { recursive: true });
    await mkdir(join(target, 'rules'), { recursive: true });
    await cp(join(toolkit, '.claude/rules'), join(source, 'rules'), { recursive: true });
    await run({ temporary, source, target, sync: () => execFileSync('bash', [helper, source, target], { encoding: 'utf8' }) });
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
}

test('native rules install, update untouched copies and preserve customized copies', async () => {
  await fixture(async ({ source, target, sync }) => {
    const name = '01-typescript-style.md';
    sync();
    const original = await readFile(join(target, 'rules', name), 'utf8');
    sync();
    assert.equal(await readFile(join(target, 'rules', name), 'utf8'), original);
    await writeFile(join(source, 'rules', name), `${original}\nUpdated upstream rule.\n`);
    sync();
    assert.match(await readFile(join(target, 'rules', name), 'utf8'), /Updated upstream rule/);
    await writeFile(join(target, 'rules', name), 'Project-specific customization.\n');
    await writeFile(join(source, 'rules', name), 'Next upstream revision.\n');
    assert.match(sync(), /Kept customized native rule/);
    assert.equal(await readFile(join(target, 'rules', name), 'utf8'), 'Project-specific customization.\n');
  });
});

test('a pre-existing native filename is not assumed to be toolkit-owned', async () => {
  await fixture(async ({ target, sync }) => {
    await writeFile(join(target, 'rules/00-architecture.md'), 'Owner architecture.\n');
    assert.match(sync(), /Kept customized native rule/);
    assert.equal(await readFile(join(target, 'rules/00-architecture.md'), 'utf8'), 'Owner architecture.\n');
  });
});

test('all seven exact legacy files migrate losslessly with LF or CRLF and repeated sync is stable', async () => {
  for (const crlf of [false, true]) {
    await fixture(async ({ target, sync }) => {
      const originals = new Map();
      for (const name of legacyNames) {
        let content = await readFile(join(toolkit, 'docs/archive/2026-11-26-rules', name), 'utf8');
        if (crlf) content = content.replaceAll('\n', '\r\n');
        originals.set(name, content);
        await writeFile(join(target, 'rules', name), content);
      }
      sync();
      sync();
      assert.equal((await readdir(join(target, 'rules'))).filter((name) => name.endsWith('.mdc')).length, 0);
      for (const [name, content] of originals) {
        assert.equal(await readFile(join(target, 'reference/retired-toolkit-rules', name), 'utf8'), content);
      }
    });
  }
});

test('custom legacy content and an existing archive conflict are preserved', async () => {
  await fixture(async ({ target, sync }) => {
    const original = await readFile(join(toolkit, 'docs/archive/2026-11-26-rules', legacyName), 'utf8');
    const legacy = join(target, 'rules', legacyName);
    await writeFile(legacy, `${original}\nProject exception.\n`);
    assert.match(sync(), /Kept customized legacy rule/);
    assert.match(await readFile(legacy, 'utf8'), /Project exception/);
    await writeFile(legacy, original);
    const archive = join(target, 'reference/retired-toolkit-rules', legacyName);
    await mkdir(dirname(archive), { recursive: true });
    await writeFile(archive, 'Earlier local archive.\n');
    assert.match(sync(), /archive already contains different content/);
    assert.equal(await readFile(legacy, 'utf8'), original);
    assert.equal(await readFile(archive, 'utf8'), 'Earlier local archive.\n');
  });
});

test('native and legacy symlinks do not mutate their external target', { skip: process.platform === 'win32' }, async () => {
  await fixture(async ({ temporary, target, sync }) => {
    const external = join(temporary, 'external');
    await writeFile(external, 'Outside content.\n');
    await symlink(external, join(target, 'rules', legacyName));
    await symlink(external, join(target, 'rules/00-architecture.md'));
    sync();
    assert.equal(await readFile(external, 'utf8'), 'Outside content.\n');
    assert.equal((await lstat(join(target, 'rules', legacyName))).isSymbolicLink(), true);
    assert.equal((await lstat(join(target, 'rules/00-architecture.md'))).isSymbolicLink(), true);
  });
});

test('the full sync refuses to delete an existing checkout when fallback would replace it', async () => {
  await fixture(async ({ temporary }) => {
    const project = join(temporary, 'project');
    await mkdir(join(project, '.claude-toolkit'), { recursive: true });
    const owned = join(project, '.claude-toolkit/unfinished.txt');
    await writeFile(owned, 'Uncommitted work.\n');
    const result = spawnSync('bash', [join(toolkit, 'scripts/sync-claude-toolkit.sh')], {
      env: { ...process.env, CLAUDE_PROJECT_DIR: project, TMPDIR: temporary }, encoding: 'utf8',
    });
    assert.equal(result.status, 1);
    assert.match(result.stdout, /existing toolkit checkout.*preserving it/);
    assert.equal(await readFile(owned, 'utf8'), 'Uncommitted work.\n');
  });
});

test('a linked Git worktree updates its submodule and installs the native rules', async () => {
  await fixture(async ({ temporary }) => {
    const upstream = join(temporary, 'upstream');
    const project = join(temporary, 'project');
    const worktree = join(temporary, 'worktree');
    const env = {
      ...process.env,
      GIT_ALLOW_PROTOCOL: 'file',
      GIT_AUTHOR_NAME: 'Toolkit fixture',
      GIT_AUTHOR_EMAIL: 'fixture@example.invalid',
      GIT_COMMITTER_NAME: 'Toolkit fixture',
      GIT_COMMITTER_EMAIL: 'fixture@example.invalid',
    };
    const git = (directory, ...args) => execFileSync('git', ['-C', directory, ...args], { env, stdio: 'pipe' });
    await mkdir(upstream);
    await mkdir(project);
    await cp(join(toolkit, '.claude/rules'), join(upstream, '.claude/rules'), { recursive: true });
    await mkdir(join(upstream, 'scripts'));
    for (const name of ['sync-rule-files.sh', 'retired-rule-hashes.sha256']) {
      await cp(join(toolkit, 'scripts', name), join(upstream, 'scripts', name));
    }
    git(upstream, 'init', '-b', 'main');
    git(upstream, 'add', '.');
    git(upstream, '-c', 'commit.gpgsign=false', 'commit', '-m', 'Fixture toolkit');
    git(project, 'init', '-b', 'main');
    git(project, 'submodule', 'add', upstream, '.claude-toolkit');
    git(project, '-c', 'commit.gpgsign=false', 'commit', '-am', 'Fixture project');
    git(project, 'worktree', 'add', worktree, '-b', 'fixture-worktree');
    assert.equal((await lstat(join(worktree, '.git'))).isFile(), true);
    const output = execFileSync('bash', [join(toolkit, 'scripts/sync-claude-toolkit.sh')], {
      env: { ...env, CLAUDE_PROJECT_DIR: worktree, TMPDIR: temporary }, encoding: 'utf8',
    });
    assert.match(output, /submodule update/);
    assert.doesNotMatch(output, /fallback clone/);
    assert.equal(await readFile(join(worktree, '.claude/rules/00-architecture.md'), 'utf8'), await readFile(join(toolkit, '.claude/rules/00-architecture.md'), 'utf8'));
  });
});
