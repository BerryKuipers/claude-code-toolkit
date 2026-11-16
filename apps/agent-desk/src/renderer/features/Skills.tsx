import { useEffect, useState, type ReactElement } from 'react';
import {
  BookOpen,
  Code2,
  Eye,
  FolderOpen,
  Link2,
  Plus,
  RefreshCw,
  Save,
  Search,
  Sparkles,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useQueryClient } from '@tanstack/react-query';
import type { Bootstrap, LaunchRequest, SkillDocument, SkillRoot } from '../../shared/types';
import { desk, useSkill, useSkills } from '../api';
import { useUnsavedChanges } from '../unsaved';
import { AGENTS, agentName } from '../utils';
import {
  AgentMark,
  EmptyState,
  ErrorBox,
  Field,
  Modal,
  Spinner,
  useNotices,
  Warnings,
} from '../ui';

export function Skills({
  bootstrap,
  onLaunch,
}: {
  bootstrap: Bootstrap;
  onLaunch: (request: LaunchRequest) => Promise<boolean>;
}): ReactElement {
  const skills = useSkills();
  const query = useQueryClient();
  const { run } = useNotices();
  const [selected, setSelected] = useState<string>();
  const [search, setSearch] = useState('');
  const [source, setSource] = useState('all');
  const [creating, setCreating] = useState(false);
  const records = skills.data?.skills ?? [];
  const filtered = records.filter(
    (s) =>
      (source === 'all' || s.agent === source || s.scope === source) &&
      `${s.name} ${s.description} ${s.path}`.toLowerCase().includes(search.toLowerCase()),
  );
  const current = filtered.find((s) => s.id === selected) ?? filtered[0];
  return (
    <div className="skills-page">
      <header className="page-heading">
        <div>
          <div className="eyebrow">A LITTLE KNOW-HOW GOES A LONG WAY</div>
          <h1>
            Skills<span className="heading-count">{records.length}</span>
          </h1>
          <p>The instructions that make your agents feel like yours.</p>
        </div>
        <div className="button-row">
          <button
            className="secondary-button compact"
            onClick={() =>
              void run(async () => {
                await skills.refetch({ throwOnError: true });
                await query.invalidateQueries({ queryKey: ['skill'] });
              })
            }
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          <button className="primary-button" onClick={() => setCreating(true)}>
            <Plus size={16} />
            Create skill
          </button>
        </div>
      </header>
      <div className="skills-workbench">
        <section className="skill-library">
          <div className="library-controls">
            <div className="search-input">
              <Search size={16} />
              <input
                aria-label="Search skills"
                placeholder="Find a skill…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <select
              aria-label="Filter skills by source"
              value={source}
              onChange={(e) => setSource(e.target.value)}
            >
              <option value="all">All sources</option>
              {AGENTS.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.label}
                </option>
              ))}
              <option value="shared">Shared</option>
              <option value="plugin">Plugins</option>
              <option value="project">Project skills</option>
            </select>
          </div>
          {skills.isPending ? (
            <Spinner label="Discovering skills" />
          ) : skills.isError ? (
            <ErrorBox error={skills.error} retry={() => void skills.refetch()} />
          ) : (
            <div className="skill-list">
              {filtered.map((skill) => (
                <button
                  key={skill.id}
                  className={`skill-card ${current?.id === skill.id ? 'selected' : ''}`}
                  onClick={() => setSelected(skill.id)}
                  aria-pressed={current?.id === skill.id}
                >
                  <div className="skill-card-title">
                    <BookOpen size={17} />
                    <strong>{skill.name}</strong>
                    {skill.linked && <Link2 size={13} />}
                  </div>
                  <p>{skill.description || 'No description in this skill.'}</p>
                  <div className="skill-card-meta">
                    <AgentMark agent={skill.agent} small />
                    <span>{agentName(skill.agent)}</span>
                    <span className="subtle-pill">{skill.disabled ? 'Disabled' : skill.scope}</span>
                  </div>
                </button>
              ))}
              {!filtered.length && (
                <div className="list-empty">
                  <BookOpen size={24} />
                  <strong>
                    {records.length ? 'No matching skills' : 'Your toolkit starts here'}
                  </strong>
                  <p>
                    {records.length
                      ? 'Try a different name or source.'
                      : 'Create a skill or add a skill directory in Settings.'}
                  </p>
                </div>
              )}
            </div>
          )}
        </section>
        {current ? (
          <SkillDetail key={current.id} id={current.id} bootstrap={bootstrap} onLaunch={onLaunch} />
        ) : (
          <EmptyState
            symbol="◇"
            title="Good instructions travel well."
            action={
              <button className="primary-button" onClick={() => setCreating(true)}>
                <Plus size={16} />
                Create a skill
              </button>
            }
          >
            See, refine, and organize the skills your agents already know.
          </EmptyState>
        )}
      </div>
      <Warnings warnings={skills.data?.warnings} />
      {creating && (
        <CreateSkill
          roots={skills.data?.roots ?? bootstrap.skillRoots}
          onClose={() => setCreating(false)}
          onCreated={(id) => {
            setSelected(id);
            setCreating(false);
          }}
        />
      )}
    </div>
  );
}
function SkillDetail({
  id,
  bootstrap,
  onLaunch,
}: {
  id: string;
  bootstrap: Bootstrap;
  onLaunch: (request: LaunchRequest) => Promise<boolean>;
}): ReactElement {
  const document = useSkill(id);
  if (document.isPending) return <Spinner label="Opening skill" />;
  if (document.isError)
    return <ErrorBox error={document.error} retry={() => void document.refetch()} />;
  if (!document.data) return <ErrorBox error="The skill could not be found." />;
  return <SkillEditor document={document.data} bootstrap={bootstrap} onLaunch={onLaunch} />;
}
const skillDrafts = new Map<string, { content: string; revision: string; savedContent: string }>();
function SkillEditor({
  document,
  bootstrap,
  onLaunch,
}: {
  document: SkillDocument;
  bootstrap: Bootstrap;
  onLaunch: (request: LaunchRequest) => Promise<boolean>;
}): ReactElement {
  const draft = skillDrafts.get(document.skill.id);
  const [content, setContent] = useState(draft?.content ?? document.content);
  const [revision, setRevision] = useState(draft?.revision ?? document.revision);
  const [savedContent, setSavedContent] = useState(draft?.savedContent ?? document.content);
  const [mode, setMode] = useState<'preview' | 'edit'>('preview');
  const [saving, setSaving] = useState(false);
  const [improve, setImprove] = useState(false);
  const query = useQueryClient();
  const { run, notify } = useNotices();
  const skill = document.skill;
  const dirty = content !== savedContent;
  useUnsavedChanges(`skill:${skill.id}`, dirty, true);
  useEffect(() => {
    if (document.revision !== revision && !dirty) {
      setContent(document.content);
      setSavedContent(document.content);
      setRevision(document.revision);
    }
  }, [document.content, document.revision, revision, dirty]);
  const reload = async (): Promise<void> => {
    setSaving(true);
    await run(async () => {
      const latest = await desk.readSkill(skill.id);
      setContent(latest.content);
      setSavedContent(latest.content);
      setRevision(latest.revision);
      skillDrafts.delete(skill.id);
      query.setQueryData(['skill', skill.id], latest);
    }, 'Skill reloaded from disk');
    setSaving(false);
  };
  const save = async (): Promise<void> => {
    setSaving(true);
    await run(async () => {
      const result = await desk.saveSkill({ id: skill.id, content, revision });
      setRevision(result.revision);
      setSavedContent(result.content);
      setContent(result.content);
      skillDrafts.delete(skill.id);
      query.setQueryData(['skill', skill.id], result);
      await query.invalidateQueries({ queryKey: ['skills'] });
      notify('Skill saved. A backup of the previous version is available.');
    });
    setSaving(false);
  };

  return (
    <section className="skill-detail">
      <header className="skill-detail-header">
        <div className="eyebrow">{skill.scope.toUpperCase()} SKILL</div>
        <h2>{skill.name}</h2>
        <p>{skill.description}</p>
        <div className="skill-path">
          <code>{skill.path}</code>
          <button
            className={dirty ? 'text-button' : 'icon-button'}
            disabled={saving}
            aria-label={
              dirty ? 'Discard unsaved changes and reload skill' : 'Reload skill from disk'
            }
            onClick={() => void reload()}
          >
            <RefreshCw size={14} />
            {dirty && 'Discard & reload'}
          </button>
          <button
            className="icon-button"
            aria-label="Show skill file"
            onClick={() => void run(() => desk.revealPath(skill.path))}
          >
            <FolderOpen size={15} />
          </button>
        </div>
        <div className="skill-toolbar">
          <div className="segmented">
            <button
              className={mode === 'preview' ? 'active' : ''}
              onClick={() => setMode('preview')}
            >
              <Eye size={14} />
              Preview
            </button>
            <button className={mode === 'edit' ? 'active' : ''} onClick={() => setMode('edit')}>
              <Code2 size={14} />
              {skill.editable ? 'Edit' : 'Source'}
            </button>
          </div>
          <div className="button-row">
            {dirty && <span className="unsaved-dot">Unsaved</span>}
            <button
              className="secondary-button compact"
              disabled={!skill.editable || !dirty || saving}
              onClick={() => void save()}
            >
              <Save size={14} />
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      </header>
      {!skill.editable && (
        <div className="inline-note">
          {skill.linked
            ? 'This skill is linked from another location.'
            : 'This source is managed outside Agent Desk.'}{' '}
          Open its source folder to manage it there.
        </div>
      )}
      <div className="skill-editor-body">
        {mode === 'edit' ? (
          <textarea
            aria-label="Skill Markdown source"
            className="code-editor skill-source"
            spellCheck={false}
            readOnly={!skill.editable}
            value={content}
            onChange={(e) => {
              setContent(e.target.value);
              skillDrafts.set(skill.id, { content: e.target.value, revision, savedContent });
            }}
          />
        ) : (
          <div className="markdown skill-preview">
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
                img: ({ alt }) => <span>[Image: {alt || 'attachment'}]</span>,
              }}
            >
              {content.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/, '')}
            </ReactMarkdown>
          </div>
        )}
      </div>
      <footer className="skill-footer">
        <button
          className="text-button"
          disabled={!skill.editable || dirty || saving}
          onClick={() =>
            void run(
              async () => {
                await desk.setSkillEnabled({ id: skill.id, enabled: !!skill.disabled });
                await query.invalidateQueries({ queryKey: ['skills'] });
                await query.invalidateQueries({ queryKey: ['skill', skill.id] });
              },
              skill.disabled ? 'Skill restored' : 'Skill disabled',
            )
          }
        >
          {skill.disabled ? <ToggleLeft size={19} /> : <ToggleRight size={19} />}
          {skill.disabled ? 'Restore skill' : 'Disable skill'}
        </button>
        <button
          className="primary-button"
          disabled={dirty}
          title={dirty ? 'Save your changes first' : 'Start a coding agent with this skill'}
          onClick={() => setImprove(true)}
        >
          <Sparkles size={15} />
          Improve with an agent
        </button>
      </footer>
      {improve && (
        <ImproveSkill
          document={{ ...document, content }}
          bootstrap={bootstrap}
          onLaunch={onLaunch}
          onClose={() => setImprove(false)}
        />
      )}
    </section>
  );
}
function CreateSkill({
  roots,
  onClose,
  onCreated,
}: {
  roots: SkillRoot[];
  onClose: () => void;
  onCreated: (id: string) => void;
}): ReactElement {
  const writable = roots.filter((r) => r.writable);
  const [root, setRoot] = useState(writable[0]?.id ?? '');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [body, setBody] = useState(
    '# Purpose\n\nDescribe what this skill helps the agent accomplish.\n\n## Approach\n\n',
  );
  const [saving, setSaving] = useState(false);
  const query = useQueryClient();
  const { run } = useNotices();
  const submit = async (): Promise<void> => {
    setSaving(true);
    await run(async () => {
      const document = await desk.createSkill({
        rootId: root,
        name,
        content: `---\nname: ${JSON.stringify(name)}\ndescription: ${JSON.stringify(description)}\n---\n\n${body}`,
      });
      await query.invalidateQueries({ queryKey: ['skills'] });
      onCreated(document.skill.id);
    }, 'Skill created');
    setSaving(false);
  };
  return (
    <Modal
      title="Create a skill"
      subtitle="A reusable bit of knowledge, in your own words."
      onClose={onClose}
      wide
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <div className="modal-body">
          {!writable.length && (
            <ErrorBox error="No writable skill directory was found. Add a skill directory in Settings, then try again." />
          )}
          <div className="form-grid">
            <Field label="Name" hint="Lowercase words with hyphens.">
              <input
                required
                pattern="[a-z0-9]+(?:-[a-z0-9]+)*"
                placeholder="my-useful-skill"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </Field>
            <Field label="Save in">
              <select required value={root} onChange={(e) => setRoot(e.target.value)}>
                {writable.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.path}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          <Field label="Description">
            <input
              required
              placeholder="When and why should an agent use this skill?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </Field>
          <Field label="Instructions · Markdown">
            <textarea
              className="code-editor"
              spellCheck={false}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={11}
            />
          </Field>
        </div>
        <footer className="modal-footer">
          <button type="button" className="secondary-button" onClick={onClose}>
            Cancel
          </button>
          <button
            className="primary-button"
            disabled={saving || !root || !name.trim()}
            type="submit"
          >
            <Plus size={15} />
            {saving ? 'Creating…' : 'Create skill'}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
function ImproveSkill({
  document,
  bootstrap,
  onLaunch,
  onClose,
}: {
  document: SkillDocument;
  bootstrap: Bootstrap;
  onLaunch: (request: LaunchRequest) => Promise<boolean>;
  onClose: () => void;
}): ReactElement {
  const profiles = bootstrap.profiles;
  const [profile, setProfile] = useState(
    profiles.find((p) => p.id === bootstrap.settings.defaultProfileId)?.id ?? profiles[0]?.id ?? '',
  );
  const [prompt, setPrompt] = useState(
    `Improve the skill at ${document.skill.path}. Read its complete instructions and relevant companion files, preserve its intent, and make it clearer and more effective for real tasks. Check the result and explain the changes.`,
  );
  const [busy, setBusy] = useState(false);
  return (
    <Modal
      title="Give this skill a fresh pair of eyes"
      subtitle="This starts a real agent session with the skill’s source path."
      onClose={onClose}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const selected = profiles.find((p) => p.id === profile);
          if (!selected) return;
          setBusy(true);
          void onLaunch({
            agent: selected.agent,
            profileId: selected.id,
            projectPath: document.skill.path.replace(/[\\/][^\\/]+$/, ''),
            prompt,
          })
            .then((success) => {
              if (success) onClose();
            })
            .finally(() => setBusy(false));
        }}
      >
        <div className="modal-body">
          <Field label="Agent & connection">
            <select value={profile} onChange={(e) => setProfile(e.target.value)}>
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="What should it improve?">
            <textarea rows={7} value={prompt} onChange={(e) => setPrompt(e.target.value)} />
          </Field>
        </div>
        <footer className="modal-footer">
          <button type="button" className="secondary-button" onClick={onClose}>
            Cancel
          </button>
          <button
            className="primary-button"
            disabled={busy || !profile || !prompt.trim()}
            type="submit"
          >
            <Sparkles size={15} />
            {busy ? 'Starting…' : 'Start agent'}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
