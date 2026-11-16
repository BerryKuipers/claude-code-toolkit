import { Component, type ReactElement, type ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App } from './App';
import { ErrorBox, NoticeProvider } from './ui';
import './styles.css';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});
class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error): { error: Error } {
    return { error };
  }
  render(): ReactNode {
    if (this.state.error)
      return (
        <div className="startup-screen">
          <h1>The workspace needs a restart.</h1>
          <ErrorBox error={this.state.error} retry={() => window.location.reload()} />
        </div>
      );
    return this.props.children;
  }
}
createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <NoticeProvider>
        <App />
      </NoticeProvider>
    </QueryClientProvider>
  </ErrorBoundary>,
);
