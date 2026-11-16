import { createHash } from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import type {
  AgentId,
  AppSettings,
  SessionIndex,
  SessionRecord,
  Transcript,
} from '../shared/types';
import { CodexHistory } from './session-codex';
import {
  object,
  parseAntigravity,
  parseClaude,
  parseCodex,
  parseGemini,
  string,
  type JsonRecord,
  type SessionInput,
} from './session-formats';

const MAX_FILE_BYTES = 32 * 1024 * 1024;
const MAX_FILES = 10000;
const MAX_DIRECTORIES = 20000;
const MAX_DEPTH = 10;

interface ScanRoot {
  agent: AgentId;
  path: string;
  sourceKind: SessionRecord['sourceKind'];
  archived?: boolean;
  custom?: boolean;
}

interface Source {
  session: SessionRecord;
  root?: ScanRoot;
  appServer?: boolean;
  nativeStore?: boolean;
}

interface ReadResult {
  records: JsonRecord[];
  warnings: string[];
  truncated: boolean;
  modifiedAt: string;
}

async function exists(value: string): Promise<boolean> {
  try {
    await fs.access(value);
    return true;
  } catch {
    return false;
  }
}

function candidate(agent: AgentId, name: string): boolean {
  if (agent === 'claude')
    return (
      name.endsWith('.jsonl') &&
      !/^agent-|\.orphaned-|\.superseded-/.test(name) &&
      name !== 'history.jsonl'
    );
  if (agent === 'codex') return /^rollout-.*\.jsonl$/.test(name);
  if (agent === 'gemini') return /^session-.*\.jsonl?$/.test(name);
  return name === 'transcript.jsonl';
}

async function readRecords(file: string): Promise<ReadResult> {
  const info = await fs.lstat(file);
  if (!info.isFile() || info.isSymbolicLink())
    throw new Error('Session source is not a regular file.');
  const handle = await fs.open(file, 'r');
  const warnings: string[] = [];
  const truncated = info.size > MAX_FILE_BYTES;
  let text = '';
  try {
    if (truncated && file.endsWith('.json'))
      throw new Error('This legacy JSON session exceeds the 32 MiB read limit.');
    if (truncated) {
      const headSize = 8 * 1024 * 1024;
      const tailSize = MAX_FILE_BYTES - headSize;
      const head = Buffer.alloc(headSize);
      const tail = Buffer.alloc(tailSize);
      const headRead = await handle.read(head, 0, headSize, 0);
      const tailRead = await handle.read(tail, 0, tailSize, info.size - tailSize);
      const headText = head.subarray(0, headRead.bytesRead).toString('utf8');
      const tailText = tail.subarray(0, tailRead.bytesRead).toString('utf8');
      text = `${headText.slice(0, headText.lastIndexOf('\n'))}\n${tailText.slice(tailText.indexOf('\n') + 1)}`;
      warnings.push(
        'This large session is a partial view: the first 8 MiB and last 24 MiB were read.',
      );
    } else {
      const buffer = Buffer.alloc(info.size);
      const read = await handle.read(buffer, 0, buffer.length, 0);
      text = buffer.subarray(0, read.bytesRead).toString('utf8');
    }
  } finally {
    await handle.close();
  }
  const records: JsonRecord[] = [];
  if (file.endsWith('.json')) {
    try {
      const parsed = JSON.parse(text);
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error();
      records.push(object(parsed));
    } catch {
      throw new Error('Session JSON is malformed or is being written. Refresh to try again.');
    }
  } else {
    let malformed = 0;
    for (const line of text.split('\n')) {
      if (!line.trim()) continue;
      if (line.length > 2 * 1024 * 1024) {
        malformed++;
        continue;
      }
      try {
        const parsed = JSON.parse(line);
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed))
          records.push(object(parsed));
        else malformed++;
      } catch {
        malformed++;
      }
    }
    if (malformed)
      warnings.push(
        `${malformed} malformed, incomplete, or oversized transcript record${malformed === 1 ? ' was' : 's were'} skipped.`,
      );
  }
  return { records, warnings, truncated, modifiedAt: info.mtime.toISOString() };
}

export class SessionService {
  private readonly home: string;
  private readonly settings: () => AppSettings;
  private cached?: SessionIndex;
  private cacheKey = '';
  private scanning?: Promise<SessionIndex>;
  private sources = new Map<string, Source>();
  private fileCache = new Map<string, { signature: string; transcript: Transcript | null }>();
  private codex?: CodexHistory;
  private codexKey = '';
  private codexRetryAt = 0;
  private codexWarning = '';

  constructor(options: { home: string; settings: () => AppSettings }) {
    this.home = options.home;
    this.settings = options.settings;
  }

