import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SessionService } from '../src/main/sessions';
import { parseGemini } from '../src/main/session-formats';
import type { AppSettings } from '../src/shared/types';

let home: string;
let project: string;
let settings: AppSettings;
let service: SessionService;
const now = '2026-11-16T09:00:00.000Z';

async function write(relative: string, content: string): Promise<string> {
  const file = path.join(home, relative);
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, content);
  return file;
}

async function jsonl(relative: string, records: unknown[]): Promise<string> {
  return write(relative, `${records.map(record => JSON.stringify(record)).join('\n')}\n`);
}

beforeEach(async () => {
  vi.stubEnv('CLAUDE_CONFIG_DIR', '');
  vi.stubEnv('CODEX_HOME', '');
  vi.stubEnv('GEMINI_CLI_HOME', '');
  home = await fs.mkdtemp(path.join(os.tmpdir(), 'agent-desk-sessions-'));
  project = path.join(home, 'project');
  await fs.mkdir(project);
  settings = {
    theme: 'dark', fontSize: 14, terminalScrollback: 5000, defaultProfileId: '', projects: [project],
    historyRoots: [], skillDirectories: [], agentCommands: { claude: 'claude', codex: path.join(home, 'not-installed'), gemini: 'gemini', antigravity: 'agy' },
    proxyCommand: '', scanOnStart: true, autoRefreshSeconds: 30,
  };
  service = new SessionService({ home, settings: () => settings });
});

afterEach(async () => {
  service.close();
  vi.unstubAllEnvs();
  await fs.rm(home, { recursive: true, force: true });
});

