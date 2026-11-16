import { useCallback, useEffect, useState, type ReactElement } from 'react';
import {
  BookOpen,
  ChevronRight,
  CircleHelp,
  Command,
  Folder,
  LayoutGrid,
  MessageSquare,
  Monitor,
  Plus,
  Settings2,
  SlidersHorizontal,
  TerminalSquare,
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import type { Bootstrap, LaunchRequest, TerminalInfo } from '../shared/types';
import { desk, IS_DEMO, useBootstrap, useSessions, useTerminals } from './api';
import { hasUnsavedChanges } from './unsaved';
import { baseName, errorText } from './utils';
import { AgentMark, EmptyState, ErrorBox, Spinner, useNotices } from './ui';
import { Sessions } from './features/Sessions';
import { Models } from './features/Models';
import { Skills } from './features/Skills';
import { Settings } from './features/Settings';
import { Terminals } from './features/Terminals';
import { NewSession } from './features/NewSession';

type View = 'sessions' | 'models' | 'skills' | 'settings' | 'workspace';
const NAVIGATION = [
  { id: 'sessions' as const, label: 'Sessions', icon: MessageSquare },
  { id: 'models' as const, label: 'Models & connections', icon: SlidersHorizontal },
  { id: 'skills' as const, label: 'Skills', icon: BookOpen },
];
const VIEW_LABELS: Record<View, string> = {
  sessions: 'Sessions',
  models: 'Models & connections',
  skills: 'Skills',
  settings: 'Settings',
  workspace: 'Live workspace',
};

export function App(): ReactElement {
  if (!desk) return <DesktopRequired />;
  return <ConnectedApp />;
}
function ConnectedApp(): ReactElement {
  const bootstrap = useBootstrap();
  if (bootstrap.isPending)
    return (
      <div className="startup-screen">
        <div className="brand-mark large">✳</div>
        <h1>Agent Desk</h1>
        <Spinner label="Making a little room for your work…" />
      </div>
    );
  if (bootstrap.isError)
    return (
      <div className="startup-screen">
        <div className="brand-mark large">✳</div>
        <h1>Let’s get you connected.</h1>
        <ErrorBox error={bootstrap.error} retry={() => void bootstrap.refetch()} />
      </div>
    );
  return <Workspace bootstrap={bootstrap.data} />;
}
function Workspace({ bootstrap }: { bootstrap: Bootstrap }): ReactElement {
  const [view, setView] = useState<View>('sessions');
  const [search, setSearch] = useState('');
  const [project, setProject] = useState('all');
  const [newSession, setNewSession] = useState(false);
  const [selectedTerminal, setSelectedTerminal] = useState<string>();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const sessions = useSessions(0, bootstrap.settings.scanOnStart);
  const terminals = useTerminals();
  const query = useQueryClient();
  const { run, notify } = useNotices();
  const terminalList = terminals.data ?? [];
  const running = terminalList.filter((t) => t.status === 'running');
  const projects = [
    ...new Set([
      ...bootstrap.settings.projects,
      ...(sessions.data?.sessions ?? []).map((s) => s.projectPath),
    ]),
  ]
    .filter(Boolean)
    .slice(0, 9);
  const navigate = (next: View): void => {
    setView(next);
    setSidebarOpen(false);
  };
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const apply = (): void => {
      document.documentElement.dataset.theme =
        bootstrap.settings.theme === 'system'
          ? media.matches
            ? 'dark'
            : 'light'
          : bootstrap.settings.theme;
    };
    apply();
    media.addEventListener('change', apply);
    return () => media.removeEventListener('change', apply);
  }, [bootstrap.settings.theme]);
  useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent): void => {
      if (hasUnsavedChanges()) event.preventDefault();
    };
    window.addEventListener('beforeunload', beforeUnload);
    return () => window.removeEventListener('beforeunload', beforeUnload);
  }, []);
  useEffect(() => {
    const shortcut = (event: KeyboardEvent): void => {
      const target = event.target instanceof Element ? event.target : null;
      if (target?.closest('.xterm') || document.activeElement?.closest('.xterm')) return;
      if (!(event.metaKey || event.ctrlKey)) return;
      if (event.key.toLowerCase() === 'n') {
        event.preventDefault();
        setNewSession(true);
      }
      if (event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setView('sessions');
        setTimeout(() => document.getElementById('session-search')?.focus(), 20);
      }
      if (event.key === ',') {
        event.preventDefault();
        setView('settings');
      }
    };
    window.addEventListener('keydown', shortcut);
    return () => window.removeEventListener('keydown', shortcut);
  }, []);
  useEffect(
    () =>
      desk.onTerminal((event) => {
        if (event.type === 'exit') {
          for (const key of ['terminals', 'sessions', 'skills', 'skill', 'configs'])
            void query.invalidateQueries({ queryKey: [key] });
        }
      }),
    [query],
  );
  const openTerminal = useCallback(
    (terminal: TerminalInfo): void => {
      query.setQueryData<TerminalInfo[]>(['terminals'], (current) => [
        ...(current ?? []).filter((t) => t.id !== terminal.id),
        terminal,
      ]);
      setSelectedTerminal(terminal.id);
      setView('workspace');
    },
    [query],
  );
  const launch = useCallback(
    async (request: LaunchRequest): Promise<boolean> => {
      try {
        const terminal = await desk.launch(request);
        openTerminal(terminal);
        void query.invalidateQueries({ queryKey: ['sessions'] });
        return true;
      } catch (error) {
        notify(errorText(error), 'error');
        return false;
      }
    },
    [openTerminal, query, notify],
  );
  const closeTerminal = async (id: string): Promise<void> => {
    await run(async () => {
      await desk.terminalClose(id);
      query.setQueryData<TerminalInfo[]>(
        ['terminals'],
        (current) => current?.filter((t) => t.id !== id) ?? [],
      );
      await query.invalidateQueries({ queryKey: ['terminals'] });
    });
  };
  return (
    <div className="app-shell">
      {IS_DEMO && (
        <div className="demo-banner">
          <span className="demo-pill">DEMO WORKSPACE</span>Sample data for a look around. Your
          files, keys, and tools are untouched.
          <span>Open the desktop app for live connections.</span>
        </div>
      )}
      <div className="app-body">
        {sidebarOpen && (
          <button
            className="sidebar-backdrop"
            aria-label="Close navigation"
            onClick={() => setSidebarOpen(false)}
          />
        )}
        <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
          <button
            className="brand"
            onClick={() => {
              setProject('all');
              navigate('sessions');
            }}
            aria-label="Agent Desk home"
          >
            <span className="brand-mark">✳</span>
            <span>Agent Desk</span>
          </button>
          <button className="new-session-button" onClick={() => setNewSession(true)}>
            <Plus size={17} />
            <span>New session</span>
            <kbd>⌘ N</kbd>
          </button>
          <nav aria-label="Main navigation">
            {NAVIGATION.map((item) => (
              <button
                key={item.id}
                className={`nav-item ${view === item.id ? 'active' : ''}`}
                onClick={() => {
                  if (item.id === 'sessions') setProject('all');
                  navigate(item.id);
                }}
                aria-current={view === item.id ? 'page' : undefined}
              >
                <item.icon size={17} />
                <span>{item.label}</span>
                {item.id === 'sessions' && !!sessions.data?.sessions.length && (
                  <span className="nav-count">{sessions.data.sessions.length}</span>
                )}
              </button>
            ))}
            <button
              className={`nav-item ${view === 'workspace' ? 'active' : ''}`}
              onClick={() => navigate('workspace')}
              aria-current={view === 'workspace' ? 'page' : undefined}
            >
              <TerminalSquare size={17} />
              <span>Workspace</span>
              {running.length > 0 && <span className="live-count">{running.length}</span>}
            </button>
          </nav>
          <div className="sidebar-section">
            <div className="sidebar-section-heading">
              <span>PROJECTS</span>
              <button
                className="icon-button"
                title="Manage project folders"
                aria-label="Manage project folders"
                onClick={() => navigate('settings')}
              >
                <Plus size={13} />
              </button>
            </div>
            <div className="sidebar-projects">
              {projects.length ? (
                projects.map((path) => (
                  <button
                    className={`project-link ${project === path && view === 'sessions' ? 'active' : ''}`}
                    key={path}
                    onClick={() => {
                      setProject(path);
                      setSearch('');
                      navigate('sessions');
                    }}
                    title={path}
                  >
                    <Folder size={15} />
                    <span>{baseName(path)}</span>
                  </button>
                ))
              ) : (
                <p className="sidebar-empty">
                  Your projects will find
                  <br />a home here.
                </p>
              )}
            </div>
          </div>
          {running.length > 0 && (
            <div className="sidebar-section running-section">
              <div className="sidebar-section-heading">
                <span>RUNNING</span>
                <span className="status-dot live" />
              </div>
              {running.map((terminal) => (
                <button
                  key={terminal.id}
                  className={`running-link ${selectedTerminal === terminal.id && view === 'workspace' ? 'active' : ''}`}
                  onClick={() => {
                    setSelectedTerminal(terminal.id);
                    navigate('workspace');
                  }}
                >
                  <AgentMark agent={terminal.agent} small />
                  <span>{terminal.title}</span>
                </button>
              ))}
            </div>
          )}
          <div className="sidebar-bottom">
            <button
              className={`nav-item ${view === 'settings' ? 'active' : ''}`}
              onClick={() => navigate('settings')}
            >
              <Settings2 size={17} />
              <span>Settings</span>
              <kbd>⌘ ,</kbd>
            </button>
            <div className="local-workspace">
              <div className="local-avatar">
                <Monitor size={17} />
              </div>
              <div>
                <strong>Local workspace</strong>
                <span>{bootstrap.agents.filter((a) => a.available).length} agents detected</span>
              </div>
              <span className="status-dot" />
            </div>
          </div>
        </aside>
        <main className="main-workspace">
          <div className="window-bar">
            <button
              className="icon-button mobile-menu"
              aria-label="Open navigation"
              onClick={() => setSidebarOpen(true)}
            >
              <LayoutGrid size={17} />
            </button>
            <span>Workspace</span>
            <ChevronRight size={12} />
            <strong>{VIEW_LABELS[view]}</strong>
            <div className="window-status">
              <span className="status-dot" />
              On your computer
            </div>
          </div>
          <div className="main-content">
            <div className="view-panel" hidden={view !== 'sessions'}>
              <Sessions
                bootstrap={bootstrap}
                search={search}
                setSearch={setSearch}
                project={project}
                setProject={setProject}
                onNew={() => setNewSession(true)}
                onLaunch={launch}
              />
            </div>
            <div className="view-panel" hidden={view !== 'models'}>
              <Models bootstrap={bootstrap} onTerminal={openTerminal} />
            </div>
            <div className="view-panel" hidden={view !== 'skills'}>
              <Skills bootstrap={bootstrap} onLaunch={launch} />
            </div>
            <div className="view-panel" hidden={view !== 'settings'}>
              <Settings bootstrap={bootstrap} />
            </div>
            {terminals.isError && view === 'workspace' && (
              <ErrorBox error={terminals.error} retry={() => void terminals.refetch()} />
            )}
            <Terminals
              terminals={terminalList}
              selected={selectedTerminal}
              onSelect={setSelectedTerminal}
              visible={view === 'workspace'}
              settings={bootstrap.settings}
              onNew={() => setNewSession(true)}
              onClose={closeTerminal}
            />
          </div>
        </main>
      </div>
      {newSession && (
        <NewSession
          bootstrap={bootstrap}
          initialProject={project}
          onClose={() => setNewSession(false)}
          onLaunch={launch}
        />
      )}
    </div>
  );
}
function DesktopRequired(): ReactElement {
  return (
    <div className="desktop-required">
      <div className="brand">
        <span className="brand-mark">✳</span>
        <span>Agent Desk</span>
      </div>
      <EmptyState
        symbol="⌘"
        title="Your agents live on your computer."
        action={
          <a className="primary-button" href="?demo=1">
            Explore the sample workspace
            <ChevronRight size={16} />
          </a>
        }
      >
        Open the desktop application to access your sessions, local settings, skills, and live
        terminals. This browser view cannot access them.
      </EmptyState>
      <p className="desktop-note">
        For development, start the Electron app with <code>npm run dev</code>.
      </p>
    </div>
  );
}
