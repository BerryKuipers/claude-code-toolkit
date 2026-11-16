import type {
  Bootstrap,
  DeskApi,
  SessionRecord,
  SkillDocument,
  ConfigDocument,
  ProviderProfile,
} from '../shared/types';

const NOW = new Date();
const ago = (hours: number): string => new Date(NOW.getTime() - hours * 3600000).toISOString();
const profiles: ProviderProfile[] = [
  {
    id: 'claude-native',
    name: 'Claude · native configuration',
    agent: 'claude',
    provider: 'native',
    route: 'native',
    env: {},
  },
  {
    id: 'codex-native',
    name: 'Codex · native configuration',
    agent: 'codex',
    provider: 'native',
    route: 'native',
    env: {},
  },
  {
    id: 'gemini-native',
    name: 'Gemini · native configuration',
    agent: 'gemini',
    provider: 'native',
    route: 'native',
    env: {},
  },
  {
    id: 'local-proxy',
    name: 'Home proxy',
    agent: 'claude',
    provider: 'local-proxy',
    route: 'anthropic',
    baseUrl: 'http://127.0.0.1:18765',
    model: 'auto',
    env: {},
  },
  {
    id: 'openrouter',
    name: 'OpenRouter · explore',
    agent: 'claude',
    provider: 'openrouter',
    route: 'anthropic',
    baseUrl: 'https://openrouter.ai/api',
    apiKeyEnv: 'OPENROUTER_API_KEY',
    env: {},
    hasSecret: true,
  },
];
const sessions: SessionRecord[] = [
  {
    id: 'demo-1',
    nativeId: 'sample-session-1',
    agent: 'claude',
    title: 'Give the studio a little breathing room',
    projectPath: '/Users/you/Projects/studio',
    projectName: 'studio',
    createdAt: ago(3),
    updatedAt: ago(0.2),
    preview: 'A quieter workspace, a clearer hierarchy, and a place for every idea.',
    messageCount: 12,
    model: 'Native default',
    sourceKind: 'cli',
    resumable: true,
  },
  {
    id: 'demo-2',
    nativeId: 'sample-session-2',
    agent: 'codex',
    title: 'Make the audio pipeline feel instant',
    projectPath: '/Users/you/Projects/home-sage',
    projectName: 'home-sage',
    createdAt: ago(5),
    updatedAt: ago(2),
    preview: 'Stream the first sentence while the next one is still being generated.',
    messageCount: 28,
    model: 'Native default',
    sourceKind: 'cli',
    resumable: true,
  },
  {
    id: 'demo-3',
    nativeId: 'sample-session-3',
    agent: 'gemini',
    title: 'A fresh pair of eyes on the architecture',
    projectPath: '/Users/you/Projects/studio',
    projectName: 'studio',
    createdAt: ago(8),
    updatedAt: ago(4),
    preview: 'Follow the data from the session index into the project workspace.',
    messageCount: 9,
    sourceKind: 'cli',
    resumable: true,
  },
  {
    id: 'demo-4',
    nativeId: 'sample-session-4',
    agent: 'claude',
    title: 'The small details that make a big difference',
    projectPath: '/Users/you/Projects/flower-guy',
    projectName: 'flower-guy',
    createdAt: ago(30),
    updatedAt: ago(26),
    preview: 'Keyboard navigation, meaningful empty states, and a calmer palette.',
    messageCount: 35,
    sourceKind: 'cli',
    resumable: true,
  },
  {
    id: 'demo-5',
    nativeId: 'sample-session-5',
    agent: 'antigravity',
    title: 'Explore a warmer lighting direction',
    projectPath: '/Users/you/Projects/mokum',
    projectName: 'mokum',
    createdAt: ago(50),
    updatedAt: ago(48),
    preview: 'Notes from the material and lighting study.',
    messageCount: 6,
    sourceKind: 'ide',
    resumable: false,
    resumeNote:
      'Antigravity stores proprietary session state. Open the project in Antigravity to continue.',
  },
];
const skillDocs: SkillDocument[] = [
  {
    skill: {
      id: 'demo-skill-1',
      name: 'finish-the-slice',
      description: 'Carry an idea through implementation, verification, and a clean handoff.',
      path: '/Users/you/.claude/skills/finish-the-slice/SKILL.md',
      agent: 'claude',
      scope: 'user',
      rootId: 'demo-root',
      editable: true,
      linked: false,
    },
    content:
      '---\nname: finish-the-slice\ndescription: Carry an idea through implementation, verification, and a clean handoff.\n---\n\n# Finish the slice\n\nStart with the outcome. Understand the existing project before changing it.\n\n## Work with purpose\n\n- Build one complete behavior at a time.\n- Verify the part that matters.\n- Keep the result easy to review.\n\n## A useful handoff\n\nExplain what changed, why it changed, and what was actually tested.\n',
    revision: 'demo-r1',
  },
  {
    skill: {
      id: 'demo-skill-2',
      name: 'design-eye',
      description: 'Turn a good layout into a thoughtful, coherent product experience.',
      path: '/Users/you/.agents/skills/design-eye/SKILL.md',
      agent: 'shared',
      scope: 'shared',
      rootId: 'demo-root',
      editable: true,
      linked: false,
    },
    content:
      '---\nname: design-eye\ndescription: Turn a good layout into a thoughtful product experience.\n---\n\n# Design eye\n\nGive each screen a clear purpose. Use space, rhythm, and contrast to make that purpose obvious.\n',
    revision: 'demo-r1',
  },
  {
    skill: {
      id: 'demo-skill-3',
      name: 'evidence-reasoner',
      description: 'Separate observed facts from assumptions, and make decisions traceable.',
      path: '/Users/you/.codex/skills/evidence-reasoner/SKILL.md',
      agent: 'codex',
      scope: 'user',
      rootId: 'demo-root',
      editable: true,
      linked: false,
    },
    content:
      '---\nname: evidence-reasoner\ndescription: Separate observed facts from assumptions.\n---\n\n# Evidence reasoner\n\nUse current primary sources. State what is known, inferred, and still uncertain.\n',
    revision: 'demo-r1',
  },
];
const configDocs: ConfigDocument[] = [
  {
    id: 'demo-config',
    agent: 'claude',
    label: 'Claude settings',
    path: '/Users/you/.claude/settings.json',
    format: 'json',
    exists: true,
    content: '{\n  "model": "default",\n  "permissions": {\n    "defaultMode": "default"\n  }\n}\n',
    revision: 'demo-r1',
  },
];
const bootstrap: Bootstrap = {
  appVersion: '0.1.0',
  platform: 'demo',
  home: '/Users/you',
  secureStorageAvailable: false,
  agents: ['claude', 'codex', 'gemini', 'antigravity'].map((id) => ({
    id: id as 'claude' | 'codex' | 'gemini' | 'antigravity',
    label:
      id === 'claude'
        ? 'Claude Code'
        : id === 'codex'
          ? 'Codex'
          : id === 'gemini'
            ? 'Gemini CLI'
            : 'Antigravity',
    command: id,
    available: true,
    version: 'Sample installation',
  })),
  profiles,
  skillRoots: [
    {
      id: 'demo-root',
      path: '/Users/you/.claude/skills',
      agent: 'claude',
      scope: 'user',
      writable: true,
    },
  ],
  settings: {
    theme: 'light',
    fontSize: 14,
    terminalScrollback: 10000,
    defaultProfileId: 'claude-native',
    projects: [
      '/Users/you/Projects/studio',
      '/Users/you/Projects/home-sage',
      '/Users/you/Projects/flower-guy',
    ],
    historyRoots: [],
    skillDirectories: [],
    agentCommands: {
      claude: 'claude',
      codex: 'codex',
      gemini: 'gemini',
      antigravity: 'antigravity',
    },
    proxyCommand: '',
    scanOnStart: true,
    autoRefreshSeconds: 30,
  },
};
const clone = <T>(v: T): T => structuredClone(v);
const unavailable = async (): Promise<never> => {
  throw new Error(
    'This is a sample workspace. Open Agent Desk on your computer to use live files, connections, and terminals.',
  );
};