describe('session histories', () => {
  it('reconstructs the selected Claude branch and ignores subagent and malformed lines', async () => {
    const file = await jsonl('.claude/projects/project/session-one.jsonl', [
      { type: 'user', uuid: 'u1', parentUuid: null, sessionId: 'one', cwd: project, timestamp: now, message: { role: 'user', content: 'Build the desktop app' } },
      { type: 'assistant', uuid: 'a1', parentUuid: 'u1', sessionId: 'one', cwd: project, timestamp: now, message: { role: 'assistant', model: 'native-model', content: [{ type: 'text', text: 'An abandoned answer' }] } },
      { type: 'assistant', uuid: 'a2', parentUuid: 'u1', sessionId: 'one', cwd: project, timestamp: now, message: { role: 'assistant', model: 'selected-model', content: [{ type: 'text', text: 'The current answer' }] } },
      { type: 'custom-title', customTitle: 'Agent Desk implementation' },
    ]);
    await fs.appendFile(file, '{incomplete\n');
    await jsonl('.claude/projects/project/session-one/subagents/agent-one.jsonl', [{ type: 'user', uuid: 'sub', sessionId: 'sub', message: { role: 'user', content: 'Do not index subagents' } }]);
    const index = await service.index();
    expect(index.sessions).toHaveLength(1);
    expect(index.sessions[0]).toMatchObject({ agent: 'claude', title: 'Agent Desk implementation', model: 'selected-model', projectPath: project, resumable: true });
    expect(index.warnings.join(' ')).toContain('malformed');
    const transcript = await service.transcript(index.sessions[0].id);
    expect(transcript.messages.map(message => message.content)).toEqual(['Build the desktop app', 'The current answer']);
  });

  it('reads Codex rollouts and archived sessions with an explicit unavailable-server warning', async () => {
    const records = [
      { type: 'session_meta', payload: { id: 'codex-one', cwd: project, source: 'cli', timestamp: now } },
      { type: 'turn_context', payload: { cwd: project, model: 'model-from-context' } },
      { type: 'response_item', timestamp: now, payload: { type: 'message', role: 'user', content: [{ type: 'input_text', text: 'Inspect the proxy route' }] } },
      { type: 'response_item', timestamp: now, payload: { type: 'message', role: 'assistant', content: [{ type: 'output_text', text: 'The proxy is configured.' }] } },
    ];
    await jsonl('.codex/sessions/2026/11/16/rollout-one.jsonl', records);
    await jsonl('.codex/archived_sessions/rollout-archived.jsonl', [{ ...records[0], payload: { ...records[0].payload, id: 'codex-archived' } }, ...records.slice(1)]);
    const index = await service.index();
    expect(index.sessions).toHaveLength(2);
    expect(index.warnings.join(' ')).toContain('Local rollout files');
    expect(index.warnings.join(' ')).toContain('was not found');
    const active = index.sessions.find(session => !session.archived)!;
    expect(active).toMatchObject({ model: 'model-from-context', projectPath: project, resumable: true });
    expect(index.sessions.find(session => session.archived)).toMatchObject({ resumable: false });
    expect((await service.transcript(active.id)).messages.map(message => message.role)).toEqual(['user', 'assistant']);
  });

  it('deduplicates repeated Claude records without requiring linked ancestry', async () => {
    await jsonl('.claude/projects/project/repeated.jsonl', [
      { type: 'user', uuid: 'u1', sessionId: 'repeated', cwd: project, message: { role: 'user', content: 'Review the change' } },
      { type: 'assistant', uuid: 'a1', sessionId: 'repeated', message: { role: 'assistant', content: 'Partial answer' } },
      { type: 'assistant', uuid: 'a1', sessionId: 'repeated', message: { role: 'assistant', content: 'Complete answer' } },
    ]);
    const index = await service.index();
    expect((await service.transcript(index.sessions[0].id)).messages.map(message => message.content)).toEqual(['Review the change', 'Complete answer']);
  });

  it('reads legacy Gemini JSON and maps its actual project marker', async () => {
    await write('.gemini/tmp/project-slug/.project_root', project);
    await write('.gemini/tmp/project-slug/chats/session-old.json', JSON.stringify({
      sessionId: 'gemini-legacy', projectHash: 'opaque-hash', startTime: now, lastUpdated: now,
      messages: [
        { id: 'g1', type: 'user', timestamp: now, content: [{ text: 'Fix the status line' }] },
        { id: 'g2', type: 'gemini', timestamp: now, model: 'gemini-local', content: 'Fixed it.' },
      ],
    }));
    const index = await service.index();
    expect(index.sessions[0]).toMatchObject({ nativeId: 'gemini-legacy', agent: 'gemini', projectPath: project, resumable: true, model: 'gemini-local' });
    expect((await service.transcript(index.sessions[0].id)).messages[0].content).toBe('Fix the status line');
  });

  it('applies current Gemini JSONL patches, metadata, tool result updates and rewind semantics', () => {
    const transcript = parseGemini([
      { sessionId: 'gemini-current', projectHash: 'hash', startTime: now },
      { id: 'u1', type: 'user', content: 'Original prompt' },
      { id: 'a1', type: 'gemini', content: 'Initial response', toolCalls: [{ id: 't1', name: 'read_file', args: { path: 'README.md' } }] },
      { $patch: { updates: [{ id: 'u1', content: 'Corrected prompt' }, { id: 'a1', content: 'Final response', toolCalls: [{ id: 't1', result: [{ text: 'File content' }] }] }] } },
      { id: 'u2', type: 'user', content: 'Discard this branch' },
      { id: 'a2', type: 'gemini', content: 'Also discarded' },
      { $rewindTo: 'u2' },
      { $set: { summary: 'Reviewed readme', lastUpdated: now } },
    ], { agent: 'gemini', sourcePath: '/tmp/session.jsonl', modifiedAt: now, projectPath: project });
    expect(transcript?.session.title).toBe('Reviewed readme');
    expect(transcript?.messages.map(message => message.content)).toEqual(['Corrected prompt', 'Final response', 'read_file\nFile content']);
  });

  it('does not fabricate a cwd from opaque Gemini folder names', async () => {
    await jsonl('.gemini/tmp/opaque/chats/session-current.jsonl', [
      { sessionId: 'unmapped-gemini', projectHash: 'opaque', startTime: now, lastUpdated: now },
      { id: 'g1', type: 'user', content: 'Find my project' },
    ]);
    const index = await service.index();
    expect(index.sessions[0]).toMatchObject({ projectPath: '', resumable: false });
    expect(index.sessions[0].resumeNote).toContain('could not be determined');
  });

  it('respects Gemini home as the parent directory of .gemini', async () => {
    const parent = path.join(home, 'isolated');
    vi.stubEnv('GEMINI_CLI_HOME', parent);
    await write('isolated/.gemini/tmp/example/.project_root', project);
    await jsonl('isolated/.gemini/tmp/example/chats/session-isolated.jsonl', [
      { sessionId: 'isolated', projectHash: 'hash', startTime: now },
      { id: 'g1', type: 'user', content: 'Isolated state' },
    ]);
    expect((await service.index()).sessions.map(session => session.nativeId)).toEqual(['isolated']);
  });

  it('indexes Antigravity CLI transcripts and marks App sessions for native import', async () => {
    await write('.gemini/antigravity-cli/cache/last_conversations.json', JSON.stringify({ [project]: 'agy-cli' }));
    await jsonl('.gemini/antigravity-cli/brain/agy-cli/.system_generated/logs/transcript.jsonl', [
      { type: 'user', content: 'Continue the CLI work', timestamp: now },
      { type: 'assistant', content: 'Ready to continue', timestamp: now },
    ]);
    await jsonl('.gemini/antigravity/brain/agy-app/.system_generated/logs/transcript.jsonl', [
      { type: 'user', content: 'App-only work', workspacePaths: [project], timestamp: now },
    ]);
    const index = await service.index();
    expect(index.sessions).toHaveLength(2);
    expect(index.sessions.find(session => session.nativeId === 'agy-cli')).toMatchObject({ projectPath: project, sourceKind: 'cli', resumable: true });
    expect(index.sessions.find(session => session.nativeId === 'agy-app')).toMatchObject({ sourceKind: 'desktop', resumable: false });
    expect(index.sessions.find(session => session.nativeId === 'agy-app')?.resumeNote).toContain('/resume → Other');
  });

  it('reports unrecognized Antigravity rows instead of fabricating chat messages', async () => {
    await jsonl('.gemini/antigravity-cli/brain/agy-unknown/.system_generated/logs/transcript.jsonl', [{ storageVersion: 999, binary: 'opaque' }]);
    const index = await service.index();
    expect(index.sessions).toHaveLength(1);
    expect(index.warnings.join(' ')).toContain('no recognized message records');
    expect((await service.transcript(index.sessions[0].id)).messages).toEqual([]);
  });

  it('skips symlink directories and files, supports custom roots and refreshes changed files', async () => {
    const file = await jsonl('custom-history/session.jsonl', [{ type: 'user', sessionId: 'custom', cwd: project, message: { role: 'user', content: 'First message' } }]);
    settings.historyRoots = [{ id: 'extra', agent: 'claude', path: path.join(home, 'custom-history') }];
    await fs.symlink(path.dirname(file), path.join(home, 'custom-history', 'cycle'), 'dir');
    await fs.symlink(file, path.join(home, 'custom-history', 'copy.jsonl'));
    let index = await service.index();
    expect(index.sessions).toHaveLength(1);
    expect(index.sessions[0]).toMatchObject({ projectPath: project, resumable: false });
    expect(index.sessions[0].resumeNote).toContain('outside the active native session store');
    await fs.appendFile(file, `${JSON.stringify({ type: 'assistant', sessionId: 'custom', message: { role: 'assistant', content: 'Second message' } })}\n`);
    index = await service.index(true);
    expect(index.sessions).toHaveLength(1);
    expect((await service.transcript(index.sessions[0].id)).messages).toHaveLength(2);
    await expect(service.transcript('../../.credentials.json')).rejects.toThrow('Session not found');
  });

  it('prefers the active native identity over a newer exported copy', async () => {
    const record = { type: 'user', sessionId: 'same-session', cwd: project, timestamp: now, message: { role: 'user', content: 'Native conversation' } };
    const nativeFile = await jsonl('.claude/projects/project/same-session.jsonl', [record]);
    await jsonl('exports/same-session.jsonl', [{ ...record, timestamp: '2026-11-17T09:00:00.000Z', message: { role: 'user', content: 'Newer exported copy' } }]);
    settings.historyRoots = [
      { id: 'native-alias', agent: 'claude', path: path.join(home, '.claude/projects') },
      { id: 'exports', agent: 'claude', path: path.join(home, 'exports') },
    ];
    const index = await service.index();
    expect(index.sessions).toHaveLength(1);
    expect(index.sessions[0]).toMatchObject({ sourcePath: nativeFile, resumable: true, title: 'Native conversation' });
    expect((await service.transcript(index.sessions[0].id)).messages[0].content).toBe('Native conversation');
  });

  it('enables an external history only when it becomes the configured active store', async () => {
    await jsonl('alternate-config/projects/project/alternate.jsonl', [{ type: 'user', sessionId: 'alternate', cwd: project, message: { role: 'user', content: 'Separate native configuration' } }]);
    settings.historyRoots = [{ id: 'alternate', agent: 'claude', path: path.join(home, 'alternate-config/projects') }];
    expect((await service.index()).sessions[0].resumable).toBe(false);
    vi.stubEnv('CLAUDE_CONFIG_DIR', path.join(home, 'alternate-config'));
    const native = (await service.index()).sessions[0];
    expect(native.resumable).toBe(true);
    expect(native.resumeNote).toBeUndefined();
  });

  it('does not claim arbitrary Antigravity export folders are CLI histories', async () => {
    await jsonl('exports/brain/agy-copy/.system_generated/logs/transcript.jsonl', [{ type: 'user', cwd: project, content: 'Copied desktop history' }]);
    settings.historyRoots = [{ id: 'export', agent: 'antigravity', path: path.join(home, 'exports') }];
    const record = (await service.index()).sessions[0];
    expect(record).toMatchObject({ nativeId: 'agy-copy', sourceKind: 'desktop', projectPath: project, resumable: false });
    expect(record.resumeNote).toContain('outside the active native session store');
    expect((await service.transcript(record.id)).messages[0].content).toBe('Copied desktop history');
  });

  it('disables resume when the recorded project no longer exists', async () => {
    await jsonl('.claude/projects/deleted/session.jsonl', [{ type: 'user', sessionId: 'deleted', cwd: path.join(home, 'missing'), message: { role: 'user', content: 'An old project' } }]);
    expect((await service.index()).sessions[0]).toMatchObject({ resumable: false, resumeNote: 'The original project directory is not available on this computer.' });
  });
});

