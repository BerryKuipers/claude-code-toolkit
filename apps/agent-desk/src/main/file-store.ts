import { createHash, randomUUID } from 'node:crypto';
import { constants } from 'node:fs';
import { lstat, mkdir, open, realpath, rename, stat, unlink } from 'node:fs/promises';
import path from 'node:path';

export const TEXT_LIMIT = 2 * 1024 * 1024;

export function revision(content: string | undefined): string {
  if (content === undefined) return 'missing';
  return createHash('sha256').update(content).digest('hex');
}

export function agentHomes(home: string): {
  claude: string;
  codex: string;
  gemini: string;
  configured: string[];
} {
  const expand = (value: string): string =>
    path.resolve(
      value === '~'
        ? home
        : value.startsWith('~/') || value.startsWith('~\\')
          ? path.join(home, value.slice(2))
          : value,
    );
  const claude = expand(process.env.CLAUDE_CONFIG_DIR || path.join(home, '.claude'));
  const codex = expand(process.env.CODEX_HOME || path.join(home, '.codex'));
  const gemini = path.join(expand(process.env.GEMINI_CLI_HOME || home), '.gemini');
  const configured = [
    process.env.CLAUDE_CONFIG_DIR ? claude : undefined,
    process.env.CODEX_HOME ? codex : undefined,
    process.env.GEMINI_CLI_HOME ? gemini : undefined,
  ].filter((value): value is string => Boolean(value));
  return { claude, codex, gemini, configured };
}

export function approvedAnchor(
  file: string,
  home: string,
  projects: string[],
  configured: string[] = [],
): string {
  const candidates = [...projects, ...configured, home]
    .map((root) => path.resolve(root))
    .filter((root) => inside(root, file));
  candidates.sort((a, b) => b.length - a.length);
  if (!candidates[0])
    throw new Error('This path is outside the configured agent homes and projects.');
  return candidates[0];
}

export async function ensureConfiguredRoot(root: string): Promise<string> {
  let ancestor = path.resolve(root);
  while (true) {
    try {
      const info = await stat(ancestor);
      if (!info.isDirectory()) throw new Error('The configured agent home is not a directory.');
      break;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
      const parent = path.dirname(ancestor);
      if (parent === ancestor) throw new Error('Cannot find the configured agent home.');
      ancestor = parent;
    }
  }
  return ensureDirectoryWithin(root, ancestor);
}

export function inside(root: string, candidate: string): boolean {
  const relative = path.relative(root, candidate);
  return (
    relative === '' ||
    (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative))
  );
}

export function stableId(prefix: string, value: string): string {
  return `${prefix}-${revision(value).slice(0, 24)}`;
}

export async function readText(file: string, limit = TEXT_LIMIT): Promise<string> {
  const handle = await open(file, constants.O_RDONLY);
  try {
    const info = await handle.stat();
    if (!info.isFile()) throw new Error('The selected path is not a regular file.');
    if (info.size > limit)
      throw new Error(`File exceeds the ${Math.round(limit / 1024)} KiB editor limit.`);
    const bytes = Buffer.alloc(limit + 1);
    let total = 0;
    while (total < bytes.length) {
      const result = await handle.read(bytes, total, bytes.length - total, total);
      if (result.bytesRead === 0) break;
      total += result.bytesRead;
    }
    if (total > limit) throw new Error('File changed beyond the editor size limit while reading.');
    const result = bytes.subarray(0, total).toString('utf8');
    if (result.includes('\0')) throw new Error('Binary files cannot be edited.');
    return result;
  } finally {
    await handle.close();
  }
}

export async function optionalText(file: string): Promise<string | undefined> {
  try {
    return await readText(file);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return undefined;
    throw error;
  }
}

