import { useEffect, useRef, useState, type ReactElement } from 'react';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { Folder, Play, Plus, Square, TerminalSquare, X } from 'lucide-react';
import type { AppSettings, TerminalInfo, TerminalEvent } from '../../shared/types';
import { desk } from '../api';
import { agentName } from '../utils';
import { AgentMark, EmptyState, ErrorBox, Modal, useNotices } from '../ui';
import '@xterm/xterm/css/xterm.css';

export function Terminals({
  terminals,
  selected,
  onSelect,
  visible,
  settings,
  onNew,
  onClose,
}: {
  terminals: TerminalInfo[];
  selected?: string;
  onSelect: (id: string) => void;
  visible: boolean;
  settings: AppSettings;
  onNew: () => void;
  onClose: (id: string) => Promise<void>;
}): ReactElement {
  const [closing, setClosing] = useState<TerminalInfo>();
  const current = terminals.find((t) => t.id === selected) ?? terminals.at(-1);
  const close = (terminal: TerminalInfo): void => {
    if (terminal.status === 'running') setClosing(terminal);
    else void onClose(terminal.id);
  };
  return (
    <section
      className="terminal-workspace"
      style={{ display: visible ? 'flex' : 'none' }}
      aria-label="Live agent workspace"
    >
      <header className="terminal-workspace-heading">
        <div>
          <div className="eyebrow">IN THE FLOW</div>
          <h1>Workspace</h1>
        </div>
        <button className="secondary-button compact" onClick={onNew}>
          <Plus size={15} />
          New session
        </button>
      </header>
      {terminals.length ? (
        <>
          <div className="terminal-tabs" role="tablist" aria-label="Running sessions">
            {terminals.map((terminal) => (
              <div
                className={`terminal-tab ${current?.id === terminal.id ? 'selected' : ''}`}
                key={terminal.id}
              >
                <button
                  role="tab"
                  aria-selected={current?.id === terminal.id}
                  onClick={() => onSelect(terminal.id)}
                >
                  <AgentMark agent={terminal.agent} small />
                  <span>{terminal.title}</span>
                  <span
                    className={`status-dot ${terminal.status === 'running' ? 'live' : 'stopped'}`}
                  />
                </button>
                <button
                  className="icon-button"
                  title={
                    terminal.status === 'running' ? 'Stop and close session' : 'Close terminal'
                  }
                  aria-label={`Close ${terminal.title}`}
                  onClick={() => close(terminal)}
                >
                  <X size={13} />
                </button>
              </div>
            ))}
          </div>
          <div className="terminal-context">
            <div>
              <Folder size={14} />
              <span>{current?.projectPath}</span>
            </div>
            <span>
              {current?.status === 'running' ? (
                <>
                  <span className="status-dot live" />
                  Running
                </>
              ) : (
                `Exited${current?.exitCode === undefined ? '' : ` · code ${current.exitCode}`}`
              )}
            </span>
          </div>
          <div className="terminal-surfaces">
            {terminals.map((terminal) => (
              <TerminalSurface
                key={terminal.id}
                terminal={terminal}
                active={visible && current?.id === terminal.id}
                settings={settings}
              />
            ))}
          </div>
          <footer className="terminal-footnote">
            <TerminalSquare size={13} />
            <span>
              The native {current ? agentName(current.agent) : 'agent'} interface. Slash commands,
              tools, and keyboard shortcuts work here.
            </span>
            <span>Sessions keep running across views</span>
          </footer>
        </>
      ) : (
        <EmptyState
          title="Make yourself some thinking space."
          action={
            <button className="primary-button" onClick={onNew}>
              <Plus size={15} />
              Start a session
            </button>
          }
        >
          Your live agents will have a home here. Start something new or resume a conversation from
          Sessions.
        </EmptyState>
      )}
      {closing && (
        <Modal
          title="Stop this running session?"
          subtitle={closing.title}
          onClose={() => setClosing(undefined)}
        >
          <div className="modal-body">
            <p>
              This stops the agent process. Its saved conversation remains in the agent’s history.
            </p>
          </div>
          <footer className="modal-footer">
            <button className="secondary-button" onClick={() => setClosing(undefined)}>
              Keep working
            </button>
            <button
              className="danger-button"
              onClick={() => {
                const id = closing.id;
                setClosing(undefined);
                void onClose(id);
              }}
            >
              <Square size={14} />
              Stop and close
            </button>
          </footer>
        </Modal>
      )}
    </section>
  );
}
function TerminalSurface({
  terminal,
  active,
  settings,
}: {
  terminal: TerminalInfo;
  active: boolean;
  settings: AppSettings;
}): ReactElement {
  const host = useRef<HTMLDivElement>(null);
  const instance = useRef<XTerm | undefined>(undefined);
  const fitRef = useRef<FitAddon | undefined>(undefined);
  const [error, setError] = useState<unknown>();
  const { notify } = useNotices();
  const latestSettings = useRef(settings);
  latestSettings.current = settings;
  useEffect(() => {
    const target = host.current!;
    const config = latestSettings.current;
    const xterm = new XTerm({
      cursorBlink: false,
      disableStdin: terminal.status === 'exited',
      fontFamily: "'SFMono-Regular', Consolas, 'Liberation Mono', monospace",
      fontSize: config.fontSize,
      lineHeight: 1.35,
      scrollback: config.terminalScrollback,
      allowProposedApi: false,
      screenReaderMode: true,
      theme: {
        background: '#20211f',
        foreground: '#e6e5dc',
        cursor: '#d6a184',
        selectionBackground: '#57584d',
        black: '#20211f',
        red: '#e58b7a',
        green: '#adc394',
        yellow: '#dac797',
        blue: '#a2bacd',
        magenta: '#c4abd4',
        cyan: '#9dc7bf',
        white: '#e6e5dc',
      },
    });
    const fit = new FitAddon();
    xterm.loadAddon(fit);
    xterm.open(target);
    instance.current = xterm;
    fitRef.current = fit;
    let disposed = false;
    let ready = false;
    let cursor = 0;
    let running = terminal.status === 'running';
    let exitShown = false;
    let pending: TerminalEvent[] = [];
    let pendingBytes = 0;
    let snapshotTimeout: ReturnType<typeof setTimeout> | undefined;
    const showExit = (exitCode?: number): void => {
      running = false;
      xterm.options.disableStdin = true;
      xterm.options.cursorBlink = false;
      if (exitShown) return;
      exitShown = true;
      xterm.write(
        `\r\n\x1b[90m[Session exited${exitCode === undefined ? '' : ` with code ${exitCode}`}]\x1b[0m\r\n`,
      );
    };
    const replay = (event: TerminalEvent): void => {
      if (event.sequence <= cursor) return;
      cursor = event.sequence;
      if (event.type === 'data' && event.data) xterm.write(event.data);
      if (event.type === 'exit') showExit(event.exitCode);
    };
    const startLive = (cause: unknown): void => {
      if (disposed || ready) return;
      clearTimeout(snapshotTimeout);
      setError(
        new Error(
          `Earlier terminal history could not be loaded. Live output is continuing. ${cause instanceof Error ? cause.message : String(cause)}`,
        ),
      );
      ready = true;
      pending.sort((a, b) => a.sequence - b.sequence).forEach(replay);
      pending = [];
      pendingBytes = 0;
    };
    const unsubscribe = desk.onTerminal((event) => {
      if (event.id !== terminal.id || disposed) return;
      if (ready) {
        replay(event);
        return;
      }
      const eventBytes = (event.data?.length ?? 0) * 2 + 128;
      if (pendingBytes + eventBytes > 2 * 1024 * 1024 || pending.length >= 2048) {
        startLive(new Error('The initial history response exceeded the pending output limit.'));
        replay(event);
        return;
      }
      pending.push(event);
      pendingBytes += eventBytes;
    });
    snapshotTimeout = setTimeout(
      () => startLive(new Error('The history request timed out.')),
      5000,
    );
    void desk
      .terminalSnapshot(terminal.id)
      .then((snapshot) => {
        if (disposed || ready) return;
        clearTimeout(snapshotTimeout);
        cursor = snapshot.sequence;
        xterm.write(snapshot.data);
        if (snapshot.status === 'exited') showExit(snapshot.exitCode);
        pending.sort((a, b) => a.sequence - b.sequence).forEach(replay);
        pending = [];
        pendingBytes = 0;
        ready = true;
      })
      .catch(startLive);
    const input = xterm.onData((data) => {
      void desk.terminalWrite(terminal.id, data).catch((cause) => {
        if (!disposed) notify(String(cause), 'error');
      });
    });
    const terminalResize = xterm.onResize(({ cols, rows }) => {
      if (running)
        void desk.terminalResize(terminal.id, cols, rows).catch((cause) => {
          if (!disposed && running) setError(cause);
        });
    });
    const resize = (): void => {
      if (target.clientWidth && target.clientHeight) fit.fit();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(target);
    resize();
    return () => {
      disposed = true;
      clearTimeout(snapshotTimeout);
      observer.disconnect();
      input.dispose();
      terminalResize.dispose();
      unsubscribe();
      xterm.dispose();
      instance.current = undefined;
      fitRef.current = undefined;
    };
  }, [terminal.id, notify]);
  useEffect(() => {
    if (!instance.current) return;
    instance.current.options.fontSize = settings.fontSize;
    instance.current.options.scrollback = settings.terminalScrollback;
    if (active) {
      const timer = requestAnimationFrame(() => {
        fitRef.current?.fit();
        instance.current?.focus();
      });
      return () => cancelAnimationFrame(timer);
    }
  }, [active, settings.fontSize, settings.terminalScrollback]);
  useEffect(() => {
    const terminalInstance = instance.current;
    if (!terminalInstance) return;
    terminalInstance.options.cursorBlink = false;
    if (!active || terminal.status !== 'running') return;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = (): void => {
      terminalInstance.options.cursorBlink =
        document.visibilityState === 'visible' &&
        !reducedMotion.matches &&
        !terminalInstance.options.disableStdin;
    };
    update();
    document.addEventListener('visibilitychange', update);
    reducedMotion.addEventListener('change', update);
    return () => {
      document.removeEventListener('visibilitychange', update);
      reducedMotion.removeEventListener('change', update);
      terminalInstance.options.cursorBlink = false;
    };
  }, [active, terminal.status]);
  return (
    <div className="terminal-surface" style={{ display: active ? 'flex' : 'none' }}>
      {error !== undefined && <ErrorBox error={error} />}
      <div className="xterm-host" ref={host} />
    </div>
  );
}