async function fakeCodex(legacy = false): Promise<string> {
  await fs.mkdir(path.join(home, '.codex'), { recursive: true });
  const script = `#!/usr/bin/env node
import readline from 'node:readline';
import fs from 'node:fs';
const project = ${JSON.stringify(project)};
const legacy = ${JSON.stringify(legacy)};
const log = ${JSON.stringify(path.join(home, 'requests.jsonl'))};
const turn = (id, text) => ({ id, startedAt: 1794819600, items: [{ id: id + '-item', type: 'agentMessage', text }] });
const thread = id => ({ id, cwd: project, name: 'Server ' + id, preview: 'From native metadata', createdAt: 1794816000, updatedAt: 1794819600, model: 'test-codex', source: 'cli' });
readline.createInterface({ input: process.stdin }).on('line', line => {
  const request = JSON.parse(line);
  fs.appendFileSync(log, JSON.stringify(request) + '\\n');
  if (request.id === undefined) return;
  const p = request.params || {};
  let result = {};
  if (request.method === 'thread/list') result = p.archived ? { data: [], nextCursor: null } : p.cursor ? { data: [thread('second')], nextCursor: null } : { data: [thread('first')], nextCursor: 'next-page' };
  if (request.method === 'thread/read') result = { thread: { ...thread(p.threadId), turns: p.includeTurns ? [turn('old', 'Legacy history')] : [] } };
  if (request.method === 'thread/turns/list') {
    if (legacy) { process.stdout.write(JSON.stringify({ id: request.id, error: { code: -32601, message: 'unknown method' } }) + '\\n'); return; }
    result = p.cursor ? { data: [turn('earlier', 'Earlier turn')], nextCursor: null } : { data: [turn('latest', 'Latest turn')], nextCursor: 'older-page' };
  }
  process.stdout.write(JSON.stringify({ id: request.id, result }) + '\\n');
});
`;
  const command = await write('fake-codex.mjs', script);
  await fs.chmod(command, 0o755);
  return command;
}

