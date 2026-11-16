import { useState, type ReactElement } from 'react';
import { KeyRound, LockKeyhole, Save, ShieldCheck } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import type { Bootstrap, ProviderProfile, Route } from '../../shared/types';
import { desk, useSaveProfile } from '../api';
import { AGENTS } from '../utils';
import { ErrorBox, Field, Modal, useNotices } from '../ui';

export function ProfileEditor({
  profile,
  bootstrap,
  onClose,
}: {
  profile?: ProviderProfile;
  bootstrap: Bootstrap;
  onClose: () => void;
}): ReactElement {
  const [draft, setDraft] = useState<ProviderProfile>(
    profile
      ? structuredClone(profile)
      : {
          id: crypto.randomUUID(),
          name: '',
          agent: 'claude',
          provider: 'native',
          route: 'native',
          env: {},
        },
  );
  const [envText, setEnvText] = useState(JSON.stringify(draft.env, null, 2));
  const [secret, setSecret] = useState('');
  const [persist, setPersist] = useState(bootstrap.secureStorageAvailable);
  const [error, setError] = useState<unknown>();
  const [saving, setSaving] = useState(false);
  const save = useSaveProfile();
  const query = useQueryClient();
  const { notify, run } = useNotices();
  const patch = (values: Partial<ProviderProfile>): void =>
    setDraft((current) => ({ ...current, ...values }));
  const routeFor = (agent: ProviderProfile['agent']): Route =>
    agent === 'claude' ? 'anthropic' : agent === 'codex' ? 'openai-responses' : 'gemini';
  const chooseProvider = (provider: ProviderProfile['provider']): void => {
    const native = provider === 'native';
    patch({
      provider,
      route: native ? 'native' : routeFor(draft.agent),
      baseUrl: native
        ? undefined
        : provider === 'openrouter'
          ? draft.agent === 'claude'
            ? 'https://openrouter.ai/api'
            : 'https://openrouter.ai/api/v1'
          : provider === 'deepseek'
            ? 'https://api.deepseek.com/anthropic'
            : provider === 'local-proxy'
              ? 'http://127.0.0.1:18765'
              : '',
      apiKeyEnv: native
        ? undefined
        : provider === 'openrouter'
          ? 'OPENROUTER_API_KEY'
          : provider === 'deepseek'
            ? 'DEEPSEEK_API_KEY'
            : 'AGENT_DESK_API_KEY',
      authMode: 'bearer',
    });
  };
  const submit = async (): Promise<void> => {
    setError(undefined);
    setSaving(true);
    try {
      const env: unknown = JSON.parse(envText);
      if (
        !env ||
        typeof env !== 'object' ||
        Array.isArray(env) ||
        Object.values(env).some((v) => typeof v !== 'string')
      )
        throw new Error('Environment overrides must be a JSON object containing string values.');
      const saved = await save.mutateAsync({
        ...draft,
        name: draft.name.trim(),
        model: draft.model?.trim() || undefined,
        baseUrl: draft.baseUrl?.trim() || undefined,
        env: env as Record<string, string>,
      });
      if (secret) {
        try {
          await desk.saveSecret({ profileId: saved.id, secret, persist });
        } catch (cause) {
          throw new Error(
            `The profile was saved, but its API key was not: ${cause instanceof Error ? cause.message : String(cause)}`,
          );
        }
      }
      await query.invalidateQueries({ queryKey: ['bootstrap'] });
      notify(profile ? 'Connection profile updated' : 'Connection profile created');
      onClose();
    } catch (cause) {
      setError(cause);
    } finally {
      setSaving(false);
    }
  };
  return (
    <Modal
      title={profile ? 'Edit connection' : 'A new connection'}
      subtitle="Choose the agent. Give it the model you want to work with."
      onClose={() => {
        if (!saving) onClose();
      }}
      wide
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <div className="modal-body">
          <div className="form-grid">
            <Field label="Profile name">
              <input
                required
                maxLength={100}
                placeholder="e.g. Home proxy · fast coding"
                value={draft.name}
                onChange={(e) => patch({ name: e.target.value })}
              />
            </Field>
            <Field label="Coding agent">
              <select
                value={draft.agent}
                onChange={(e) => {
                  const agent = e.target.value as ProviderProfile['agent'];
                  patch({
                    agent,
                    provider: 'native',
                    route: 'native',
                    baseUrl: undefined,
                    apiKeyEnv: undefined,
                  });
                }}
              >
                {AGENTS.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Connect through">
              <select
                value={draft.provider}
                onChange={(e) => chooseProvider(e.target.value as ProviderProfile['provider'])}
              >
                <option value="native">Native configuration</option>
                <>
                  <option value="local-proxy">My proxy</option>
                  {!['gemini', 'antigravity'].includes(draft.agent) && (
                    <option value="openrouter">OpenRouter</option>
                  )}
                  {draft.agent === 'claude' && <option value="deepseek">DeepSeek</option>}
                  <option value="custom">Custom endpoint</option>
                </>
              </select>
            </Field>
            <Field label="Protocol" hint="The endpoint must speak the protocol this agent uses.">
              <input
                readOnly
                value={
                  draft.route === 'native'
                    ? 'Installed agent configuration'
                    : draft.route === 'anthropic'
                      ? 'Anthropic Messages'
                      : draft.route === 'openai-responses'
                        ? 'OpenAI Responses'
                        : 'Gemini API'
                }
              />
            </Field>
          </div>
          {draft.provider === 'native' ? (
            <div className="info-panel">
              <ShieldCheck size={20} />
              <div>
                <strong>Your existing setup, carried through.</strong>
                <p>
                  The agent uses its installed configuration, including sign-in, routing, and
                  settings. Leave model blank to follow its current default.
                </p>
              </div>
            </div>
          ) : (
            <div className="form-grid">
              <Field label="Endpoint URL" hint="Include the API prefix your provider expects.">
                <input
                  type="url"
                  required
                  placeholder="http://127.0.0.1:18765"
                  value={draft.baseUrl ?? ''}
                  onChange={(e) => patch({ baseUrl: e.target.value })}
                />
              </Field>
              <Field
                label="API key environment variable"
                hint="Use a key already available to your computer, or save one below."
              >
                <input
                  pattern="[A-Za-z_][A-Za-z0-9_]*"
                  value={draft.apiKeyEnv ?? ''}
                  onChange={(e) => patch({ apiKeyEnv: e.target.value || undefined })}
                />
              </Field>
            </div>
          )}
          <div className="form-grid">
            <Field
              label="Model ID"
              hint={
                draft.provider === 'native'
                  ? 'Optional. Blank uses the native default.'
                  : 'Use the exact model ID from your provider’s catalog.'
              }
            >
              <input
                placeholder={
                  draft.provider === 'native' ? 'Automatic · agent default' : 'provider/model-name'
                }
                value={draft.model ?? ''}
                onChange={(e) => patch({ model: e.target.value })}
              />
            </Field>
            <Field label="Reasoning effort" hint="Availability depends on your agent and model.">
              <input
                list="effort-options"
                placeholder="Agent default"
                value={draft.effort ?? ''}
                onChange={(e) => patch({ effort: e.target.value || undefined })}
              />
              <datalist id="effort-options">
                <option value="low" />
                <option value="medium" />
                <option value="high" />
                <option value="xhigh" />
                <option value="max" />
              </datalist>
            </Field>
            {draft.agent === 'claude' && (
              <Field
                label="Subagent model"
                hint="Optional model override for Claude’s delegated agents."
              >
                <input
                  value={draft.subagentModel ?? ''}
                  placeholder="Agent default"
                  onChange={(e) => patch({ subagentModel: e.target.value || undefined })}
                />
              </Field>
            )}
            {draft.agent === 'claude' && (
              <Field
                label="Small helper model"
                hint="Optional override for Claude’s small / Haiku helper tasks."
              >
                <input
                  value={draft.smallModel ?? ''}
                  placeholder="Agent default"
                  onChange={(e) => patch({ smallModel: e.target.value || undefined })}
                />
              </Field>
            )}
            <Field
              label="Context window"
              hint="Optional token limit. Applied to Claude; descriptive for other agents."
            >
              <input
                type="number"
                min={1024}
                step={1}
                value={draft.contextWindow ?? ''}
                placeholder="Provider default"
                onChange={(e) =>
                  patch({ contextWindow: e.target.value ? Number(e.target.value) : undefined })
                }
              />
            </Field>
          </div>
          {draft.provider !== 'native' && (
            <section className="credential-panel">
              <h3>
                <KeyRound size={16} />
                API credential{draft.hasSecret && <span className="pill good">Key saved</span>}
              </h3>
              <Field label={draft.hasSecret ? 'Replace saved key' : 'API key'}>
                <input
                  type="password"
                  autoComplete="off"
                  value={secret}
                  placeholder={
                    draft.hasSecret
                      ? 'Leave blank to keep the saved key'
                      : 'Optional if using an environment variable'
                  }
                  onChange={(e) => setSecret(e.target.value)}
                />
              </Field>
              <label className="check-field">
                <input
                  type="checkbox"
                  checked={persist}
                  disabled={!bootstrap.secureStorageAvailable}
                  onChange={(e) => setPersist(e.target.checked)}
                />
                <span>
                  <LockKeyhole size={13} />
                  Remember using this computer’s encrypted storage
                </span>
              </label>
              <p className="field-hint">
                {bootstrap.secureStorageAvailable
                  ? 'Turn this off to keep a new key only until Agent Desk closes.'
                  : 'Secure storage is unavailable here. New keys stay in memory for this app session only.'}
              </p>
              {draft.hasSecret && (
                <button
                  type="button"
                  className="text-button danger"
                  onClick={() =>
                    void run(async () => {
                      await desk.deleteSecret(draft.id);
                      patch({ hasSecret: false });
                      await query.invalidateQueries({ queryKey: ['bootstrap'] });
                    }, 'Saved credential removed')
                  }
                >
                  Remove saved credential
                </button>
              )}
            </section>
          )}
          <details className="advanced-section">
            <summary>Advanced environment & settings</summary>
            <Field
              label="Environment overrides"
              hint="JSON string values. Use the credential field for secrets."
            >
              <textarea
                className="code-editor short"
                spellCheck={false}
                value={envText}
                onChange={(e) => setEnvText(e.target.value)}
              />
            </Field>
            {draft.agent === 'claude' && (
              <Field
                label="Additional settings file"
                hint="Optional path passed to Claude Code for this profile."
              >
                <input
                  value={draft.settingsFile ?? ''}
                  onChange={(e) => patch({ settingsFile: e.target.value || undefined })}
                />
              </Field>
            )}
            <Field label="Authentication header">
              <select
                value={draft.authMode ?? 'bearer'}
                onChange={(e) => patch({ authMode: e.target.value as 'bearer' | 'api-key' })}
              >
                <option value="bearer">Bearer token</option>
                <option value="api-key">API key header</option>
              </select>
            </Field>
          </details>
          {error !== undefined && <ErrorBox error={error} />}
        </div>
        <footer className="modal-footer">
          <button className="secondary-button" type="button" disabled={saving} onClick={onClose}>
            Cancel
          </button>
          <button className="primary-button" type="submit" disabled={saving || !draft.name.trim()}>
            <Save size={15} />
            {saving ? 'Saving…' : 'Save connection'}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
