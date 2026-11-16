import { useState, type ReactElement } from 'react';
import { ArrowUpRight, FolderOpen, LoaderCircle } from 'lucide-react';
import type { AgentId, Bootstrap, LaunchRequest } from '../../shared/types';
import { desk } from '../api';
import { AGENTS } from '../utils';
import { AgentMark, Field, Modal, useNotices } from '../ui';

export function NewSession({
  bootstrap,
  initialProject,
  onClose,
  onLaunch,
}: {
  bootstrap: Bootstrap;
  initialProject?: string;
  onClose: () => void;
  onLaunch: (request: LaunchRequest) => Promise<boolean>;
}): ReactElement {
  const defaultProfile =
    bootstrap.profiles.find((p) => p.id === bootstrap.settings.defaultProfileId) ??
    bootstrap.profiles[0];
  const [agent, setAgent] = useState<AgentId>(defaultProfile?.agent ?? 'claude');
  const [profile, setProfile] = useState(defaultProfile?.id ?? '');
  const [project, setProject] = useState(
    initialProject && initialProject !== 'all'
      ? initialProject
      : (bootstrap.settings.projects[0] ?? ''),
  );
  const [prompt, setPrompt] = useState('');
  const [busy, setBusy] = useState(false);
  const { run } = useNotices();
  const profiles = bootstrap.profiles.filter((p) => p.agent === agent);
  const installation = bootstrap.agents.find((a) => a.id === agent);
  const chooseAgent = (id: AgentId): void => {
    setAgent(id);
    setProfile(
      bootstrap.profiles.find((p) => p.agent === id && p.id === bootstrap.settings.defaultProfileId)
        ?.id ??
        bootstrap.profiles.find((p) => p.agent === id)?.id ??
        '',
    );
  };
  const submit = async (): Promise<void> => {
    setBusy(true);
    try {
      const success = await onLaunch({
        agent,
        projectPath: project.trim(),
        profileId: profile || undefined,
        prompt: prompt.trim() || undefined,
      });
      if (success) onClose();
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal
      title="What are you working on?"
      subtitle="A new session. A little room to think."
      onClose={() => {
        if (!busy) onClose();
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
          <div className="agent-choices">
            {AGENTS.map((item) => (
              <button
                type="button"
                key={item.id}
                className={agent === item.id ? 'selected' : ''}
                onClick={() => chooseAgent(item.id)}
                aria-pressed={agent === item.id}
              >
                <AgentMark agent={item.id} />
                <span>{item.short}</span>
              </button>
            ))}
          </div>
          {!installation?.available && (
            <div className="inline-note">
              {AGENTS.find((a) => a.id === agent)?.label} was not detected. Set its executable path
              in Settings if it is installed elsewhere.
            </div>
          )}
          <Field label="Project folder">
            <div className="browse-input">
              <input
                required
                value={project}
                onChange={(e) => setProject(e.target.value)}
                placeholder="Choose a project folder"
                list="project-suggestions"
              />
              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  void run(async () => {
                    const path = await desk.pickDirectory();
                    if (path) setProject(path);
                  })
                }
              >
                <FolderOpen size={16} />
                Browse
              </button>
            </div>
            <datalist id="project-suggestions">
              {bootstrap.settings.projects.map((path) => (
                <option key={path} value={path} />
              ))}
            </datalist>
          </Field>
          <Field label="Connection profile">
            <select value={profile} onChange={(e) => setProfile(e.target.value)}>
              {!profiles.length && <option value="">Native agent settings</option>}
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                  {p.model ? ` · ${p.model}` : ''}
                </option>
              ))}
            </select>
          </Field>
          {agent === 'antigravity' && (
            <div className="inline-note">
              Starts the Antigravity CLI (<code>agy</code>) in this workspace. Imported IDE
              conversations may need the CLI’s own import flow before resuming.
            </div>
          )}
          <Field
            label="First thought"
            hint="Optional. Leave blank to start an interactive session."
          >
            <textarea
              rows={5}
              placeholder="Describe what you’d like to build, explore, or fix…"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </Field>
        </div>
        <footer className="modal-footer">
          <span className="muted small-text">Your agent’s own tools and permissions.</span>
          <button className="primary-button" type="submit" disabled={busy || !project.trim()}>
            {busy ? <LoaderCircle size={16} className="spin" /> : <ArrowUpRight size={16} />}
            {busy ? 'Starting…' : 'Start session'}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
