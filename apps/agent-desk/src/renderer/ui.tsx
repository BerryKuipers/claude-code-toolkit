import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useRef,
  useState,
  type ReactElement,
  type ReactNode,
} from 'react';
import { AlertCircle, Check, ChevronDown, LoaderCircle, X } from 'lucide-react';
import type { AgentId } from '../shared/types';
import { AGENTS, agentName, errorText } from './utils';

export function AgentMark({
  agent,
  small = false,
}: {
  agent: AgentId | 'shared' | 'proxy';
  small?: boolean;
}): ReactElement {
  return (
    <span
      className={`agent-mark agent-${agent} ${small ? 'small' : ''}`}
      aria-label={agentName(agent)}
    >
      {AGENTS.find((a) => a.id === agent)?.symbol ?? (agent === 'proxy' ? '⇄' : '◇')}
    </span>
  );
}
export function Spinner({ label = 'Loading your workspace' }: { label?: string }): ReactElement {
  return (
    <div className="loading-state" role="status">
      <LoaderCircle className="spin" size={22} />
      <span>{label}</span>
    </div>
  );
}
export function ErrorBox({ error, retry }: { error: unknown; retry?: () => void }): ReactElement {
  return (
    <div className="error-box" role="alert">
      <AlertCircle size={18} />
      <div>
        <strong>Something needs attention</strong>
        <p>{errorText(error)}</p>
        {retry && (
          <button className="text-button" onClick={retry}>
            Try again
          </button>
        )}
      </div>
    </div>
  );
}
export function EmptyState({
  symbol = '✳',
  title,
  children,
  action,
}: {
  symbol?: string;
  title: string;
  children: ReactNode;
  action?: ReactNode;
}): ReactElement {
  return (
    <div className="empty-state">
      <div className="empty-symbol" aria-hidden="true">
        {symbol}
      </div>
      <h2>{title}</h2>
      <p>{children}</p>
      {action}
    </div>
  );
}
export function Warnings({ warnings }: { warnings?: string[] }): ReactElement | null {
  if (!warnings?.length) return null;
  return (
    <details className="warnings">
      <summary>
        <AlertCircle size={14} />
        {warnings.length} {warnings.length === 1 ? 'source note' : 'source notes'}
        <ChevronDown size={13} />
      </summary>
      <ul>
        {warnings.map((w, i) => (
          <li key={i}>{w}</li>
        ))}
      </ul>
    </details>
  );
}
export function Modal({
  title,
  subtitle,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}): ReactElement {
  const ref = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const heading = useId();
  useEffect(() => {
    const before = document.activeElement as HTMLElement | null;
    const panel = ref.current!;
    const nodes = (): HTMLElement[] =>
      Array.from(
        panel.querySelectorAll<HTMLElement>(
          'button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href], [tabindex="0"]',
        ),
      ).filter((node) => node.getClientRects().length > 0);
    (nodes()[1] ?? nodes()[0] ?? panel).focus();
    const keydown = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') {
        e.preventDefault();
        closeRef.current();
      }
      if (e.key !== 'Tab') return;
      const focusable = nodes();
      const first = focusable[0];
      const last = focusable.at(-1);
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last?.focus();
      }
      if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener('keydown', keydown);
    return () => {
      document.removeEventListener('keydown', keydown);
      before?.focus();
    };
  }, []);
  return (
    <div
      className="modal-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={ref}
        className={`modal ${wide ? 'wide' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={heading}
        tabIndex={-1}
      >
        <header className="modal-header">
          <div>
            <h2 id={heading}>{title}</h2>
            {subtitle && <p>{subtitle}</p>}
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close dialog">
            <X size={19} />
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}
interface Notice {
  id: number;
  text: string;
  kind: 'success' | 'error';
}
interface NoticeContext {
  notify: (text: string, kind?: Notice['kind']) => void;
  run: <T>(task: () => Promise<T>, success?: string) => Promise<T | undefined>;
}
const Notices = createContext<NoticeContext | null>(null);
export function NoticeProvider({ children }: { children: ReactNode }): ReactElement {
  const [notices, setNotices] = useState<Notice[]>([]);
  const next = useRef(0);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  useEffect(() => () => timers.current.forEach(clearTimeout), []);
  const notify = useCallback((text: string, kind: Notice['kind'] = 'success'): void => {
    const id = ++next.current;
    setNotices((current) => [...current.slice(-3), { id, text, kind }]);
    timers.current.push(
      setTimeout(
        () => setNotices((current) => current.filter((n) => n.id !== id)),
        kind === 'error' ? 12000 : 5000,
      ),
    );
  }, []);
  const run = useCallback(
    async <T,>(task: () => Promise<T>, success?: string): Promise<T | undefined> => {
      try {
        const result = await task();
        if (success) notify(success);
        return result;
      } catch (error) {
        notify(errorText(error), 'error');
        return undefined;
      }
    },
    [notify],
  );
  return (
    <Notices.Provider value={{ notify, run }}>
      {children}
      <div className="toast-region" aria-live="polite">
        {notices.map((n) => (
          <div
            key={n.id}
            className={`toast ${n.kind}`}
            role={n.kind === 'error' ? 'alert' : 'status'}
          >
            {n.kind === 'success' ? <Check size={17} /> : <AlertCircle size={17} />}
            <span>{n.text}</span>
            <button
              className="icon-button"
              aria-label="Dismiss notification"
              onClick={() => setNotices((current) => current.filter((item) => item.id !== n.id))}
            >
              <X size={15} />
            </button>
          </div>
        ))}
      </div>
    </Notices.Provider>
  );
}
export function useNotices(): NoticeContext {
  const value = useContext(Notices);
  if (!value) throw new Error('NoticeProvider is required');
  return value;
}
export function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}): ReactElement {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint && <small>{hint}</small>}
    </label>
  );
}
