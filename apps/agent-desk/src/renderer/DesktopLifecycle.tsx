import { useEffect, useRef, useState, type ReactElement } from 'react';
import { getCurrentWindow } from '@tauri-apps/api/window';
import { LogOut } from 'lucide-react';
import type { TerminalInfo } from '../shared/types';
import { closeDesktop, IS_TAURI } from './tauri';
import { hasUnsavedChanges } from './unsaved';
import { Modal, useNotices } from './ui';

interface CloseRequest {
  unsaved: boolean;
  running: number;
}

export function DesktopLifecycle({
  terminals,
}: {
  terminals: TerminalInfo[];
}): ReactElement | null {
  const latestTerminals = useRef(terminals);
  latestTerminals.current = terminals;
  const [request, setRequest] = useState<CloseRequest | null>(null);
  const [closing, setClosing] = useState(false);
  const inProgress = useRef(false);
  const { notify } = useNotices();

  useEffect(() => {
    if (!IS_TAURI) return;
    let disposed = false;
    let unlisten: (() => void) | undefined;
    void getCurrentWindow()
      .onCloseRequested((event) => {
        event.preventDefault();
        if (disposed || inProgress.current) return;
        const unsaved = hasUnsavedChanges();
        const running = latestTerminals.current.filter(
          (terminal) => terminal.status === 'running',
        ).length;
        if (unsaved || running) {
          setRequest({ unsaved, running });
          return;
        }
        inProgress.current = true;
        void closeDesktop().catch((cause) => {
          inProgress.current = false;
          notify(String(cause), 'error');
        });
      })
      .then((cleanup) => {
        if (disposed) cleanup();
        else unlisten = cleanup;
      })
      .catch((cause) =>
        notify(`The desktop close guard could not start. ${String(cause)}`, 'error'),
      );
    return () => {
      disposed = true;
      unlisten?.();
    };
  }, [notify]);

  if (!request) return null;
  const close = async (): Promise<void> => {
    if (inProgress.current) return;
    inProgress.current = true;
    setClosing(true);
    try {
      await closeDesktop();
    } catch (cause) {
      inProgress.current = false;
      setClosing(false);
      notify(String(cause), 'error');
    }
  };
  const cancel = (): void => {
    if (!inProgress.current) setRequest(null);
  };
  return (
    <Modal title="Close Agent Desk?" onClose={cancel}>
      <div className="modal-body">
        {request.unsaved && <p>Some edits have not been saved. Closing discards these drafts.</p>}
        {request.running > 0 && (
          <p>
            {request.running} agent {request.running === 1 ? 'session is' : 'sessions are'} still
            running. Closing stops these processes. Saved sessions remain available to resume.
          </p>
        )}
      </div>
      <footer className="modal-footer">
        <button className="secondary-button" disabled={closing} onClick={cancel}>
          Keep working
        </button>
        <button className="danger-button" disabled={closing} onClick={() => void close()}>
          <LogOut size={15} />
          {closing
            ? 'Closing…'
            : request.unsaved
              ? 'Discard changes and quit'
              : 'Close agents and quit'}
        </button>
      </footer>
    </Modal>
  );
}