  private expand(value: string): string {
    if (value === '~') return this.home;
    if (value.startsWith('~/') || value.startsWith('~\\'))
      return path.join(this.home, value.slice(2));
    return value;
  }

  private homes(): { claude: string; codex: string; gemini: string } {
    return {
      claude: this.expand(process.env.CLAUDE_CONFIG_DIR || path.join(this.home, '.claude')),
      codex: this.expand(process.env.CODEX_HOME || path.join(this.home, '.codex')),
      gemini: path.join(this.expand(process.env.GEMINI_CLI_HOME || this.home), '.gemini'),
    };
  }

  private nativeRoots(): ScanRoot[] {
    const homes = this.homes();
    return [
      { agent: 'claude', path: path.join(homes.claude, 'projects'), sourceKind: 'cli' },
      { agent: 'codex', path: path.join(homes.codex, 'sessions'), sourceKind: 'cli' },
      {
        agent: 'codex',
        path: path.join(homes.codex, 'archived_sessions'),
        sourceKind: 'cli',
        archived: true,
      },
      { agent: 'gemini', path: path.join(homes.gemini, 'tmp'), sourceKind: 'cli' },
      {
        agent: 'antigravity',
        path: path.join(this.home, '.gemini', 'antigravity-cli', 'brain'),
        sourceKind: 'cli',
      },
      {
        agent: 'antigravity',
        path: path.join(this.home, '.gemini', 'antigravity', 'brain'),
        sourceKind: 'desktop',
      },
      {
        agent: 'antigravity',
        path: path.join(this.home, '.gemini', 'antigravity-ide', 'brain'),
        sourceKind: 'ide',
      },
    ];
  }

  private roots(): ScanRoot[] {
    const roots = this.nativeRoots();
    for (const root of this.settings().historyRoots) {
      const expanded = this.expand(root.path);
      const sourceKind =
        root.agent !== 'antigravity' || /(?:^|[\\/])antigravity-cli(?:[\\/]|$)/.test(expanded)
          ? 'cli'
          : /(?:^|[\\/])antigravity-ide(?:[\\/]|$)/.test(expanded)
            ? 'ide'
            : 'desktop';
      roots.push({
        agent: root.agent,
        path: expanded,
        sourceKind,
        custom: true,
        archived: /archived_sessions(?:[\\/]|$)/.test(expanded),
      });
    }
    const unique = new Map<string, ScanRoot>();
    for (const root of roots) {
      const key = `${root.agent}:${root.path}`;
      if (!unique.has(key)) unique.set(key, root);
    }
    return [...unique.values()];
  }

  async index(refresh = false): Promise<SessionIndex> {
    const settings = this.settings();
    const key = JSON.stringify([
      settings.historyRoots,
      settings.projects,
      settings.agentCommands.codex,
      this.homes(),
    ]);
    if (!refresh && this.cached && key === this.cacheKey) return this.cached;
    if (this.scanning) return this.scanning;
    this.scanning = this.scan(key);
    try {
      return await this.scanning;
    } finally {
      this.scanning = undefined;
    }
  }

  private async walk(root: ScanRoot, warnings: string[]): Promise<string[]> {
    const files: string[] = [];
    const queue: Array<{ dir: string; depth: number }> = [{ dir: root.path, depth: 0 }];
    let visited = 0;
    while (queue.length && files.length < MAX_FILES && visited < MAX_DIRECTORIES) {
      const current = queue.shift()!;
      visited++;
      try {
        const info = await fs.lstat(current.dir);
        if (info.isSymbolicLink()) continue;
        if (info.isFile()) {
          if (candidate(root.agent, path.basename(current.dir))) files.push(current.dir);
          continue;
        }
        if (!info.isDirectory()) continue;
        const entries = await fs.readdir(current.dir, { withFileTypes: true });
        entries.sort((a, b) => b.name.localeCompare(a.name));
        for (const entry of entries) {
          if (entry.isSymbolicLink()) continue;
          const full = path.join(current.dir, entry.name);
          if (entry.isFile() && candidate(root.agent, entry.name)) files.push(full);
          if (
            entry.isDirectory() &&
            current.depth < MAX_DEPTH &&
            !['subagents', 'node_modules', '.git', 'memory', 'tool-results', 'plugins'].includes(
              entry.name,
            )
          ) {
            queue.push({ dir: full, depth: current.depth + 1 });
          }
          if (files.length >= MAX_FILES) break;
        }
      } catch (error) {
        const code = (error as NodeJS.ErrnoException).code;
        if (code !== 'ENOENT' || root.custom)
          warnings.push(`Could not scan ${current.dir} (${code || 'read error'}).`);
      }
    }
    if (queue.length)
      warnings.push(
        `History scan limit reached under ${root.path}. Add a narrower history folder to inspect remaining sessions.`,
      );
    return files;
  }

