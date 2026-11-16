import { createHash } from 'node:crypto';
import path from 'node:path';
import type { AgentId, SessionMessage, SessionRecord, Transcript } from '../shared/types';

export type JsonRecord = Record<string, unknown>;

export interface SessionInput {
  agent: AgentId;
  sourcePath: string;
  sourceKind?: SessionRecord['sourceKind'];
  modifiedAt: string;
  projectPath?: string;
  nativeId?: string;
  title?: string;
  archived?: boolean;
  warnings?: string[];
  truncated?: boolean;
}

export const MAX_MESSAGES = 5000;
const MAX_CONTENT = 80000;

export function object(value: unknown): JsonRecord {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as JsonRecord)
    : {};
}

export function string(value: unknown): string {
  return typeof value === 'string' ? value : '';
}

export function list(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

export function date(value: unknown, fallback: string): string {
  const numeric = typeof value === 'number' ? (value < 1e11 ? value * 1000 : value) : undefined;
  const parsed = new Date(numeric ?? string(value));
  return Number.isFinite(parsed.getTime()) ? parsed.toISOString() : fallback;
}

export function contentText(value: unknown, depth = 0): string {
  if (depth > 8 || value === null || value === undefined) return '';
  if (typeof value === 'string') return value.slice(0, MAX_CONTENT);
  if (Array.isArray(value))
    return value
      .slice(0, 200)
      .map((item) => contentText(item, depth + 1))
      .filter(Boolean)
      .join('\n')
      .slice(0, MAX_CONTENT);
  const record = object(value);
  if (typeof record.text === 'string') return record.text.slice(0, MAX_CONTENT);
  if (record.type === 'tool_use' || record.type === 'function_call') {
    const args = record.input ?? record.arguments;
    const serialized =
      typeof args === 'string' ? args : args === undefined ? '' : JSON.stringify(args);
    return `${string(record.name) || 'Tool'}${serialized ? `\n${serialized}` : ''}`.slice(
      0,
      MAX_CONTENT,
    );
  }
  if (record.type === 'image' || record.type === 'image_url' || record.inlineData)
    return '[Image attachment]';
  for (const key of [
    'content',
    'parts',
    'message',
    'output',
    'result',
    'response',
    'markdown',
    'text_delta',
  ]) {
    if (record[key] !== undefined && record[key] !== value) {
      const text = contentText(record[key], depth + 1);
      if (text) return text;
    }
  }
  return '';
}

function titleFrom(messages: SessionMessage[]): string {
  const first = messages.find((message) => message.role === 'user' && message.content.trim());
  return (
    first?.content
      .replace(/<[^>]+>/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 110) || 'Untitled session'
  );
}

export function sessionKey(agent: AgentId, nativeId: string, sourcePath?: string): string {
  return `${agent}:${nativeId}:${createHash('sha256')
    .update(sourcePath || agent)
    .digest('hex')
    .slice(0, 12)}`;
}

function projectName(projectPath: string): string {
  if (!projectPath) return 'Unknown project';
  const parts = projectPath.replace(/\\/g, '/').split('/').filter(Boolean);
  return parts.at(-1) || projectPath;
}

export function makeTranscript(
  input: SessionInput,
  fields: Partial<SessionRecord>,
  allMessages: SessionMessage[],
): Transcript {
  const nativeId =
    fields.nativeId || input.nativeId || path.basename(input.sourcePath).replace(/\.jsonl?$/, '');
  const projectPath = fields.projectPath || input.projectPath || '';
  const sourceKind = fields.sourceKind || input.sourceKind || 'cli';
  const messages = allMessages.slice(-MAX_MESSAGES);
  const missingPath = !projectPath;
  const desktopImport = input.agent === 'antigravity' && sourceKind !== 'cli';
  const resumeNote =
    fields.resumeNote ||
    (desktopImport
      ? 'Import this conversation through Antigravity CLI /resume → Other. Native import creates a copy.'
      : missingPath
        ? 'The original project directory could not be determined. Add its project mapping before resuming.'
        : undefined);
  const record: SessionRecord = {
    id: sessionKey(input.agent, nativeId, input.sourcePath),
    nativeId,
    agent: input.agent,
    title: fields.title || input.title || titleFrom(messages),
    projectPath,
    projectName: projectName(projectPath),
    createdAt: fields.createdAt || messages[0]?.timestamp || input.modifiedAt,
    updatedAt: fields.updatedAt || messages.at(-1)?.timestamp || input.modifiedAt,
    preview: messages
      .filter((message) => message.role === 'user' || message.role === 'assistant')
      .slice(-3)
      .map((message) => message.content)
      .join('\n')
      .slice(-2400),
    messageCount: allMessages.length,
    model: fields.model || [...messages].reverse().find((message) => message.model)?.model,
    sourcePath: input.sourcePath || undefined,
    sourceKind,
    resumable: Boolean(nativeId && !missingPath && !desktopImport && !input.archived),
    resumeNote: input.archived
      ? 'This session is archived. Restore it in its native CLI before resuming.'
      : resumeNote,
    archived: input.archived || undefined,
  };
  return {
    session: record,
    messages,
    warnings: input.warnings ? [...input.warnings] : [],
    truncated: input.truncated || allMessages.length > MAX_MESSAGES || undefined,
  };
}

function claudeMessages(records: JsonRecord[]): SessionMessage[] {
  const messages: SessionMessage[] = [];
  for (const [index, record] of records.entries()) {
    const message = object(record.message);
    const raw = message.content ?? record.content;
    const content = contentText(raw);
    if (!content) continue;
    const baseRole = string(message.role) || string(record.type);
    if (!['user', 'assistant', 'system', 'tool'].includes(baseRole)) continue;
    const tool = list(raw).find((block) => object(block).type === 'tool_result');
    const toolUse = list(raw).find((block) => object(block).type === 'tool_use');
    messages.push({
      id: string(record.uuid) || `message-${index}`,
      role: tool ? 'tool' : (baseRole as SessionMessage['role']),
      content,
      timestamp: string(record.timestamp) || undefined,
      model: string(message.model) || undefined,
      toolName: string(object(toolUse).name) || undefined,
    });
  }
  return messages;
}

export function parseClaude(records: JsonRecord[], input: SessionInput): Transcript | null {
  const relevant = records.filter(
    (record) =>
      !record.isSidechain && ['user', 'assistant', 'system', 'tool'].includes(string(record.type)),
  );
  if (!relevant.length) return null;
  const nativeId =
    [...relevant]
      .reverse()
      .map((record) => string(record.sessionId))
      .find(Boolean) || input.nativeId;
  const projectPath =
    [...relevant]
      .reverse()
      .map((record) => string(record.cwd))
      .find(Boolean) || input.projectPath;
  const title = [...records]
    .reverse()
    .map(
      (record) =>
        string(record.customTitle) || (record.type === 'summary' ? string(record.summary) : ''),
    )
    .find(Boolean);
  const distinct = new Map<string, JsonRecord>();
  for (const [index, record] of relevant.entries())
    distinct.set(string(record.uuid) || `record-${index}`, record);
  let ordered = [...distinct.values()];
  const last = [...relevant]
    .reverse()
    .find((record) => ['user', 'assistant', 'tool'].includes(string(record.type)));
  if (last && typeof last.parentUuid !== 'undefined' && string(last.uuid)) {
    const nodes = new Map(
      records
        .filter((record) => string(record.uuid))
        .map((record) => [string(record.uuid), record]),
    );
    const chain: JsonRecord[] = [];
    const seen = new Set<string>();
    let cursor: JsonRecord | undefined = last;
    while (cursor && !seen.has(string(cursor.uuid))) {
      const id = string(cursor.uuid);
      seen.add(id);
      if (!cursor.isSidechain) chain.push(cursor);
      const parent = string(cursor.parentUuid);
      if (parent && !nodes.has(parent))
        input = {
          ...input,
          warnings: [
            ...(input.warnings || []),
            'Some earlier messages are unavailable in this transcript chain.',
          ],
        };
      cursor = nodes.get(parent);
    }
    ordered = chain.reverse();
  }
  const messages = claudeMessages(ordered);
  if (!messages.length) return null;
  return makeTranscript(
    input,
    {
      nativeId,
      projectPath,
      title,
      createdAt: date(relevant[0]?.timestamp, input.modifiedAt),
      updatedAt: date(relevant.at(-1)?.timestamp, input.modifiedAt),
    },
    messages,
  );
}

export function parseCodex(records: JsonRecord[], input: SessionInput): Transcript | null {
  const metadata = object(records.find((record) => record.type === 'session_meta')?.payload);
  const context = object(
    [...records].reverse().find((record) => record.type === 'turn_context')?.payload,
  );
  if (!Object.keys(metadata).length) return null;
  if (
    typeof metadata.source === 'object' &&
    Object.keys(object(metadata.source)).some((key) => /sub.?agent/i.test(key))
  )
    return null;
  const messages: SessionMessage[] = [];
  const responses = records.filter((record) => record.type === 'response_item');
  const hasMessages = responses.some((record) => object(record.payload).type === 'message');
  for (const [index, record] of records.entries()) {
    const payload = object(record.payload);
    if (record.type === 'response_item') {
      let role = string(payload.role);
      if (
        payload.type === 'function_call' ||
        payload.type === 'custom_tool_call' ||
        payload.type === 'function_call_output'
      )
        role = 'tool';
      if (!['user', 'assistant', 'system', 'tool'].includes(role)) continue;
      const text =
        payload.type === 'function_call'
          ? contentText(payload)
          : contentText(payload.content ?? payload.output ?? payload.input);
      if (!text) continue;
      messages.push({
        id: string(payload.id) || `response-${index}`,
        role: role as SessionMessage['role'],
        content: text,
        timestamp: string(record.timestamp) || undefined,
        toolName: string(payload.name) || undefined,
      });
    } else if (record.type === 'event_msg' && !hasMessages) {
      if (payload.type !== 'user_message' && payload.type !== 'agent_message') continue;
      const text = contentText(payload.message);
      if (text)
        messages.push({
          id: `event-${index}`,
          role: payload.type === 'user_message' ? 'user' : 'assistant',
          content: text,
          timestamp: string(record.timestamp) || undefined,
        });
    }
  }
  const source = string(metadata.source);
  return makeTranscript(
    input,
    {
      nativeId: string(metadata.id) || string(metadata.session_id) || input.nativeId,
      projectPath: string(context.cwd) || string(metadata.cwd) || input.projectPath,
      model: string(context.model) || string(metadata.model) || undefined,
      title: string(metadata.thread_name) || string(metadata.name) || input.title,
      sourceKind: source === 'vscode' ? 'ide' : source === 'appServer' ? 'desktop' : 'cli',
      createdAt: date(metadata.timestamp, input.modifiedAt),
      updatedAt: date(records.at(-1)?.timestamp, input.modifiedAt),
    },
    messages,
  );
}

export function parseGemini(records: JsonRecord[], input: SessionInput): Transcript | null {
  let metadata: JsonRecord = {};
  const messages = new Map<string, JsonRecord>();
  let counter = 0;
  const add = (value: unknown) => {
    const message = object(value);
    if (!['user', 'gemini', 'assistant', 'info', 'error', 'warning'].includes(string(message.type)))
      return;
    messages.set(string(message.id) || `message-${counter++}`, message);
  };
  for (const record of records) {
    if (typeof record.sessionId === 'string') {
      metadata = { ...metadata, ...record };
      list(record.messages).forEach(add);
    } else if (record.$set && typeof record.$set === 'object') {
      const patch = object(record.$set);
      if (Array.isArray(patch.messages)) {
        messages.clear();
        patch.messages.forEach(add);
      }
      metadata = { ...metadata, ...patch };
    } else if (typeof record.$rewindTo === 'string') {
      const target = record.$rewindTo;
      let found = false;
      for (const id of messages.keys()) {
        if (id === target) found = true;
        if (found) messages.delete(id);
      }
      if (!found) messages.clear();
    } else if (record.$patch) {
      const patch = object(record.$patch);
      const applyPatch = (value: unknown) => {
        const update = object(value);
        const existing = messages.get(string(update.id));
        if (!existing) return;
        if (update.content !== undefined) existing.content = update.content;
        for (const rawTool of list(update.toolCalls)) {
          const toolPatch = object(rawTool);
          const existingTool = list(existing.toolCalls).find(
            (tool) => object(tool).id === toolPatch.id,
          );
          if (existingTool && 'result' in toolPatch) object(existingTool).result = toolPatch.result;
        }
      };
      applyPatch(patch);
      list(patch.updates).forEach(applyPatch);
      list(patch.removeIds).forEach((id) => messages.delete(string(id)));
      if (Array.isArray(patch.orderIds)) {
        const ordered = patch.orderIds
          .map((id) => [string(id), messages.get(string(id))] as const)
          .filter((entry): entry is readonly [string, JsonRecord] => Boolean(entry[1]));
        for (const [id] of ordered) messages.delete(id);
        for (const [id, message] of ordered) messages.set(id, message);
      }
    } else {
      add(record);
    }
  }
  if (!string(metadata.sessionId) || metadata.kind === 'subagent') return null;
  const parsed: SessionMessage[] = [];
  for (const [id, message] of messages) {
    const content = contentText(message.displayContent ?? message.content);
    const role =
      message.type === 'user'
        ? 'user'
        : ['gemini', 'assistant'].includes(string(message.type))
          ? 'assistant'
          : 'system';
    if (content)
      parsed.push({
        id,
        role,
        content,
        timestamp: string(message.timestamp) || undefined,
        model: string(message.model) || undefined,
      });
    for (const [index, item] of list(message.toolCalls).entries()) {
      const tool = object(item);
      const result = contentText(tool.result);
      parsed.push({
        id: string(tool.id) || `${id}-tool-${index}`,
        role: 'tool',
        content:
          `${string(tool.name) || 'Tool'}\n${result || JSON.stringify(tool.args ?? {})}`.slice(
            0,
            MAX_CONTENT,
          ),
        toolName: string(tool.name) || undefined,
        timestamp: string(tool.timestamp) || undefined,
      });
    }
  }
  return makeTranscript(
    input,
    {
      nativeId: string(metadata.sessionId),
      projectPath: string(metadata.cwd) || input.projectPath,
      title: string(metadata.summary) || undefined,
      createdAt: date(metadata.startTime, input.modifiedAt),
      updatedAt: date(metadata.lastUpdated, input.modifiedAt),
    },
    parsed,
  );
}

export function parseAntigravity(records: JsonRecord[], input: SessionInput): Transcript | null {
  const messages: SessionMessage[] = [];
  let nativeId = input.nativeId || '';
  let projectPath = input.projectPath || '';
  let title = input.title || '';
  let model = '';
  for (const [index, row] of records.entries()) {
    const record = Object.keys(object(row.step_update)).length ? object(row.step_update) : row;
    const metadata = { ...object(row.metadata), ...object(row.init), ...record };
    nativeId = string(metadata.conversation_id) || string(metadata.conversationId) || nativeId;
    projectPath = string(metadata.cwd) || string(list(metadata.workspacePaths)[0]) || projectPath;
    title = string(metadata.conversation_title) || string(metadata.title) || title;
    model =
      string(metadata.modelName) ||
      string(metadata.model) ||
      string(object(metadata.model).id) ||
      model;
    const type =
      string(record.type) || string(record.step_type) || string(record.role) || string(row.event);
    const nested = object(record.message);
    let role = string(nested.role) || string(record.role);
    if (!role) {
      if (/user_input|user_message|^user$/i.test(type)) role = 'user';
      if (/agent_response|assistant|model_response|^gemini$/i.test(type)) role = 'assistant';
      if (/tool|command/i.test(type)) role = 'tool';
    }
    if (!['user', 'assistant', 'system', 'tool'].includes(role)) continue;
    const text = contentText(
      record.content ??
        nested.content ??
        record.text ??
        record.text_delta ??
        record.user_input ??
        record.agent_response ??
        record.result ??
        record.message,
    );
    if (!text) continue;
    const stepId = typeof record.step_index === 'number' ? `step-${record.step_index}` : '';
    const existing = stepId ? messages.find((message) => message.id === stepId) : undefined;
    if (existing && typeof record.text_delta === 'string')
      existing.content = (existing.content + text).slice(0, MAX_CONTENT);
    else
      messages.push({
        id: string(record.id) || stepId || `message-${index}`,
        role: role as SessionMessage['role'],
        content: text,
        timestamp: string(record.timestamp) || string(row.timestamp) || undefined,
        model: model || undefined,
        toolName: string(record.tool_name) || string(record.toolName) || undefined,
      });
  }
  if (!nativeId && !messages.length) return null;
  const transcript = makeTranscript(
    input,
    { nativeId, projectPath, title, model: model || undefined },
    messages,
  );
  if (!messages.length)
    transcript.warnings.push(
      'This Antigravity transcript has no recognized message records. Use the native CLI to inspect this conversation.',
    );
  return transcript;
}
