import { useMemo, useState, type ReactElement } from 'react';
import {
  ArrowDownToLine,
  ArrowUpRight,
  Folder,
  MessageSquare,
  Play,
  RefreshCw,
  Search,
  SlidersHorizontal,
  X,
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { AgentId, Bootstrap, LaunchRequest, SessionRecord } from '../../shared/types';
import { desk, useSessions, useTranscript } from '../api';
import { AGENTS, agentName, dateLabel, relativeDate } from '../utils';
import { AgentMark, EmptyState, ErrorBox, Spinner, useNotices, Warnings } from '../ui';

interface SessionsProps {
  bootstrap: Bootstrap;
  search: string;
  setSearch: (value: string) => void;
  project: string;
  setProject: (value: string) => void;
  onNew: () => void;
  onLaunch: (request: LaunchRequest) => Promise<boolean>;
}
export function Sessions({
  bootstrap,
  search,
  setSearch,
  project,
  setProject,
  onNew,
  onLaunch,
}: SessionsProps): ReactElement {
  const sessions = useSessions(
    bootstrap.settings.autoRefreshSeconds,
    bootstrap.settings.scanOnStart,
  );
  const query = useQueryClient();
  const [selected, setSelected] = useState<string>();
  const [agent, setAgent] = useState('all');
  const [model, setModel] = useState('all');
  const [advanced, setAdvanced] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const { run } = useNotices();
  const records = sessions.data?.sessions ?? [];
  const models = [...new Set(records.map((s) => s.model).filter((m): m is string => !!m))];
  const projects = [...new Set(records.map((s) => s.projectPath).filter(Boolean))];
  const filtered = useMemo(
    () =>
      records
        .filter(
          (s) =>
            (agent === 'all' || s.agent === agent) &&
            (project === 'all' || s.projectPath === project) &&
            (model === 'all' || s.model === model) &&
            `${s.title} ${s.preview} ${s.projectPath} ${s.model ?? ''} ${s.nativeId}`
              .toLowerCase()
              .includes(search.toLowerCase()),
        )
        .sort((a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt)),
    [records, agent, project, model, search],
  );
  const current = filtered.find((s) => s.id === selected) ?? filtered[0];
  const refresh = async (): Promise<void> => {
    setRefreshing(true);
    await run(async () => {
      await sessions.refetch({ throwOnError: true });
      await query.invalidateQueries({ queryKey: ['transcript'] });
    });
    setRefreshing(false);
  };
  return (
    <div className="sessions-page">
      <header className="page-heading">
        <div>
          <div className="eyebrow">YOUR WORK, TOGETHER</div>
          <h1>
            Sessions<span className="heading-count">{records.length}</span>
          </h1>
          <p>Pick up a thought. Keep the momentum.</p>
        </div>
        <button
          className="secondary-button compact"
          onClick={() => void refresh()}
          disabled={refreshing}
        >
          <RefreshCw size={15} className={refreshing ? 'spin' : ''} />
          Refresh
        </button>
      </header>
      <div className="session-workbench">
        <section className="session-library" aria-label="Session library">
          <div className="library-controls">
            <div className="search-input">
              <Search size={16} />
              <input
                id="session-search"
                aria-label="Search sessions"
                placeholder="Search your sessions…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              {search ? (
                <button
                  className="icon-button"
                  aria-label="Clear search"
                  onClick={() => setSearch('')}
                >
                  <X size={14} />
                </button>
              ) : (
                <kbd aria-hidden="true">{bootstrap.platform === 'darwin' ? '⌘' : 'Ctrl'} K</kbd>
              )}
            </div>
            <div className="filter-row">
              <select
                aria-label="Filter sessions by agent"
                value={agent}
                onChange={(e) => setAgent(e.target.value)}
              >
                <option value="all">All agents</option>
                {AGENTS.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label}
                  </option>
                ))}
              </select>
              <button
                className={`filter-toggle ${advanced || project !== 'all' || model !== 'all' ? 'active' : ''}`}
                onClick={() => setAdvanced(!advanced)}
                aria-label="More session filters"
                aria-expanded={advanced}
              >
                <SlidersHorizontal size={14} />
                Filters
              </button>
            </div>
            {advanced && (
              <div className="advanced-filters">
                <select
                  aria-label="Filter sessions by project"
                  value={project}
                  onChange={(e) => setProject(e.target.value)}
                >
                  <option value="all">All projects</option>
                  {projects.map((p) => (
                    <option key={p} value={p}>
                      {p.split(/[\\/]/).at(-1)}
                    </option>
                  ))}
                </select>
                <select
                  aria-label="Filter sessions by model"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                >
                  <option value="all">All models</option>
                  {models.map((m) => (
                    <option key={m}>{m}</option>
                  ))}
                </select>
                <button
                  className="text-button"
                  onClick={() => {
                    setAgent('all');
                    setProject('all');
                    setModel('all');
                    setSearch('');
                  }}
                >
                  Reset filters
                </button>
              </div>
            )}
          </div>
          {sessions.isPending && !sessions.isFetching ? (
            <div className="list-empty">
              <Search size={23} />
              <strong>Ready when you are</strong>
              <p>Startup scanning is off. Refresh to read your local session history.</p>
              <button className="text-button" onClick={() => void refresh()}>
                Scan session history
              </button>
            </div>
          ) : sessions.isPending ? (
            <Spinner label="Reading local sessions" />
          ) : sessions.isError ? (
            <ErrorBox error={sessions.error} retry={() => void sessions.refetch()} />
          ) : (
            <div className="session-list">
              {filtered.map((session, i) => (
                <div key={session.id}>
                  {(i === 0 ||
                    dateLabel(session.updatedAt) !== dateLabel(filtered[i - 1].updatedAt)) && (
                    <div className="date-divider">{dateLabel(session.updatedAt)}</div>
                  )}
                  <button
                    className={`session-card ${current?.id === session.id ? 'selected' : ''}`}
                    onClick={() => setSelected(session.id)}
                    aria-pressed={current?.id === session.id}
                  >
                    <div className="session-card-meta">
                      <AgentMark agent={session.agent} small />
                      <span>{agentName(session.agent)}</span>
                      <time title={session.updatedAt}>{relativeDate(session.updatedAt)}</time>
                    </div>
                    <h3>{session.title || 'Untitled session'}</h3>
                    <p>{session.preview || 'Open this session to see its conversation.'}</p>
                    <div className="session-card-footer">
                      <Folder size={12} />
                      <span>{session.projectName || 'Unknown project'}</span>
                      <MessageSquare size={12} />
                      <span>{session.messageCount}</span>
                    </div>
                  </button>
                </div>
              ))}
              {!filtered.length && (
                <div className="list-empty">
                  <Search size={23} />
                  <strong>{records.length ? 'No matching sessions' : 'A fresh start'}</strong>
                  <p>
                    {records.length
                      ? 'Try another search or clear your filters.'
                      : 'Your local agent history will appear here. You can also add history folders in Settings.'}
                  </p>
                  {!records.length && (
                    <button className="text-button" onClick={onNew}>
                      Start your first session
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
          <div className="library-footer">
            <span>
              {filtered.length} {filtered.length === 1 ? 'session' : 'sessions'}
            </span>
            <span>Newest first</span>
          </div>
        </section>
        {current ? (
          <Conversation
            key={current.id}
            session={current}
            bootstrap={bootstrap}
            onLaunch={onLaunch}
          />
        ) : (
          <EmptyState
            title="Space for your next idea."
            action={
              <button className="primary-button" onClick={onNew}>
                Start a session <ArrowUpRight size={16} />
              </button>
            }
          >
            Claude, Codex, Gemini, and Antigravity. One place to find your work and get back to it.
          </EmptyState>
        )}
      </div>
      <Warnings warnings={sessions.data?.warnings} />
    </div>
  );
}
function Conversation({
  session,
  bootstrap,
  onLaunch,
}: {
  session: SessionRecord;
  bootstrap: Bootstrap;
  onLaunch: (request: LaunchRequest) => Promise<boolean>;
}): ReactElement {
  const transcript = useTranscript(session.id, session.updatedAt);
  const profiles = bootstrap.profiles.filter((p) => p.agent === session.agent);
  const defaultProfile =
    profiles.find((p) => p.id === bootstrap.settings.defaultProfileId) ??
    profiles.find((p) => p.provider === 'native') ??
    profiles[0];
  const [profile, setProfile] = useState(defaultProfile?.id ?? '');
  const [launching, setLaunching] = useState(false);
  const { run, notify } = useNotices();
  const resume = async (): Promise<void> => {
    setLaunching(true);
    try {
      await onLaunch({
        agent: session.agent,
        projectPath: session.projectPath,
        sessionId: session.id,
        profileId: profile || undefined,
      });
    } finally {
      setLaunching(false);
    }
  };
  return (
    <section className="conversation" aria-label="Session conversation">
      <header className="conversation-header">
        <div className="conversation-title">
          <div className="breadcrumb">
            <Folder size={13} />
            {session.projectName}
            <span>/</span>
            {agentName(session.agent)}
          </div>
          <h2>{session.title}</h2>
        </div>
        <div className="icon-actions">
          <button
            className="icon-button"
            title="Export conversation as Markdown"
            aria-label="Export conversation"
            onClick={() =>
              void run(async () => {
                const path = await desk.exportSession(session.id);
                if (path) notify(`Exported to ${path}`);
              })
            }
          >
            <ArrowDownToLine size={17} />
          </button>
          <button
            className="icon-button"
            title="Show project folder"
            aria-label="Show project folder"
            disabled={!session.projectPath}
            onClick={() => void run(() => desk.revealPath(session.projectPath))}
          >
            <Folder size={17} />
          </button>
        </div>
      </header>
      <div className="conversation-scroll">
        {transcript.isPending ? (
          <Spinner label="Opening conversation" />
        ) : transcript.isError ? (
          <ErrorBox error={transcript.error} retry={() => void transcript.refetch()} />
        ) : (
          <>
            <div className="conversation-origin">
              <span className="status-dot" />
              Local{' '}
              {session.sourceKind === 'ide'
                ? 'IDE'
                : session.sourceKind === 'desktop'
                  ? 'desktop'
                  : 'CLI'}{' '}
              history<span>·</span>
              {new Date(session.createdAt).toLocaleDateString(undefined, {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}
            </div>
            <div className="messages">
              {transcript.data.messages.map((message) => (
                <article className={`message message-${message.role}`} key={message.id}>
                  <div className="message-author">
                    {message.role === 'assistant' ? (
                      <AgentMark agent={session.agent} small />
                    ) : (
                      <span className="user-avatar">{message.role === 'user' ? 'Y' : '›'}</span>
                    )}
                    <strong>
                      {message.role === 'assistant'
                        ? agentName(session.agent)
                        : message.role === 'user'
                          ? 'You'
                          : (message.toolName ?? message.role)}
                    </strong>
                    {message.model && <span className="message-model">{message.model}</span>}
                    {message.timestamp && (
                      <time>
                        {new Date(message.timestamp).toLocaleTimeString(undefined, {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </time>
                    )}
                  </div>
                  {message.role === 'tool' ? (
                    <details className="tool-output">
                      <summary>{message.toolName ?? 'Tool output'}</summary>
                      <pre>{message.content}</pre>
                    </details>
                  ) : (
                    <div className="markdown">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          a: ({ href, children }) => (
                            <a
                              href={href}
                              onClick={(e) => {
                                e.preventDefault();
                                if (href && /^https?:\/\//.test(href))
                                  void run(() => desk.openExternal(href));
                              }}
                            >
                              {children}
                            </a>
                          ),
                          img: ({ alt }) => (
                            <span className="muted">[Image: {alt || 'attachment'}]</span>
                          ),
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </article>
              ))}
            </div>
            <Warnings warnings={transcript.data.warnings} />
            {transcript.data.truncated && (
              <div className="inline-note">
                This preview is shortened. The complete session remains in its original history
                file.
              </div>
            )}
            {!transcript.data.messages.length && (
              <EmptyState title="No readable messages yet">
                This source contains session metadata. Open its original app to view the full
                conversation.
              </EmptyState>
            )}
          </>
        )}
      </div>
      <footer className="conversation-footer">
        <div>
          <span className="eyebrow">CONTINUE WHERE YOU LEFT OFF</span>
          {session.resumable ? (
            <select
              aria-label="Profile for resuming session"
              value={profile}
              onChange={(e) => setProfile(e.target.value)}
            >
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          ) : (
            <p>{session.resumeNote ?? 'Resume is not available for this session source.'}</p>
          )}
        </div>
        {session.resumable ? (
          <button
            className="primary-button"
            onClick={() => void resume()}
            disabled={launching || !profile}
          >
            {launching ? <RefreshCw size={16} className="spin" /> : <Play size={15} />}Resume
            session
          </button>
        ) : (
          <button
            className="secondary-button"
            onClick={() => void run(() => desk.revealPath(session.projectPath))}
            disabled={!session.projectPath}
          >
            Open project
            <ArrowUpRight size={15} />
          </button>
        )}
      </footer>
    </section>
  );
}