  private async projectForGemini(file: string): Promise<string | undefined> {
    let directory = path.dirname(file);
    for (let level = 0; level < 4; level++) {
      const marker = path.join(directory, '.project_root');
      try {
        const info = await fs.lstat(marker);
        if (info.isFile() && !info.isSymbolicLink() && info.size < 16384) {
          const project = (await fs.readFile(marker, 'utf8')).trim();
          if (path.isAbsolute(project) || /^[A-Za-z]:[\\/]/.test(project)) return project;
        }
      } catch {}
      directory = path.dirname(directory);
    }
    const directoryKey = path.basename(path.dirname(path.dirname(file)));
    return this.settings().projects.find(
      (project) => createHash('sha256').update(project).digest('hex') === directoryKey,
    );
  }

  private async antigravityProjects(root: ScanRoot): Promise<Map<string, string>> {
    const mapping = new Map<string, string>();
    const roots = [root.path, path.dirname(root.path)];
    for (const parent of roots) {
      try {
        const cache = path.join(parent, 'cache', 'last_conversations.json');
        const info = await fs.lstat(cache);
        if (!info.isFile() || info.isSymbolicLink() || info.size > 1024 * 1024) continue;
        const contents = object(JSON.parse(await fs.readFile(cache, 'utf8')));
        for (const [project, nativeId] of Object.entries(contents)) {
          if (
            typeof nativeId === 'string' &&
            (path.isAbsolute(project) || /^[A-Za-z]:[\\/]/.test(project))
          )
            mapping.set(nativeId, project);
        }
      } catch {}
    }
    return mapping;
  }

  private async parseFile(
    file: string,
    root: ScanRoot,
    mapping?: Map<string, string>,
    includeMessages = false,
  ): Promise<Transcript | null> {
    const info = await fs.lstat(file);
    if (!info.isFile() || info.isSymbolicLink())
      throw new Error('Session source is not a regular file.');
    const signature = `${info.size}:${info.mtimeMs}:${root.agent}:${root.sourceKind}:${Boolean(root.archived)}:${JSON.stringify(this.settings().projects)}:${JSON.stringify(mapping ? [...mapping] : [])}`;
    const cached = this.fileCache.get(file);
    if (!includeMessages && cached?.signature === signature) return cached.transcript;
    const read = await readRecords(file);
    const input: SessionInput = {
      agent: root.agent,
      sourcePath: file,
      sourceKind: root.sourceKind,
      modifiedAt: read.modifiedAt,
      warnings: read.warnings,
      truncated: read.truncated,
      archived: root.archived,
    };
    let transcript: Transcript | null;
    if (root.agent === 'claude') transcript = parseClaude(read.records, input);
    else if (root.agent === 'codex') transcript = parseCodex(read.records, input);
    else if (root.agent === 'gemini')
      transcript = parseGemini(read.records, {
        ...input,
        projectPath: await this.projectForGemini(file),
      });
    else {
      const parts = file.split(path.sep);
      const brain = parts.lastIndexOf('brain');
      const nativeId =
        brain >= 0
          ? parts[brain + 1]
          : path.basename(path.dirname(path.dirname(path.dirname(file))));
      transcript = parseAntigravity(read.records, {
        ...input,
        nativeId,
        projectPath: mapping?.get(nativeId),
      });
    }
    if (!transcript && read.warnings.length) throw new Error(read.warnings.join(' '));
    if (this.fileCache.size > MAX_FILES) this.fileCache.delete(this.fileCache.keys().next().value!);
    this.fileCache.set(file, {
      signature,
      transcript: transcript ? { ...transcript, messages: [] } : null,
    });
    return transcript;
  }