describe('Codex app-server history protocol', () => {
  it('initializes, pages all providers, and reads paginated turns without resuming', async () => {
    settings.agentCommands.codex = await fakeCodex();
    const index = await service.index();
    expect(index.warnings).toEqual([]);
    expect(index.sessions).toHaveLength(2);
    const transcript = await service.transcript(index.sessions[0].id);
    expect(transcript.messages.map(message => message.content)).toEqual(['Earlier turn', 'Latest turn']);
    const requests = (await fs.readFile(path.join(home, 'requests.jsonl'), 'utf8')).trim().split('\n').map(line => JSON.parse(line));
    expect(requests.some(request => request.method === 'initialize')).toBe(true);
    expect(requests.filter(request => request.method === 'thread/list').every(request => Array.isArray(request.params.modelProviders) && request.params.modelProviders.length === 0)).toBe(true);
    expect(requests.some(request => request.method === 'thread/turns/list' && request.params.cursor === 'older-page')).toBe(true);
    expect(requests.some(request => request.method === 'thread/resume' || request.method === 'turn/start')).toBe(false);
  });

  it('uses the documented older read-history method with a visible compatibility warning', async () => {
    settings.agentCommands.codex = await fakeCodex(true);
    const index = await service.index();
    const transcript = await service.transcript(index.sessions[0].id);
    expect(transcript.messages[0].content).toBe('Legacy history');
    expect(transcript.warnings.join(' ')).toContain('older thread/read');
  });

  it('does not recreate a failing native history process on every refresh', async () => {
    await fs.mkdir(path.join(home, '.codex'), { recursive: true });
    const log = path.join(home, 'starts.txt');
    const command = await write('failing-codex.mjs', `#!/usr/bin/env node\nimport fs from 'node:fs';\nfs.appendFileSync(${JSON.stringify(log)}, 'start\\n');\nprocess.exit(1);\n`);
    await fs.chmod(command, 0o755);
    settings.agentCommands.codex = command;
    const first = await service.index();
    const second = await service.index(true);
    expect(first.warnings.join(' ')).toContain('exited');
    expect(second.warnings.join(' ')).toContain('retries after one minute');
    expect((await fs.readFile(log, 'utf8')).trim().split('\n')).toHaveLength(1);
  });
});
