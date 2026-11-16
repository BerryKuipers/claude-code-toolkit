export type AgentId = 'claude' | 'codex' | 'gemini' | 'antigravity';
export type Theme = 'system' | 'light' | 'dark';
export type Route = 'native' | 'anthropic' | 'openai-responses' | 'gemini';

export interface ProviderProfile {
  id: string;
  name: string;
  agent: AgentId;
  provider: 'native' | 'local-proxy' | 'openrouter' | 'deepseek' | 'custom';
  route: Route;
  baseUrl?: string;
  model?: string;
  smallModel?: string;
  subagentModel?: string;
  effort?: string;
  apiKeyEnv?: string;
  authMode?: 'bearer' | 'api-key';
  settingsFile?: string;
  contextWindow?: number;
  env: Record<string, string>;
  hasSecret?: boolean;
}

export interface HistoryRoot {
  id: string;
  agent: AgentId;
  path: string;
}

export interface AppSettings {
  theme: Theme;
  fontSize: number;
  terminalScrollback: number;
  defaultProfileId: string;
  projects: string[];
  historyRoots: HistoryRoot[];
  skillDirectories: string[];
  agentCommands: Record<AgentId, string>;
  proxyCommand: string;
  scanOnStart: boolean;
  autoRefreshSeconds: number;
}

export interface AgentInstall {
  id: AgentId;
  label: string;
  command: string;
  available: boolean;
  version?: string;
  path?: string;
  error?: string;
}

export interface SessionRecord {
  id: string;
  nativeId: string;
  agent: AgentId;
  title: string;
  projectPath: string;
  projectName: string;
  createdAt: string;
  updatedAt: string;
  preview: string;
  messageCount: number;
  model?: string;
  sourcePath?: string;
  sourceKind: 'cli' | 'desktop' | 'ide';
  resumable: boolean;
  resumeNote?: string;
  archived?: boolean;
}

export interface SessionMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp?: string;
  model?: string;
  toolName?: string;
}

export interface SessionIndex {
  sessions: SessionRecord[];
  warnings: string[];
  scannedAt: string;
}

export interface Transcript {
  session: SessionRecord;
  messages: SessionMessage[];
  warnings: string[];
  truncated?: boolean;
}

export interface SkillRoot {
  id: string;
  path: string;
  agent: AgentId | 'shared';
  scope: 'user' | 'project' | 'plugin' | 'shared';
  writable: boolean;
}

export interface SkillRecord {
  id: string;
  name: string;
  description: string;
  path: string;
  agent: AgentId | 'shared';
  scope: SkillRoot['scope'];
  rootId: string;
  editable: boolean;
  linked: boolean;
  disabled?: boolean;
}

export interface SkillDocument {
  skill: SkillRecord;
  content: string;
  revision: string;
}

export interface ConfigDocument {
  id: string;
  agent: AgentId;
  label: string;
  path: string;
  format: 'json' | 'toml' | 'markdown';
  exists: boolean;
  content: string;
  revision: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  contextWindow?: number;
  inputPrice?: number;
  outputPrice?: number;
  free?: boolean;
}

export interface ModelCatalog {
  models: ModelInfo[];
  source: string;
  verifiedAt: string;
  latencyMs: number;
  warnings: string[];
}

export interface ProviderStatus {
  ok: boolean;
  message: string;
  latencyMs: number;
  checkedAt: string;
  modelCount?: number;
}

export interface LaunchRequest {
  agent: AgentId;
  projectPath: string;
  profileId?: string;
  sessionId?: string;
  prompt?: string;
}

export interface TerminalInfo {
  id: string;
  agent: AgentId | 'proxy';
  title: string;
  projectPath: string;
  startedAt: string;
  status: 'running' | 'exited';
  exitCode?: number;
  profileId?: string;
  sessionId?: string;
}

export interface TerminalEvent {
  id: string;
  sequence: number;
  type: 'data' | 'exit';
  data?: string;
  exitCode?: number;
}

export interface TerminalSnapshot {
  data: string;
  sequence: number;
  status: TerminalInfo['status'];
  exitCode?: number;
}

export interface Bootstrap {
  settings: AppSettings;
  profiles: ProviderProfile[];
  agents: AgentInstall[];
  skillRoots: SkillRoot[];
  appVersion: string;
  platform: string;
  home: string;
  secureStorageAvailable: boolean;
  warnings?: string[];
}

export interface DeskApi {
  bootstrap(): Promise<Bootstrap>;
  sessions(refresh?: boolean): Promise<SessionIndex>;
  transcript(id: string): Promise<Transcript>;
  skills(): Promise<{ skills: SkillRecord[]; roots: SkillRoot[]; warnings: string[] }>;
  readSkill(id: string): Promise<SkillDocument>;
  saveSkill(input: { id: string; content: string; revision: string }): Promise<SkillDocument>;
  createSkill(input: { rootId: string; name: string; content: string }): Promise<SkillDocument>;
  setSkillEnabled(input: { id: string; enabled: boolean }): Promise<void>;
  configs(): Promise<ConfigDocument[]>;
  saveConfig(input: { id: string; content: string; revision: string }): Promise<ConfigDocument>;
  saveSettings(settings: AppSettings): Promise<AppSettings>;
  saveProfile(profile: ProviderProfile): Promise<ProviderProfile>;
  deleteProfile(id: string): Promise<void>;
  saveSecret(input: { profileId: string; secret: string; persist: boolean }): Promise<void>;
  deleteSecret(profileId: string): Promise<void>;
  models(profileId: string): Promise<ModelCatalog>;
  probe(profileId: string): Promise<ProviderStatus>;
  launch(request: LaunchRequest): Promise<TerminalInfo>;
  terminals(): Promise<TerminalInfo[]>;
  terminalSnapshot(id: string): Promise<TerminalSnapshot>;
  terminalWrite(id: string, data: string): Promise<void>;
  terminalResize(id: string, cols: number, rows: number): Promise<void>;
  terminalClose(id: string): Promise<void>;
  onTerminal(listener: (event: TerminalEvent) => void): () => void;
  pickDirectory(): Promise<string | null>;
  revealPath(path: string): Promise<void>;
  openExternal(url: string): Promise<void>;
  exportSession(id: string): Promise<string | null>;
  proxyStart(): Promise<TerminalInfo>;
  proxyAuthenticate(provider: 'codex' | 'kimi' | 'grok' | 'cursor'): Promise<TerminalInfo>;
  proxyMonitor(profileId: string): Promise<unknown>;
}

declare global {
  interface Window {
    desk: DeskApi;
  }
}