  private async scan(key: string): Promise<SessionIndex> {
    const warnings: string[] = [];
    const sources = new Map<string, Source>();
    const deduped = new Map<string, Source>();
    const seenFiles = new Set<string>();
    const roots = this.roots();
    const nativeRoots = this.nativeRoots();
    const homes = this.homes();
    const command = this.settings().agentCommands.codex;
    const codexKey = `${command}:${homes.codex}`;
    if (this.codexKey !== codexKey) {
      this.codex?.close();
      this.codex = undefined;
      this.codexKey = codexKey;
      this.codexRetryAt = 0;
      this.codexWarning = '';
    }
    if (command && Date.now() < this.codexRetryAt) warnings.push(this.codexWarning);
    else if (command && (await exists(homes.codex))) {
      try {
        this.codex ||= new CodexHistory(command, homes.codex);
        const indexed = await this.codex.index();
        this.codexWarning = '';
        warnings.push(...indexed.warnings);
        for (const session of indexed.sessions)
          deduped.set(`codex:${session.nativeId}`, { session, appServer: true, nativeStore: true });
      } catch (error) {
        this.codexWarning = `${error instanceof Error ? error.message : 'Codex app-server is unavailable.'} Local rollout files are being indexed; newer paginated-only history may be unavailable. The native history connection retries after one minute.`;
        this.codexRetryAt = Date.now() + 60000;
        warnings.push(this.codexWarning);
        this.codex?.close();
        this.codex = undefined;
      }
    }
    for (const root of roots) {
      if (!path.isAbsolute(root.path)) {
        warnings.push(`History folder must be an absolute path: ${root.path}`);
        continue;
      }
      const files = await this.walk(root, warnings);
      const mapping =
        root.agent === 'antigravity' ? await this.antigravityProjects(root) : undefined;
      for (const file of files) {
        if (seenFiles.has(file)) continue;
        seenFiles.add(file);
        try {
          const nativeRoot = nativeRoots.find((candidate) => {
            if (candidate.agent !== root.agent) return false;
            const relative = path.relative(candidate.path, file);
            return (
              !path.isAbsolute(relative) &&
              relative !== '..' &&
              !relative.startsWith(`..${path.sep}`)
            );
          });
          const nativeStore = Boolean(nativeRoot);
          const sourceRoot = nativeRoot || root;
          const transcript = await this.parseFile(file, sourceRoot, mapping);
          if (!transcript) continue;
          warnings.push(
            ...transcript.warnings.map((warning) => `${path.basename(file)}: ${warning}`),
          );
          const session = { ...transcript.session };
          if (!nativeStore) {
            session.resumable = false;
            session.resumeNote =
              'This history is outside the active native session store. Open or import it with its native app before resuming.';
          }
          const dedupeKey = `${session.agent}:${session.nativeId}`;
          const previous = deduped.get(dedupeKey);
          if (previous?.appServer) {
            if (!nativeStore) continue;
            previous.root = sourceRoot;
            previous.session.sourcePath = session.sourcePath;
            if (!previous.session.projectPath && session.projectPath) {
              previous.session.projectPath = session.projectPath;
              previous.session.projectName = session.projectName;
              previous.session.resumable = session.resumable;
              previous.session.resumeNote = session.resumeNote;
            }
            previous.session.model ||= session.model;
            previous.session.messageCount ||= session.messageCount;
          } else {
            const priority = nativeStore ? (session.archived ? 1 : 2) : 0;
            const previousPriority = previous?.nativeStore
              ? previous.session.archived
                ? 1
                : 2
              : 0;
            if (
              !previous ||
              priority > previousPriority ||
              (priority === previousPriority && previous.session.updatedAt < session.updatedAt)
            ) {
              deduped.set(dedupeKey, { session, root: sourceRoot, nativeStore });
            }
          }
        } catch (error) {
          warnings.push(
            `${path.basename(file)}: ${error instanceof Error ? error.message : 'Could not read transcript.'}`,
          );
        }
      }
    }
    for (const source of deduped.values()) {
      if (
        source.session.projectPath &&
        source.session.resumable &&
        !(await exists(source.session.projectPath))
      ) {
        source.session = {
          ...source.session,
          resumable: false,
          resumeNote: 'The original project directory is not available on this computer.',
        };
      }
      sources.set(source.session.id, source);
    }
    this.sources = sources;
    this.cached = {
      sessions: [...sources.values()]
        .map((source) => source.session)
        .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)),
      warnings: [...new Set(warnings)].slice(0, 200),
      scannedAt: new Date().toISOString(),
    };
    this.cacheKey = key;
    return this.cached;
  }

  async transcript(id: string): Promise<Transcript> {
    if (!this.cached) await this.index();
    const source = this.sources.get(id);
    if (!source) throw new Error('Session not found. Refresh your history and select it again.');
    let apiFailure: string | undefined;
    if (source.appServer && this.codex) {
      try {
        return await this.codex.transcript(source.session);
      } catch (error) {
        apiFailure = error instanceof Error ? error.message : 'Codex history API failed.';
      }
    }
    if (source.root && source.session.sourcePath) {
      const mapping =
        source.root.agent === 'antigravity'
          ? await this.antigravityProjects(source.root)
          : undefined;
      const parsed = await this.parseFile(source.session.sourcePath, source.root, mapping, true);
      if (!parsed) throw new Error('The session no longer contains a recognized transcript.');
      return {
        ...parsed,
        session: { ...source.session, messageCount: parsed.messages.length },
        warnings: [
          ...parsed.warnings,
          ...(apiFailure ? [`${apiFailure} Showing the local rollout transcript.`] : []),
        ],
      };
    }
    throw new Error(apiFailure || 'A readable transcript is not available for this session.');
  }

  close(): void {
    this.codex?.close();
    this.codex = undefined;
    this.fileCache.clear();
    this.sources.clear();
    this.cached = undefined;
  }
}
