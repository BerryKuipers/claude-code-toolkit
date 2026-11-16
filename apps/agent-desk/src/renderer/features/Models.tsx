import { useEffect, useState, type ReactElement } from 'react';
import {
  ArrowRight,
  BookOpen,
  Cable,
  Check,
  CircleDot,
  Clock3,
  Ellipsis,
  ExternalLink,
  KeyRound,
  Pencil,
  Play,
  Plus,
  Radio,
  Search,
  Server,
  ShieldCheck,
  Trash2,
  Zap,
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import type { Bootstrap, ProviderProfile, ProviderStatus, TerminalInfo } from '../../shared/types';
import { desk, useCatalog } from '../api';
import { AGENTS, agentName, contextLabel } from '../utils';
import { AgentMark, EmptyState, ErrorBox, Modal, Spinner, useNotices, Warnings } from '../ui';
import { ProfileEditor } from './ProfileEditor';

export function Models({
  bootstrap,
  onTerminal,
}: {
  bootstrap: Bootstrap;
  onTerminal: (terminal: TerminalInfo) => void;
}): ReactElement {
  const [edit, setEdit] = useState<ProviderProfile | 'new'>();
  const [catalog, setCatalog] = useState<ProviderProfile>();
  const [remove, setRemove] = useState<ProviderProfile>();
  const [agent, setAgent] = useState('all');
  const [statuses, setStatuses] = useState<Record<string, ProviderStatus>>({});
  const [testing, setTesting] = useState<string>();
  useEffect(() => setStatuses({}), [bootstrap.profiles]);
  const [monitor, setMonitor] = useState<unknown>();
  const [monitorOpen, setMonitorOpen] = useState(false);
  const [starting, setStarting] = useState(false);
  const [authProvider, setAuthProvider] = useState<'codex' | 'kimi' | 'grok' | 'cursor'>('codex');
  const [authenticating, setAuthenticating] = useState(false);
  const query = useQueryClient();
  const { run } = useNotices();
  const profiles = bootstrap.profiles.filter((p) => agent === 'all' || p.agent === agent);
  const proxy = bootstrap.profiles.find((p) => p.provider === 'local-proxy');
  const test = async (profile: ProviderProfile): Promise<void> => {
    setTesting(profile.id);
    const result = await run(() => desk.probe(profile.id));
    if (result) setStatuses((current) => ({ ...current, [profile.id]: result }));
    setTesting(undefined);
  };
  const authenticate = async (): Promise<void> => {
    setAuthenticating(true);
    const terminal = await run(() => desk.proxyAuthenticate(authProvider));
    if (terminal) onTerminal(terminal);
    setAuthenticating(false);
  };
  const startProxy = async (): Promise<void> => {
    setStarting(true);
    const terminal = await run(() => desk.proxyStart());
    if (terminal) onTerminal(terminal);
    setStarting(false);
  };
  return (
    <div className="standard-page models-page">
      <header className="page-heading">
        <div>
          <div className="eyebrow">THE RIGHT TOOLS FOR THE THOUGHT</div>
          <h1>Models & connections</h1>
          <p>Your subscriptions, your proxy, your choice of models.</p>
        </div>
        <button className="primary-button" onClick={() => setEdit('new')}>
          <Plus size={16} />
          Add connection
        </button>
      </header>
      <div className="model-overview">
        <div className="overview-orbit" aria-hidden="true">
          <span>✳</span>
          <span>⌘</span>
          <span>✦</span>
        </div>
        <div>
          <h2>One workspace. Many ways to think.</h2>
          <p>
            Keep your native accounts close. Bring in another model whenever the work calls for it.
          </p>
        </div>
        <div className="overview-count">
          <strong>{bootstrap.profiles.length}</strong>
          <span>connections</span>
        </div>
      </div>
      <div className="section-toolbar">
        <div className="segmented">
          {[{ id: 'all', short: 'All agents' }, ...AGENTS].map((a) => (
            <button
              key={a.id}
              className={agent === a.id ? 'active' : ''}
              onClick={() => setAgent(a.id)}
            >
              {a.short}
            </button>
          ))}
        </div>
        <span className="muted small-text">Profiles apply when a session starts</span>
      </div>
      <div className="connection-grid">
        {profiles.map((profile) => (
          <article key={profile.id} className="connection-card">
            <div className="connection-top">
              <AgentMark agent={profile.agent} />
              <span className={`pill ${profile.provider === 'native' ? 'neutral' : ''}`}>
                {profile.provider === 'native'
                  ? 'Native config'
                  : profile.provider === 'local-proxy'
                    ? 'Your proxy'
                    : profile.provider === 'openrouter'
                      ? 'OpenRouter'
                      : profile.provider === 'deepseek'
                        ? 'DeepSeek'
                        : 'Custom'}
              </span>
              <button
                className="icon-button"
                aria-label={`Edit ${profile.name}`}
                onClick={() => setEdit(profile)}
              >
                <Pencil size={15} />
              </button>
            </div>
            <h3>{profile.name}</h3>
            <p className="connection-description">
              {profile.provider === 'native'
                ? `${agentName(profile.agent)} with your existing configuration.`
                : profile.baseUrl}
            </p>
            <div className="connection-model">
              <CircleDot size={14} />
              <span>{profile.model || 'Automatic · native default'}</span>
              {profile.effort && <span className="subtle-pill">{profile.effort}</span>}
            </div>
            <div className="connection-security">
              {profile.provider === 'native' ? (
                <>
                  <ShieldCheck size={13} />
                  Uses the installed configuration
                </>
              ) : (
                <>
                  <KeyRound size={13} />
                  {profile.hasSecret
                    ? 'Credential saved'
                    : profile.apiKeyEnv
                      ? `From ${profile.apiKeyEnv}`
                      : 'No credential configured'}
                </>
              )}
            </div>
            {statuses[profile.id] && (
              <div className={`connection-result ${statuses[profile.id].ok ? 'good' : 'bad'}`}>
                <span>
                  {statuses[profile.id].ok ? <Check size={13} /> : <Radio size={13} />}
                  {statuses[profile.id].message}
                </span>
                <small>{statuses[profile.id].latencyMs} ms</small>
              </div>
            )}
            <div className="connection-actions">
              <button
                onClick={() => void test(profile)}
                disabled={!!testing}
                className="text-button"
              >
                <Radio size={14} />
                {testing === profile.id ? 'Checking…' : 'Test connection'}
              </button>
              {profile.provider !== 'native' && (
                <button onClick={() => setCatalog(profile)} className="text-button">
                  Models
                  <ArrowRight size={14} />
                </button>
              )}
              <button
                onClick={() => setRemove(profile)}
                className="icon-button delete-connection"
                aria-label={`Delete ${profile.name}`}
                title="Delete connection"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </article>
        ))}
        <button className="add-connection-card" onClick={() => setEdit('new')}>
          <span>
            <Plus size={22} />
          </span>
          <strong>Make room for another model</strong>
          <p>
            A local proxy, OpenRouter, DeepSeek,
            <br />
            or your own compatible endpoint.
          </p>
        </button>
      </div>
      <section className="proxy-panel">
        <div className="proxy-icon">
          <Server size={23} />
        </div>
        <div className="proxy-copy">
          <h3>Your proxy, within reach</h3>
          <p>
            {bootstrap.settings.proxyCommand
              ? 'Start the configured proxy executable and follow its output in a live terminal.'
              : 'Set a proxy executable in Settings to manage it from here.'}
          </p>
        </div>
        <div className="button-row">
          {proxy && (
            <button
              className="secondary-button compact"
              onClick={() =>
                void run(async () => {
                  const value = await desk.proxyMonitor(proxy.id);
                  setMonitor(value);
                  setMonitorOpen(true);
                })
              }
            >
              <Radio size={14} />
              Status
            </button>
          )}
          <button
            className="secondary-button compact"
            disabled={!bootstrap.settings.proxyCommand || starting}
            onClick={() => void startProxy()}
          >
            <Play size={14} />
            {starting ? 'Starting…' : 'Start proxy'}
          </button>
        </div>
      </section>
      <div className="proxy-auth-panel">
        <div>
          <strong>Connect an account to your proxy</strong>
          <p>Run the proxy’s own sign-in flow in a live terminal.</p>
        </div>
        <select
          aria-label="Proxy sign-in provider"
          value={authProvider}
          onChange={(e) => setAuthProvider(e.target.value as typeof authProvider)}
        >
          <option value="codex">Codex</option>
          <option value="kimi">Kimi</option>
          <option value="grok">Grok</option>
          <option value="cursor">Cursor</option>
        </select>
        <button
          className="secondary-button compact"
          onClick={() => void authenticate()}
          disabled={authenticating}
        >
          <KeyRound size={14} />
          {authenticating ? 'Opening…' : 'Sign in'}
        </button>
      </div>
      {edit && (
        <ProfileEditor
          profile={edit === 'new' ? undefined : edit}
          bootstrap={bootstrap}
          onClose={() => setEdit(undefined)}
        />
      )}
      {catalog && (
        <Catalog
          profile={catalog}
          onClose={() => setCatalog(undefined)}
          onChoose={(model) => {
            setEdit({ ...catalog, model });
            setCatalog(undefined);
          }}
        />
      )}
      {remove && (
        <Modal
          title="Remove this connection?"
          subtitle={remove.name}
          onClose={() => setRemove(undefined)}
        >
          <div className="modal-body">
            <p>
              The profile and its saved credential will be removed from Agent Desk. Existing running
              sessions continue with their current configuration.
            </p>
          </div>
          <footer className="modal-footer">
            <button className="secondary-button" onClick={() => setRemove(undefined)}>
              Keep connection
            </button>
            <button
              className="danger-button"
              onClick={() =>
                void run(async () => {
                  await desk.deleteProfile(remove.id);
                  await query.invalidateQueries({ queryKey: ['bootstrap'] });
                  setRemove(undefined);
                }, 'Connection removed')
              }
            >
              Remove connection
            </button>
          </footer>
        </Modal>
      )}
      {monitorOpen && (
        <Modal title="Proxy status" subtitle={proxy?.name} onClose={() => setMonitorOpen(false)}>
          <div className="modal-body">
            <pre className="code-preview">{JSON.stringify(monitor, null, 2)}</pre>
          </div>
        </Modal>
      )}
    </div>
  );
}
function Catalog({
  profile,
  onClose,
  onChoose,
}: {
  profile: ProviderProfile;
  onClose: () => void;
  onChoose: (id: string) => void;
}): ReactElement {
  const catalog = useCatalog(profile.id, true);
  const [search, setSearch] = useState('');
  const [free, setFree] = useState(false);
  const models =
    catalog.data?.models.filter(
      (m) =>
        (!free || m.free === true) &&
        `${m.name} ${m.id}`.toLowerCase().includes(search.toLowerCase()),
    ) ?? [];
  return (
    <Modal title="Explore available models" subtitle={profile.name} onClose={onClose} wide>
      <div className="modal-body">
        <div className="catalog-filters">
          <div className="search-input">
            <Search size={16} />
            <input
              aria-label="Search models"
              placeholder="Find a model…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <label className="check-field">
            <input type="checkbox" checked={free} onChange={(e) => setFree(e.target.checked)} />
            <span>Free only</span>
          </label>
        </div>
        {catalog.isPending ? (
          <Spinner label="Fetching the provider’s live catalog" />
        ) : catalog.isError ? (
          <ErrorBox error={catalog.error} retry={() => void catalog.refetch()} />
        ) : (
          <>
            <Warnings warnings={catalog.data.warnings} />
            <div className="catalog-list">
              {models.map((model) => (
                <button key={model.id} className="catalog-model" onClick={() => onChoose(model.id)}>
                  <div>
                    <strong>{model.name || model.id}</strong>
                    <code>{model.id}</code>
                  </div>
                  <span>{contextLabel(model.contextWindow)}</span>
                  {model.free && <span className="pill good">Free</span>}
                  <ArrowRight size={16} />
                </button>
              ))}
              {!models.length && (
                <EmptyState symbol="◇" title="No models match">
                  Try another search, or turn off the free filter.
                </EmptyState>
              )}
            </div>
            <p className="catalog-footer">
              {models.length} models · {catalog.data.source} · Checked{' '}
              {new Date(catalog.data.verifiedAt).toLocaleTimeString(undefined, {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </>
        )}
      </div>
    </Modal>
  );
}
