import { useEffect, useRef, useState, type ReactElement } from 'react';
import { Check, FolderOpen, Monitor, Moon, Plus, Save, Sun, Terminal, Trash2 } from 'lucide-react';
import type { AppSettings, Bootstrap } from '../../shared/types';
import { desk, useSaveSettings } from '../api';
import { useUnsavedChanges } from '../unsaved';
import { AGENTS, agentName } from '../utils';
import { AgentMark, ErrorBox, Field, useNotices } from '../ui';
import { NativeConfigs } from './NativeConfigs';

type Tab = 'appearance' | 'agents' | 'sources' | 'native';
export function Settings({ bootstrap }: { bootstrap: Bootstrap }): ReactElement {
  const [tab, setTab] = useState<Tab>('appearance');
  const [draft, setDraft] = useState<AppSettings>(() => structuredClone(bootstrap.settings));
  const [saved, setSaved] = useState(JSON.stringify(bootstrap.settings));
  const [error, setError] = useState<unknown>();
  const save = useSaveSettings();
  const { run, notify } = useNotices();
  const dirty = JSON.stringify(draft) !== saved;
  useUnsavedChanges('app-settings', dirty);
  const latestServerSettings = useRef(JSON.stringify(bootstrap.settings));
  useEffect(() => {
    const next = JSON.stringify(bootstrap.settings);
    if (next === latestServerSettings.current) return;
    latestServerSettings.current = next;
    if (!dirty) {
      setDraft(structuredClone(bootstrap.settings));
      setSaved(next);
    }
  }, [bootstrap.settings, dirty]);
  const patch = (value: Partial<AppSettings>): void =>
    setDraft((current) => ({ ...current, ...value }));
  const persist = async (): Promise<void> => {
    setError(undefined);
    try {
      const result = await save.mutateAsync(draft);
      setDraft(result);
      setSaved(JSON.stringify(result));
      notify('Settings saved');
    } catch (cause) {
      setError(cause);
    }
  };
  const pick = async (apply: (path: string) => void): Promise<void> => {
    await run(async () => {
      const path = await desk.pickDirectory();
      if (path) apply(path);
    });
  };
  return (
    <div className="standard-page settings-page">
      <header className="page-heading">
        <div>
          <div className="eyebrow">MAKE YOURSELF AT HOME</div>
          <h1>Settings</h1>
          <p>A workspace that works the way you do.</p>
        </div>
        {tab !== 'native' && (
          <button
            className="primary-button"
            disabled={!dirty || save.isPending}
            onClick={() => void persist()}
          >
            <Save size={15} />
            {save.isPending ? 'Saving…' : 'Save changes'}
          </button>
        )}
      </header>
      <div className="settings-tabs" role="tablist" aria-label="Settings sections">
        {[
          { id: 'appearance', label: 'Appearance' },
          { id: 'agents', label: 'Agents & defaults' },
          { id: 'sources', label: 'Folders & history' },
          { id: 'native', label: 'Native configuration' },
        ].map((item) => (
          <button
            role="tab"
            aria-selected={tab === item.id}
            className={tab === item.id ? 'active' : ''}
            key={item.id}
            onClick={() => setTab(item.id as Tab)}
          >
            {item.label}
          </button>
        ))}
      </div>
      {error !== undefined && <ErrorBox error={error} />}
      {tab === 'appearance' && (
        <div className="settings-content">
          <SettingsSection
            title="A comfortable place to work"
            description="Choose a palette that feels right for your day."
          >
            <div className="theme-options">
              {[
                { value: 'light', label: 'Light', icon: Sun },
                { value: 'dark', label: 'Dark', icon: Moon },
                { value: 'system', label: 'System', icon: Monitor },
              ].map((theme) => (
                <button
                  className={`theme-option ${draft.theme === theme.value ? 'selected' : ''}`}
                  key={theme.value}
                  onClick={() => patch({ theme: theme.value as AppSettings['theme'] })}
                  aria-pressed={draft.theme === theme.value}
                >
                  <div className={`theme-miniature theme-miniature-${theme.value}`}>
                    <div />
                    <div>
                      <i />
                      <i />
                      <i />
                      <span />
                    </div>
                  </div>
                  <span>
                    <theme.icon size={15} />
                    {theme.label}
                    {draft.theme === theme.value && <Check size={14} />}
                  </span>
                </button>
              ))}
            </div>
            <div className="form-grid">
              <Field label="Terminal font size">
                <div className="range-field">
                  <input
                    type="range"
                    min={10}
                    max={24}
                    value={draft.fontSize}
                    onChange={(e) => patch({ fontSize: Number(e.target.value) })}
                  />
                  <span>{draft.fontSize}px</span>
                </div>
              </Field>
              <Field label="Terminal scrollback" hint="Lines kept in each live terminal.">
                <input
                  type="number"
                  min={1000}
                  max={100000}
                  step={1000}
                  value={draft.terminalScrollback}
                  onChange={(e) => patch({ terminalScrollback: Number(e.target.value) })}
                />
              </Field>
            </div>
            <div className="terminal-sample" style={{ fontSize: draft.fontSize }}>
              <span>❯</span> A little room for your next idea.
              <span className="sample-cursor" />
            </div>
          </SettingsSection>
          <SettingsSection
            title="Stay up to date"
            description="Control when Agent Desk reads your local session history."
          >
            <label className="toggle-row">
              <div>
                <strong>Scan history on startup</strong>
                <p>Find conversations from your installed agents when the app opens.</p>
              </div>
              <input
                type="checkbox"
                checked={draft.scanOnStart}
                onChange={(e) => patch({ scanOnStart: e.target.checked })}
              />
            </label>
            <Field
              label="Refresh session history"
              hint="Use at least 10 seconds, or 0 for manual refresh only."
            >
              <div className="input-unit">
                <input
                  type="number"
                  min={0}
                  max={3600}
                  value={draft.autoRefreshSeconds}
                  onChange={(e) => patch({ autoRefreshSeconds: Number(e.target.value) })}
                />
                <span>seconds</span>
              </div>
            </Field>
          </SettingsSection>
          <div className="settings-about">
            <div className="brand-mark">✳</div>
            <div>
              <strong>Agent Desk</strong>
              <span>
                Version {bootstrap.appVersion} · {bootstrap.platform}
              </span>
            </div>
            <p>One place for the way you work.</p>
          </div>
        </div>
      )}
      {tab === 'agents' && (
        <div className="settings-content">
          <SettingsSection
            title="Your installed agents"
            description="Use the executable name on your PATH, or the full path to its executable."
          >
            <div className="agent-settings-list">
              {AGENTS.map((agent) => {
                const install = bootstrap.agents.find((a) => a.id === agent.id);
                return (
                  <div className="agent-setting" key={agent.id}>
                    <AgentMark agent={agent.id} />
                    <div>
                      <strong>{agent.label}</strong>
                      <span className={install?.available ? 'good-text' : 'muted'}>
                        {install?.available ? install.version || 'Available' : 'Not detected'}
                      </span>
                    </div>
                    <input
                      aria-label={`${agent.label} executable`}
                      value={draft.agentCommands[agent.id]}
                      onChange={(e) =>
                        patch({
                          agentCommands: { ...draft.agentCommands, [agent.id]: e.target.value },
                        })
                      }
                    />
                  </div>
                );
              })}
            </div>
            <p className="field-hint">
              Installed agents keep their own authentication and permissions. Antigravity uses its
              agy CLI.
            </p>
          </SettingsSection>
          <SettingsSection
            title="A familiar starting point"
            description="Choose the connection used by default for new sessions."
          >
            <Field label="Default connection">
              <select
                value={draft.defaultProfileId}
                onChange={(e) => patch({ defaultProfileId: e.target.value })}
              >
                {bootstrap.profiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name}
                  </option>
                ))}
              </select>
            </Field>
          </SettingsSection>
          <SettingsSection
            title="Proxy executable"
            description="Run your existing proxy from Agent Desk and keep its output in a terminal."
          >
            <Field
              label="Executable"
              hint="Use an executable name on your PATH or an absolute executable path. Agent Desk supplies the serve and authentication arguments."
            >
              <input
                placeholder="e.g. claude-code-proxy"
                value={draft.proxyCommand}
                onChange={(e) => patch({ proxyCommand: e.target.value })}
              />
            </Field>
          </SettingsSection>
        </div>
      )}
      {tab === 'sources' && (
        <div className="settings-content">
          <SettingsSection
            title="Projects"
            description="Keep frequently used workspaces close at hand."
          >
            <PathList
              paths={draft.projects}
              onChange={(projects) => patch({ projects })}
              onBrowse={() =>
                void pick((path) => patch({ projects: [...new Set([...draft.projects, path])] }))
              }
              label="Project"
            />
          </SettingsSection>
          <SettingsSection
            title="Additional session folders"
            description="The standard agent locations are discovered automatically. Add other local or mounted folders here."
          >
            <div className="history-roots">
              {draft.historyRoots.map((root, index) => (
                <div className="path-row" key={root.id}>
                  <select
                    aria-label="History source agent"
                    value={root.agent}
                    onChange={(e) =>
                      patch({
                        historyRoots: draft.historyRoots.map((r, i) =>
                          i === index ? { ...r, agent: e.target.value as typeof r.agent } : r,
                        ),
                      })
                    }
                  >
                    {AGENTS.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.label}
                      </option>
                    ))}
                  </select>
                  <input
                    aria-label="History root path"
                    value={root.path}
                    placeholder="/path/to/history"
                    onChange={(e) =>
                      patch({
                        historyRoots: draft.historyRoots.map((r, i) =>
                          i === index ? { ...r, path: e.target.value } : r,
                        ),
                      })
                    }
                  />
                  <button
                    className="icon-button"
                    aria-label="Browse for history folder"
                    onClick={() =>
                      void pick((path) =>
                        patch({
                          historyRoots: draft.historyRoots.map((r, i) =>
                            i === index ? { ...r, path } : r,
                          ),
                        }),
                      )
                    }
                  >
                    <FolderOpen size={16} />
                  </button>
                  <button
                    className="icon-button"
                    aria-label="Remove history folder"
                    onClick={() =>
                      patch({ historyRoots: draft.historyRoots.filter((_, i) => i !== index) })
                    }
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
            </div>
            <button
              className="secondary-button compact"
              onClick={() =>
                patch({
                  historyRoots: [
                    ...draft.historyRoots,
                    { id: crypto.randomUUID(), agent: 'claude', path: '' },
                  ],
                })
              }
            >
              <Plus size={15} />
              Add history folder
            </button>
          </SettingsSection>
          <SettingsSection
            title="Additional skill folders"
            description="Folders containing your own skill directories. Existing agent skill locations are discovered automatically."
          >
            <PathList
              paths={draft.skillDirectories}
              onChange={(skillDirectories) => patch({ skillDirectories })}
              onBrowse={() =>
                void pick((path) =>
                  patch({ skillDirectories: [...new Set([...draft.skillDirectories, path])] }),
                )
              }
              label="Skill directory"
            />
          </SettingsSection>
        </div>
      )}
      {tab === 'native' && <NativeConfigs />}
      {dirty && tab !== 'native' && (
        <div className="settings-savebar">
          <span>
            <span className="unsaved-indicator" />
            You have unsaved changes
          </span>
          <button
            className="text-button"
            onClick={() => {
              setDraft(JSON.parse(saved) as AppSettings);
              setError(undefined);
            }}
          >
            Discard
          </button>
          <button
            className="primary-button compact"
            onClick={() => void persist()}
            disabled={save.isPending}
          >
            Save changes
            <Check size={14} />
          </button>
        </div>
      )}
    </div>
  );
}
function SettingsSection({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}): ReactElement {
  return (
    <section className="settings-section">
      <header>
        <h2>{title}</h2>
        <p>{description}</p>
      </header>
      <div>{children}</div>
    </section>
  );
}
function PathList({
  paths,
  onChange,
  onBrowse,
  label,
}: {
  paths: string[];
  onChange: (paths: string[]) => void;
  onBrowse: () => void;
  label: string;
}): ReactElement {
  return (
    <>
      <div className="path-list">
        {paths.map((path, i) => (
          <div className="path-row" key={i}>
            <FolderOpen size={16} />
            <input
              aria-label={`${label} ${i + 1}`}
              value={path}
              onChange={(e) =>
                onChange(paths.map((p, index) => (index === i ? e.target.value : p)))
              }
            />
            <button
              className="icon-button"
              aria-label={`Remove ${label.toLowerCase()} ${i + 1}`}
              onClick={() => onChange(paths.filter((_, index) => index !== i))}
            >
              <Trash2 size={15} />
            </button>
          </div>
        ))}
      </div>
      <div className="button-row">
        <button className="secondary-button compact" onClick={onBrowse}>
          <FolderOpen size={14} />
          Browse
        </button>
        <button className="text-button" onClick={() => onChange([...paths, ''])}>
          <Plus size={14} />
          Enter path
        </button>
      </div>
    </>
  );
}
