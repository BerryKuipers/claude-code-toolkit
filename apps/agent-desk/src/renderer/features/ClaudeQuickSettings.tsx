import { useMemo, type ReactElement } from 'react';
import { Puzzle, SlidersHorizontal } from 'lucide-react';
import { Field } from '../ui';

type ConfigObject = Record<string, unknown>;
function object(value: unknown): ConfigObject | undefined {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as ConfigObject)
    : undefined;
}
function string(value: unknown): string {
  return typeof value === 'string' ? value : '';
}
export function ClaudeQuickSettings({
  content,
  onChange,
}: {
  content: string;
  onChange: (value: string) => void;
}): ReactElement {
  const parsed = useMemo(() => {
    try {
      const config = object(JSON.parse(content.trim() || '{}'));
      return config
        ? { config, error: undefined }
        : { config: undefined, error: 'Quick settings require a JSON object.' };
    } catch {
      return {
        config: undefined,
        error: 'Fix the JSON in the source editor to use quick settings.',
      };
    }
  }, [content]);
  const config = parsed.config;
  const patch = (key: string, value: unknown): void => {
    if (!config) return;
    const updated = { ...config };
    if (value === undefined) delete updated[key];
    else updated[key] = value;
    onChange(`${JSON.stringify(updated, null, 2)}\n`);
  };
  const statusLine = object(config?.statusLine);
  const plugins = object(config?.enabledPlugins);
  return (
    <details className="claude-quick-settings" open>
      <summary>
        <SlidersHorizontal size={14} />
        Claude quick settings<span>Changes are saved with the file</span>
      </summary>
      {parsed.error ? (
        <p className="inline-note">{parsed.error}</p>
      ) : (
        <>
          <div className="form-grid">
            <Field label="Default model" hint="Blank follows the agent default.">
              <input
                value={string(config?.model)}
                placeholder="Agent default"
                onChange={(e) => patch('model', e.target.value || undefined)}
              />
            </Field>
            <Field label="Reasoning effort">
              <input
                value={string(config?.effortLevel)}
                placeholder="Agent default"
                list="native-effort-options"
                onChange={(e) => patch('effortLevel', e.target.value || undefined)}
              />
              <datalist id="native-effort-options">
                <option value="low" />
                <option value="medium" />
                <option value="high" />
                <option value="max" />
              </datalist>
            </Field>
            <Field label="Output style">
              <input
                value={string(config?.outputStyle)}
                placeholder="Default"
                list="output-style-options"
                onChange={(e) => patch('outputStyle', e.target.value || undefined)}
              />
              <datalist id="output-style-options">
                <option value="Default" />
                <option value="Explanatory" />
                <option value="Learning" />
              </datalist>
            </Field>
            <Field
              label="Status line command"
              hint="The existing status line object and other fields are preserved."
            >
              <input
                value={string(statusLine?.command)}
                placeholder="e.g. node ~/.claude/statusline.js"
                onChange={(e) =>
                  patch('statusLine', {
                    ...statusLine,
                    type: statusLine?.type ?? 'command',
                    command: e.target.value,
                  })
                }
              />
            </Field>
          </div>
          {plugins && Object.keys(plugins).length > 0 && (
            <div className="plugin-switches">
              <h4>
                <Puzzle size={14} />
                Installed plugin switches
              </h4>
              {Object.entries(plugins).map(([name, enabled]) =>
                typeof enabled === 'boolean' ? (
                  <label className="check-field" key={name}>
                    <input
                      type="checkbox"
                      checked={enabled}
                      onChange={(e) =>
                        patch('enabledPlugins', { ...plugins, [name]: e.target.checked })
                      }
                    />
                    <span>{name}</span>
                  </label>
                ) : (
                  <p key={name} className="field-hint">
                    {name}: custom value — use the source editor.
                  </p>
                ),
              )}
            </div>
          )}
        </>
      )}
      <p className="quick-settings-note">
        Other settings stay intact. Edit the source below for hooks, MCP configuration, and
        additional options supported by this file.
      </p>
    </details>
  );
}
