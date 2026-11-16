import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process';
import type { SessionMessage, SessionRecord, Transcript } from '../shared/types';
import {
  contentText,
  date,
  list,
  makeTranscript,
  object,
  string,
  type JsonRecord,
} from './session-formats';
import { resolveExecutable } from './executables';

class RpcError extends Error {
  constructor(
    readonly code: number,
    method: string,
  ) {
    super(`Codex ${method} failed (${code}).`);
  }
}

interface Pending {
  resolve: (value: unknown) => void;
  reject: (error: Error) => void;
  timer: ReturnType<typeof setTimeout>;
}

export class CodexHistory {
  private child?: ChildProcessWithoutNullStreams;
  private pending = new Map<number, Pending>();
  private sequence = 0;
  private ready?: Promise<void>;
  private buffer = '';
  private failure?: Error;

  constructor(
    private readonly command: string,
    private readonly home: string,
  ) {}

  private async start(): Promise<void> {
    if (this.failure) throw this.failure;
    if (this.ready) return this.ready;
    this.ready = this.initialize();
    return this.ready;
  }

  private async initialize(): Promise<void> {
    const env = Object.fromEntries(
      Object.entries(process.env).filter(
        (entry): entry is [string, string] =>
          typeof entry[1] === 'string' &&
          !entry[0].startsWith('ELECTRON_') &&
          entry[0] !== 'NODE_OPTIONS',
      ),
    );
    env.CODEX_HOME = this.home;
    const executable = await resolveExecutable(this.command, env);
    const child = spawn(
      executable.file,
      [...executable.prefixArgs, 'app-server', '--listen', 'stdio://'],
      {
        env,
        stdio: ['pipe', 'pipe', 'pipe'],
        windowsHide: true,
      },
    );
    this.child = child;
    child.stdout.setEncoding('utf8');
    child.stdout.on('data', (chunk: string) => {
      this.buffer += chunk;
      if (this.buffer.length > 32 * 1024 * 1024) {
        this.stopWith(new Error('Codex history response exceeded the 32 MiB limit.'));
        return;
      }
      for (;;) {
        const newline = this.buffer.indexOf('\n');
        if (newline < 0) break;
        const line = this.buffer.slice(0, newline);
        this.buffer = this.buffer.slice(newline + 1);
        if (!line.trim()) continue;
        try {
          const response = object(JSON.parse(line));
          const pending = this.pending.get(Number(response.id));
          if (!pending) continue;
          this.pending.delete(Number(response.id));
          clearTimeout(pending.timer);
          if (response.error)
            pending.reject(new RpcError(Number(object(response.error).code) || -1, 'request'));
          else pending.resolve(response.result);
        } catch {
          this.stopWith(new Error('Codex app-server returned invalid JSON.'));
          return;
        }
      }
    });
    child.stderr.resume();
    child.on('error', (error) =>
      this.stopWith(
        new Error(
          `Codex app-server could not start (${(error as NodeJS.ErrnoException).code || 'process error'}).`,
        ),
      ),
    );
    child.on('exit', (code) =>
      this.stopWith(new Error(`Codex app-server exited (${code ?? 'signal'}).`)),
    );
    child.stdin.on('error', () => this.stopWith(new Error('The Codex history connection closed.')));
    await this.request('initialize', {
      clientInfo: { name: 'agent-desk', title: 'Agent Desk', version: '0.1.0' },
      capabilities: { experimentalApi: false },
    });
    child.stdin.write(`${JSON.stringify({ method: 'initialized' })}\n`);
  }