export function createDemoApi(): DeskApi {
  return {
    bootstrap: async () => clone(bootstrap),
    sessions: async () => ({
      sessions: clone(sessions),
      warnings: [],
      scannedAt: NOW.toISOString(),
    }),
    transcript: async (id) => ({
      session: clone(sessions.find((s) => s.id === id)!),
      warnings: [],
      messages: [
        {
          id: 'm1',
          role: 'user',
          content:
            'I want this workspace to feel like a place I can actually think. Keep everything within reach, but give the conversation room to breathe.',
          timestamp: ago(0.5),
        },
        {
          id: 'm2',
          role: 'assistant',
          content:
            'Let’s give the work a little more space.\n\nI’ve brought the layout back to three simple ideas:\n\n1. **A familiar home for every session.** Your agents share one searchable history, while each conversation keeps its original context.\n2. **The right model, without the ceremony.** Switch between your subscription, a local proxy, and a direct provider through named profiles.\n3. **Tools that stay out of your way.** Skills and settings live one click away. The conversation stays at the center.\n\n### What changed\n\nThe sidebar now holds the navigation and your projects. The session list uses a quieter rhythm, and the transcript has a comfortable reading width.\n\n```tsx\n<Workspace>\n  <SessionLibrary />\n  <Conversation />\n</Workspace>\n```\n\nAll existing terminal sessions keep running when you move between views. Pick up a conversation whenever you’re ready.',
          timestamp: ago(0.3),
        },
        {
          id: 'm3',
          role: 'user',
          content: 'Good. That feels a lot more like it.',
          timestamp: ago(0.2),
        },
      ],
    }),
    skills: async () => ({
      skills: clone(skillDocs.map((d) => d.skill)),
      roots: clone(bootstrap.skillRoots),
      warnings: [],
    }),
    readSkill: async (id) => clone(skillDocs.find((d) => d.skill.id === id)!),
    saveSkill: unavailable,
    createSkill: unavailable,
    setSkillEnabled: unavailable,
    configs: async () => clone(configDocs),
    saveConfig: unavailable,
    saveSettings: async (settings) => {
      bootstrap.settings = clone(settings);
      return clone(settings);
    },
    saveProfile: unavailable,
    deleteProfile: unavailable,
    saveSecret: unavailable,
    deleteSecret: unavailable,
    models: async () => ({
      models: [
        {
          id: 'sample/model-free',
          name: 'Sample community model',
          contextWindow: 131072,
          free: true,
          inputPrice: 0,
          outputPrice: 0,
        },
        {
          id: 'sample/model-pro',
          name: 'Sample reasoning model',
          contextWindow: 200000,
          free: false,
        },
      ],
      source: 'Demonstration catalog',
      verifiedAt: NOW.toISOString(),
      latencyMs: 0,
      warnings: [
        'Illustrative entries only. Connect a provider in the desktop app for its live catalog.',
      ],
    }),
    probe: unavailable,
    launch: unavailable,
    terminals: async () => [],
    terminalSnapshot: unavailable,
    terminalWrite: unavailable,
    terminalResize: unavailable,
    terminalClose: unavailable,
    onTerminal: () => () => {},
    pickDirectory: unavailable,
    revealPath: unavailable,
    openExternal: unavailable,
    exportSession: unavailable,
    proxyStart: unavailable,
    proxyAuthenticate: unavailable,
    proxyMonitor: unavailable,
  };
}