export async function canonicalWithin(
  file: string,
  roots: string[],
  allowMissing = false,
): Promise<string> {
  let canonical: string;
  try {
    canonical = await realpath(file);
  } catch (error) {
    if (!allowMissing || (error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
    const parent = await realpath(path.dirname(file));
    canonical = path.join(parent, path.basename(file));
  }
  if (!roots.some((root) => inside(root, canonical)))
    throw new Error('This path points outside its approved directory.');
  return canonical;
}

export async function ensureDirectoryWithin(directory: string, anchor: string): Promise<string> {
  if (!inside(path.resolve(anchor), path.resolve(directory)))
    throw new Error('Directory is outside its approved root.');
  const canonicalAnchor = await realpath(anchor);
  const parts = path.relative(anchor, directory).split(path.sep).filter(Boolean);
  let current = canonicalAnchor;
  for (const part of parts) {
    current = path.join(current, part);
    try {
      await mkdir(current, { mode: 0o700 });
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'EEXIST') throw error;
    }
    const info = await lstat(current);
    if (info.isSymbolicLink() || !info.isDirectory())
      throw new Error(
        'A destination directory is a link or is not a directory. Choose its original location.',
      );
    if (!inside(canonicalAnchor, await realpath(current)))
      throw new Error('Destination directory escaped its approved root.');
  }
  return current;
}

export async function atomicWrite(
  file: string,
  content: string,
  mode = 0o600,
  beforeCommit?: () => Promise<void>,
): Promise<void> {
  if (Buffer.byteLength(content) > TEXT_LIMIT)
    throw new Error('Content exceeds the editor size limit.');
  await mkdir(path.dirname(file), { recursive: true, mode: 0o700 });
  const temporary = path.join(path.dirname(file), `.${path.basename(file)}.${randomUUID()}.tmp`);
  const handle = await open(
    temporary,
    constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL,
    mode,
  );
  try {
    await handle.writeFile(content, 'utf8');
    await handle.sync();
  } catch (error) {
    await handle.close();
    await unlink(temporary).catch(() => undefined);
    throw error;
  }
  await handle.close();
  try {
    await beforeCommit?.();
    await rename(temporary, file);
  } catch (error) {
    await unlink(temporary).catch(() => undefined);
    throw error;
  }
}

const fileWrites = new Map<string, SerialWrites>();

export async function writeRevision(input: {
  file: string;
  content: string;
  expectedRevision: string;
  roots: string[];
  backupDir: string;
}): Promise<string> {
  const canonical = await canonicalWithin(input.file, input.roots, true);
  if (Buffer.byteLength(input.content) > TEXT_LIMIT)
    throw new Error('Content exceeds the editor size limit.');
  let queue = fileWrites.get(canonical);
  if (!queue) {
    queue = new SerialWrites();
    fileWrites.set(canonical, queue);
  }
  return queue.run(async () => {
    const current = await optionalText(canonical);
    if (revision(current) !== input.expectedRevision)
      throw new Error('This file changed outside Agent Desk. Reload it before saving.');
    const mode = current === undefined ? 0o600 : (await stat(canonical)).mode & 0o777;
    if (current !== undefined) {
      const backupName = `${Date.now()}-${randomUUID()}-${path.basename(canonical)}`;
      await atomicWrite(path.join(input.backupDir, backupName), current);
    }
    await atomicWrite(canonical, input.content, mode, async () => {
      if ((await canonicalWithin(input.file, input.roots, true)) !== canonical)
        throw new Error('The destination changed while saving. Reload it.');
      if (revision(await optionalText(canonical)) !== input.expectedRevision)
        throw new Error('This file changed while saving. Reload it.');
    });
    return revision(input.content);
  });
}

export async function readJson<T>(file: string, fallback: T): Promise<T> {
  const content = await optionalText(file);
  if (content === undefined) return fallback;
  try {
    return JSON.parse(content) as T;
  } catch {
    throw new Error(
      `Cannot read ${path.basename(file)}: invalid JSON. Your existing file was left intact.`,
    );
  }
}

export class SerialWrites {
  private pending: Promise<unknown> = Promise.resolve();

  run<T>(action: () => Promise<T>): Promise<T> {
    const next = this.pending.then(action, action);
    this.pending = next.catch(() => undefined);
    return next;
  }
}