  private request(method: string, params: JsonRecord): Promise<unknown> {
    if (this.failure) return Promise.reject(this.failure);
    if (!this.child) return Promise.reject(new Error('Codex app-server is not running.'));
    const id = ++this.sequence;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(
        () => this.stopWith(new Error(`Codex ${method} timed out after 10 seconds.`)),
        10000,
      );
      this.pending.set(id, { resolve, reject, timer });
      this.child!.stdin.write(`${JSON.stringify({ id, method, params })}\n`);
    });
  }

  private stopWith(error: Error): void {
    if (!this.failure) this.failure = error;
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(error);
    }
    this.pending.clear();
    const child = this.child;
    this.child = undefined;
    if (child && !child.killed) child.kill();
  }

  close(): void {
    this.stopWith(new Error('Codex history connection closed.'));
  }

  async index(): Promise<{ sessions: SessionRecord[]; warnings: string[] }> {
    await this.start();
    const sessions: SessionRecord[] = [];
    const warnings: string[] = [];
    for (const archived of [false, true]) {
      let cursor: string | undefined;
      const cursors = new Set<string>();
      let compatibility = false;
      for (let page = 0; page < 100; page++) {
        let result: JsonRecord;
        const params: JsonRecord = {
          limit: 100,
          archived,
          modelProviders: [],
          ...(cursor ? { cursor } : {}),
        };
        if (!compatibility)
          Object.assign(params, {
            sortKey: 'updated_at',
            sourceKinds: ['cli', 'vscode', 'exec', 'appServer', 'unknown'],
          });
        try {
          result = object(await this.request('thread/list', params));
        } catch (error) {
          if (!(error instanceof RpcError) || error.code !== -32602 || compatibility) throw error;
          compatibility = true;
          warnings.push(
            'This Codex version accepts fewer thread filters. All providers are included, but its default source filter may omit non-interactive sessions.',
          );
          result = object(
            await this.request('thread/list', {
              limit: 100,
              archived,
              modelProviders: [],
              ...(cursor ? { cursor } : {}),
            }),
          );
        }
        if (!Array.isArray(result.data))
          throw new Error('Codex thread/list returned no session array.');
        for (const raw of result.data) {
          const thread = object(raw);
          if (!string(thread.id)) continue;
          sessions.push(this.record(thread, archived));
        }
        const next = string(result.nextCursor);
        if (!next) break;
        if (cursors.has(next)) {
          warnings.push('Codex repeated a history cursor. Remaining pages were not loaded.');
          break;
        }
        cursors.add(next);
        cursor = next;
        if (page === 99)
          warnings.push('Codex history reached the 10,000-session limit for this section.');
      }
    }
    return { sessions, warnings };
  }

  private record(thread: JsonRecord, archived = false): SessionRecord {
    const source = string(thread.source) || string(thread.sourceKind);
    const transcript = makeTranscript(
      {
        agent: 'codex',
        sourcePath: string(thread.path) || `codex-app-server:${this.home}`,
        modifiedAt: new Date().toISOString(),
        archived,
      },
      {
        nativeId: string(thread.id),
        title:
          string(thread.name) ||
          string(thread.preview).replace(/\s+/g, ' ').slice(0, 110) ||
          'Untitled Codex session',
        projectPath: string(thread.cwd),
        createdAt: date(thread.createdAt, new Date().toISOString()),
        updatedAt: date(thread.updatedAt, new Date().toISOString()),
        model: string(thread.model) || undefined,
        sourceKind: source === 'vscode' ? 'ide' : source === 'appServer' ? 'desktop' : 'cli',
      },
      [],
    );
    return {
      ...transcript.session,
      preview: string(thread.preview).slice(0, 2400),
      sourcePath: string(thread.path) || undefined,
    };
  }

  async transcript(session: SessionRecord): Promise<Transcript> {
    await this.start();
    const result = object(await this.request('thread/read', { threadId: session.nativeId }));
    const thread = object(result.thread);
    const messages: SessionMessage[] = [];
    const warnings: string[] = [];
    let truncated = false;
    let cursor: string | undefined;
    let historyBytes = 0;
    const cursors = new Set<string>();
    const turns: JsonRecord[] = [];
    try {
      for (let page = 0; page < 100; page++) {
        const batch = object(
          await this.request('thread/turns/list', {
            threadId: session.nativeId,
            limit: 50,
            sortDirection: 'desc',
            itemsView: 'full',
            ...(cursor ? { cursor } : {}),
          }),
        );
        if (!Array.isArray(batch.data))
          throw new Error('Codex thread/turns/list returned no turns array.');
        historyBytes += JSON.stringify(batch).length;
        if (historyBytes > 32 * 1024 * 1024) {
          warnings.push(
            'The Codex transcript reached the 32 MiB history limit. Older turns were not loaded.',
          );
          truncated = true;
          break;
        }
        turns.push(...batch.data.map(object));
        const next = string(batch.nextCursor);
        if (!next) break;
        if (cursors.has(next)) {
          warnings.push('Codex repeated a transcript cursor. Older turns were not loaded.');
          truncated = true;
          break;
        }
        cursors.add(next);
        cursor = next;
        if (page === 99) truncated = true;
      }
      turns.reverse();
    } catch (error) {
      if (!(error instanceof RpcError) || ![-32601, -32602].includes(error.code)) throw error;
      const legacy = object(
        await this.request('thread/read', { threadId: session.nativeId, includeTurns: true }),
      );
      if (!Array.isArray(object(legacy.thread).turns))
        throw new Error('This Codex version cannot provide a readable stored transcript.');
      turns.splice(0, turns.length, ...list(object(legacy.thread).turns).map(object));
      warnings.push('This Codex version uses the older thread/read history interface.');
    }
    const seen = new Set<string>();
    for (const [turnIndex, turn] of turns.entries()) {
      for (const [index, raw] of list(turn.items).entries()) {
        const item = object(raw);
        const id = string(item.id) || `turn-${turnIndex}-item-${index}`;
        if (seen.has(id)) continue;
        seen.add(id);
        const type = string(item.type);
        let role: SessionMessage['role'] = 'system';
        let content = '';
        let toolName: string | undefined;
        if (type === 'userMessage') {
          role = 'user';
          content = contentText(item.content);
        } else if (type === 'agentMessage') {
          role = 'assistant';
          content = contentText(item.text ?? item.content);
        } else if (type === 'reasoning') {
          content = contentText(item.summary ?? item.content);
        } else if (type === 'commandExecution') {
          role = 'tool';
          toolName = 'Shell';
          content = `${string(item.command)}\n${string(item.aggregatedOutput)}`;
        } else if (type === 'fileChange') {
          role = 'tool';
          toolName = 'File changes';
          content = list(item.changes)
            .map((rawChange) => {
              const change = object(rawChange);
              return `${string(change.path)}\n${string(change.diff)}`;
            })
            .join('\n');
        } else if (/tool|search|image|collab/i.test(type)) {
          role = 'tool';
          toolName = string(item.tool) || type;
          content = contentText(item.result ?? item.output ?? item.content) || toolName;
        }
        if (content.trim())
          messages.push({
            id,
            role,
            content: content.slice(0, 80000),
            toolName,
            timestamp: date(turn.startedAt, session.updatedAt),
          });
      }
    }
    const updated = this.record({ ...thread, id: session.nativeId }, session.archived);
    const transcript = makeTranscript(
      {
        agent: 'codex',
        sourcePath: session.sourcePath || '',
        modifiedAt: session.updatedAt,
        truncated,
        warnings,
      },
      { ...session, ...updated, nativeId: session.nativeId },
      messages,
    );
    transcript.session = { ...session, ...updated, id: session.id, messageCount: messages.length };
    if (!messages.length)
      transcript.warnings.push(
        'The Codex history API returned no displayable messages for this session.',
      );
    return transcript;
  }
}
