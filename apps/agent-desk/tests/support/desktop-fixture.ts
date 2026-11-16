import { chmod, mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { createServer, type Server } from 'node:http';
import os from 'node:os';
import path from 'node:path';

export const fixtureSessionId = '12345678-1234-4234-8234-123456789abc';

export interface LocalFixture {
  home: string;
  data: string;
  project: string;
  claude: string;
  invocations: string;
  readiness: string;
  gatewayUrl: string;
  env: Record<string, string>;
  requests: Array<{ method: string; url: string }>;
  cleanup(): Promise<void>;
}

const fakeAgent = String.raw`
const fs = require('node:fs');
const readline = require('node:readline');
const args = process.argv.slice(2);
if (args.includes('--version')) {
  process.stdout.write('Agent Desk fixture CLI 1.0.0\n');
  process.exit(0);
}
if (args[0] === 'app-server') {
  const input = readline.createInterface({ input: process.stdin, terminal: false });
  input.on('line', line => {
    const request = JSON.parse(line);
    if (request.id === undefined) return;
    if (request.method === 'thread/list') {
      fs.appendFileSync(process.env.AGENT_DESK_FIXTURE_READINESS, JSON.stringify({ method: request.method, pid: process.pid, requestedAt: new Date().toISOString() }) + '\n');
    }
    const result = request.method === 'initialize'
      ? { userAgent: 'agent-desk-fixture' }
      : { data: [], nextCursor: null };
    process.stdout.write(JSON.stringify({ id: request.id, result }) + '\n');
  });
} else {
  const resume = args.indexOf('--resume');
  const nativeId = resume >= 0 ? args[resume + 1] : 'new';
  fs.appendFileSync(process.env.AGENT_DESK_FIXTURE_INVOCATIONS, JSON.stringify({ pid: process.pid, args, cwd: process.cwd(), nativeId }) + '\n');
  process.stdout.write('FAKE_AGENT_READY resume=' + nativeId + '\r\n');
  let statusCount = 0;
  let input = '';
  if (process.stdin.isTTY) process.stdin.setRawMode(true);
  process.stdin.setEncoding('utf8');
  process.stdin.resume();
  process.stdin.on('data', chunk => {
    for (const char of chunk) {
      if (char === '\u0003') process.exit(0);
      if (char === '\r' || char === '\n') {
        const command = input.trim();
        input = '';
        if (!command) continue;
        if (command === '/status') process.stdout.write('\r\nFAKE_STATUS_' + (++statusCount) + ' pid=' + process.pid + '\r\n');
        else if (command === '/exit') process.exit(0);
        else process.stdout.write('\r\nFAKE_ECHO ' + command + '\r\n');
      } else if (char === '\u007f' || char === '\b') {
        input = input.slice(0, -1);
      } else {
        input += char;
      }
    }
  });
}
`;

async function closeServer(server: Server): Promise<void> {
  server.closeAllConnections();
  await new Promise<void>((resolve, reject) =>
    server.close((error) => (error ? reject(error) : resolve())),
  );
}

export async function createDesktopFixture(): Promise<LocalFixture> {
  const temporary = await mkdtemp(path.join(os.tmpdir(), 'agent-desk-desktop-'));
  const home = path.join(temporary, 'home');
  const data = path.join(temporary, 'app-data');
  const project = path.join(temporary, 'projects', 'desktop-fixture');
  const claude = path.join(temporary, 'agent-config', 'claude');
  const codex = path.join(temporary, 'agent-config', 'codex');
  const geminiParent = path.join(temporary, 'agent-config', 'google');
  const executable = path.join(temporary, 'fixture-agent.cjs');
  const invocations = path.join(temporary, 'invocations.jsonl');
  const readiness = path.join(temporary, 'readiness.jsonl');
  const requests: LocalFixture['requests'] = [];
  let serverListening = false;
  const server = createServer((request, response) => {
    requests.push({ method: request.method ?? '', url: request.url ?? '' });
    response.setHeader('content-type', 'application/json');
    if (request.method !== 'GET') {
      response.writeHead(405).end('{"error":"This fixture never generates model output."}');
    } else if (request.url === '/healthz') {
      response.end('{"ok":true}');
    } else if (request.url === '/v1/models') {
      response.end(
        JSON.stringify({
          data: [
            {
              id: 'fixture/coder',
              display_name: 'Fixture coder',
              context_length: 128000,
              pricing: { prompt: '0', completion: '0' },
            },
            {
              id: 'fixture/reasoner',
              display_name: 'Fixture reasoner',
              context_length: 256000,
              pricing: { prompt: '0.000001', completion: '0.000002' },
            },
          ],
          has_more: false,
        }),
      );
    } else if (request.url === '/monitor') {
      response.end(
        '{"version":1,"snapshot":{"sessions":[],"active_requests":[],"recent_requests":[]}}',
      );
    } else {
      response.writeHead(404).end('{"error":"Unknown fixture route"}');
    }
  });
  try {
    for (const directory of [
      home,
      data,
      project,
      claude,
      codex,
      path.join(geminiParent, '.gemini'),
    ])
      await mkdir(directory, { recursive: true });
    await writeFile(executable, fakeAgent);
    await chmod(executable, 0o755);
    await writeFile(invocations, '');
    await writeFile(readiness, '');
    await writeFile(
      path.join(claude, 'settings.json'),
      JSON.stringify(
        {
          model: 'fixture-native',
          effortLevel: 'medium',
          statusLine: { type: 'command', command: 'fixture-status-line' },
          fixtureUnrecognizedSetting: { keep: true },
        },
        null,
        2,
      ),
    );
    const settings = {
      fontSize: 13,
      terminalScrollback: 10000,
      defaultProfileId: 'claude-native',
      historyRoots: [],
      skillDirectories: [],
      scanOnStart: true,
      theme: 'light' as const,
      projects: [project],
      agentCommands: {
        claude: executable,
        codex: executable,
        gemini: executable,
        antigravity: executable,
      },
      proxyCommand: executable,
      autoRefreshSeconds: 0,
    };
    await writeFile(path.join(data, 'settings.json'), JSON.stringify(settings));
    const transcriptDirectory = path.join(claude, 'projects', 'fixture-project');
    await mkdir(transcriptDirectory, { recursive: true });
    const timestamp = new Date().toISOString();
    for (const [id, title, prompt] of [
      [fixtureSessionId, 'Desktop resume fixture', 'Continue the desktop layout'],
      [
        '87654321-4321-4321-8321-123456789abc',
        'Unrelated fixture conversation',
        'Inspect another project',
      ],
    ]) {
      const records = [
        {
          type: 'user',
          uuid: `${id}-user`,
          parentUuid: null,
          sessionId: id,
          cwd: project,
          timestamp,
          message: { role: 'user', content: prompt },
        },
        {
          type: 'assistant',
          uuid: `${id}-assistant`,
          parentUuid: `${id}-user`,
          sessionId: id,
          cwd: project,
          timestamp,
          message: {
            role: 'assistant',
            model: 'fixture-model',
            content: [{ type: 'text', text: 'Recorded fixture answer with a working transcript.' }],
          },
        },
        { type: 'custom-title', customTitle: title },
      ];
      await writeFile(
        path.join(transcriptDirectory, `${id}.jsonl`),
        records.map((record) => JSON.stringify(record)).join('\n') + '\n',
      );
    }
    await new Promise<void>((resolve, reject) => {
      server.once('error', reject);
      server.listen(0, '127.0.0.1', () => {
        serverListening = true;
        resolve();
      });
    });
    const address = server.address();
    if (!address || typeof address === 'string')
      throw new Error('The fixture gateway did not receive a port.');
    const gatewayUrl = `http://127.0.0.1:${address.port}`;
    const env = Object.fromEntries(
      Object.entries(process.env).filter(
        (entry): entry is [string, string] =>
          typeof entry[1] === 'string' &&
          !/(?:API_KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)/i.test(entry[0]),
      ),
    );
    delete env.ELECTRON_RUN_AS_NODE;
    delete env.AGENT_DESK_DEV_URL;
    Object.assign(env, {
      AGENT_DESK_HOME: home,
      AGENT_DESK_DATA_DIR: data,
      AGENT_DESK_FIXTURE_INVOCATIONS: invocations,
      AGENT_DESK_FIXTURE_READINESS: readiness,
      CLAUDE_CONFIG_DIR: claude,
      CODEX_HOME: codex,
      GEMINI_CLI_HOME: geminiParent,
    });
    return {
      home,
      data,
      project,
      claude,
      invocations,
      readiness,
      gatewayUrl,
      requests,
      env,
      cleanup: async () => {
        if (serverListening) {
          await closeServer(server);
          serverListening = false;
        }
        await rm(temporary, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
      },
    };
  } catch (cause) {
    if (serverListening) await closeServer(server);
    await rm(temporary, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
    throw cause;
  }
}
