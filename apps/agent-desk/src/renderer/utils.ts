import type { AgentId } from '../shared/types';
export const AGENTS: { id: AgentId; label: string; short: string; symbol: string }[] = [
  { id: 'claude', label: 'Claude Code', short: 'Claude', symbol: '✳' },
  { id: 'codex', label: 'Codex', short: 'Codex', symbol: '⌘' },
  { id: 'gemini', label: 'Gemini CLI', short: 'Gemini', symbol: '✦' },
  { id: 'antigravity', label: 'Antigravity', short: 'Antigravity', symbol: '△' },
];
export function agentName(id: AgentId | 'proxy' | 'shared'): string {
  return AGENTS.find((a) => a.id === id)?.label ?? (id === 'proxy' ? 'Proxy' : 'Shared');
}
export function relativeDate(date: string): string {
  const delta = Date.now() - new Date(date).getTime();
  if (!Number.isFinite(delta)) return 'Unknown date';
  if (delta < 60000) return 'Just now';
  if (delta < 3600000) return `${Math.floor(delta / 60000)}m ago`;
  if (delta < 86400000) return `${Math.floor(delta / 3600000)}h ago`;
  if (delta < 604800000) return `${Math.floor(delta / 86400000)}d ago`;
  return new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
export function dateLabel(date: string): string {
  const d = new Date(date);
  const today = new Date();
  if (d.toDateString() === today.toDateString()) return 'Today';
  today.setDate(today.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return 'Yesterday';
  return d.toLocaleDateString(undefined, { month: 'long', day: 'numeric' });
}
export function baseName(path: string): string {
  return path.split(/[\\/]/).filter(Boolean).at(-1) ?? path;
}
export function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
export function contextLabel(tokens?: number): string {
  return tokens ? `${Math.round(tokens / 1000)}k context` : 'Context not listed';
}
