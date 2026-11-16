import { useState, type ReactElement } from 'react';
import { FolderOpen, RefreshCw, Save, ShieldCheck } from 'lucide-react';
import { parse as parseToml } from 'smol-toml';
import { useQueryClient } from '@tanstack/react-query';
import type { ConfigDocument } from '../../shared/types';
import { useUnsavedChanges } from '../unsaved';
import { desk, useConfigs } from '../api';
import { ClaudeQuickSettings } from './ClaudeQuickSettings';
import { AgentMark, EmptyState, ErrorBox, Spinner, useNotices } from '../ui';

export function NativeConfigs(): ReactElement {
  const configs = useConfigs();
  const [selected, setSelected] = useState<string>();
  if (configs.isPending) return <Spinner label="Reading native configuration files" />;
  if (configs.isError)
    return <ErrorBox error={configs.error} retry={() => void configs.refetch()} />;
  const current = configs.data.find((c) => c.id === selected) ?? configs.data[0];
  return (
    <div className="native-configs">
      <div className="info-panel">
        <ShieldCheck size={20} />
        <div>
          <strong>Your native configuration.</strong>
          <p>
            Edit discovered agent settings and instruction files, including status line, hooks, and
            supported MCP settings. Agent Desk validates the format and creates a backup. Account
            credentials and settings stored outside these files remain with each agent.
          </p>
        </div>
      </div>
      <div className="config-workbench">
        <aside className="config-list">
          {configs.data.map((config) => (
            <button
              className={current?.id === config.id ? 'selected' : ''}
              key={config.id}
              onClick={() => setSelected(config.id)}
            >
              <AgentMark agent={config.agent} small />
              <div>
                <strong>{config.label}</strong>
                <span>{config.exists ? config.format.toUpperCase() : 'Not created yet'}</span>
              </div>
            </button>
          ))}
        </aside>
        {current ? (
          <ConfigEditor key={current.id} document={current} />
        ) : (
          <EmptyState title="No configuration files found">
            Install and sign in to a coding agent, then refresh this view.
          </EmptyState>
        )}
      </div>
    </div>
  );
}
const drafts = new Map<string, { content: string; revision: string; original: string }>();
function ConfigEditor({ document }: { document: ConfigDocument }): ReactElement {
  const existing = drafts.get(document.id);
  const [content, setContent] = useState(existing?.content ?? document.content);
  const [revision, setRevision] = useState(existing?.revision ?? document.revision);
  const [original, setOriginal] = useState(existing?.original ?? document.content);
  const [error, setError] = useState<unknown>();
  const [saving, setSaving] = useState(false);
  const { run, notify } = useNotices();
  const query = useQueryClient();
  const dirty = content !== original;
  useUnsavedChanges(`config:${document.id}`, dirty, true);
  const update = (value: string): void => {
    setContent(value);
    drafts.set(document.id, { content: value, revision, original });
  };
  const reload = async (): Promise<void> => {
    setSaving(true);
    await run(async () => {
      const documents = await desk.configs();
      const latest = documents.find((item) => item.id === document.id);
      if (!latest) throw new Error('This configuration file is no longer available.');
      setContent(latest.content);
      setOriginal(latest.content);
      setRevision(latest.revision);
      setError(undefined);
      drafts.delete(document.id);
      query.setQueryData(['configs'], documents);
    }, 'Configuration reloaded from disk');
    setSaving(false);
  };
  const save = async (): Promise<void> => {
    setError(undefined);
    setSaving(true);
    try {
      if (document.format === 'json') JSON.parse(content);
      if (document.format === 'toml') parseToml(content);
      const result = await desk.saveConfig({ id: document.id, content, revision });
      setRevision(result.revision);
      setOriginal(result.content);
      setContent(result.content);
      drafts.delete(document.id);
      await query.invalidateQueries({ queryKey: ['configs'] });
      notify('Native configuration saved with a backup. New agent sessions will use it.');
    } catch (cause) {
      setError(cause);
    } finally {
      setSaving(false);
    }
  };
  return (
    <section className="config-editor">
      <header>
        <div>
          <h3>{document.label}</h3>
          <code>{document.path}</code>
        </div>
        <button
          className="icon-button"
          aria-label="Show configuration file"
          onClick={() => void run(() => desk.revealPath(document.path))}
        >
          <FolderOpen size={16} />
        </button>
      </header>
      {document.agent === 'claude' &&
        document.format === 'json' &&
        /settings(?:\.local)?\.json$/.test(document.path) && (
          <ClaudeQuickSettings content={content} onChange={update} />
        )}
      <textarea
        aria-label={`${document.label} source`}
        className="code-editor"
        spellCheck={false}
        value={content}
        onChange={(e) => update(e.target.value)}
        placeholder={document.format === 'json' ? '{\n\n}' : ''}
      />
      {error !== undefined && <ErrorBox error={error} />}
      <footer>
        <span>
          {dirty ? 'Unsaved changes' : 'Saved'} · {document.format.toUpperCase()}
        </span>
        <div className="button-row">
          <button className="text-button" disabled={saving} onClick={() => void reload()}>
            <RefreshCw size={12} />
            {dirty ? 'Discard & reload' : 'Reload'}
          </button>
          <button
            className="text-button"
            disabled={!dirty || saving}
            onClick={() => {
              setContent(original);
              drafts.delete(document.id);
              setError(undefined);
            }}
          >
            Discard
          </button>
          <button
            className="primary-button compact"
            disabled={!dirty || saving}
            onClick={() => void save()}
          >
            <Save size={14} />
            {saving ? 'Saving…' : 'Save file'}
          </button>
        </div>
      </footer>
    </section>
  );
}
