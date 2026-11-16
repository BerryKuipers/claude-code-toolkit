import { access, readFile, realpath, stat } from 'node:fs/promises';
import { constants } from 'node:fs';
import { delimiter, dirname, extname, isAbsolute, join, resolve } from 'node:path';
import { homedir } from 'node:os';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import type { AgentId, AgentInstall, AppSettings } from '../shared/types';

const execFileAsync = promisify(execFile);

export const AGENT_LABELS: Record<AgentId, string> = {
  claude: 'Claude Code',
  codex: 'Codex',
  gemini: 'Gemini CLI',
  antigravity: 'Antigravity',
};

export interface Executable {
  file: string;
  prefixArgs: string[];
}

function searchPaths(env: NodeJS.ProcessEnv, home: string): string[] {
  const pathEntry = Object.entries(env).find(([key]) => key.toLowerCase() === 'path')?.[1] ?? '';
  return [
    ...new Set([
      ...pathEntry.split(delimiter).filter(Boolean),
      join(home, '.local', 'bin'),
      join(home, '.bun', 'bin'),
      join(home, '.npm-global', 'bin'),
      ...(process.platform === 'win32'
        ? [
            join(env.APPDATA ?? join(home, 'AppData', 'Roaming'), 'npm'),
            join(home, 'AppData', 'Local', 'Microsoft', 'WinGet', 'Links'),
          ]
        : ['/opt/homebrew/bin', '/usr/local/bin', '/usr/bin']),
    ]),
  ];
}

export async function findExecutable(
  command: string,
  env: NodeJS.ProcessEnv = process.env,
  home = homedir(),
): Promise<string> {
  if (!command || command.includes('\0') || command.includes('\n'))
    throw new Error('Choose an executable path or command name, without arguments.');
  const direct = isAbsolute(command) || command.includes('/') || command.includes('\\');
  const roots = direct ? [''] : searchPaths(env, home);
  const extensions =
    process.platform === 'win32' && !extname(command) ? ['.exe', '.com', '.cmd', '.bat', ''] : [''];
  for (const root of roots) {
    for (const extension of extensions) {
      const candidate = direct ? resolve(command + extension) : join(root, command + extension);
      try {
        await access(candidate, process.platform === 'win32' ? constants.F_OK : constants.X_OK);
        if ((await stat(candidate)).isFile()) return await realpath(candidate);
      } catch (error) {
        if (!['ENOENT', 'ENOTDIR', 'EACCES'].includes((error as NodeJS.ErrnoException).code ?? ''))
          throw error;
      }
    }
  }
  throw new Error(
    `Executable '${command}' was not found. Install it or choose its full path in Settings.`,
  );
}

export function npmShimTarget(content: string, shimPath: string): string | undefined {
  const match = content.match(/"%dp0%[\\/]([^"\r\n]+\.(?:[cm]?js|exe))"/i);
  if (!match) return undefined;
  const relative = match[1].replace(/[\\/]/g, '/');
  if (relative.split('/').includes('..') || !relative.toLowerCase().startsWith('node_modules/'))
    return undefined;
  return resolve(dirname(shimPath), relative);
}

export async function resolveExecutable(
  command: string,
  env: NodeJS.ProcessEnv = process.env,
  home = homedir(),
): Promise<Executable> {
  const file = await findExecutable(command, env, home);
  if (process.platform === 'win32' && /\.(cmd|bat)$/i.test(file)) {
    const target = npmShimTarget(await readFile(file, 'utf8'), file);
    if (!target)
      throw new Error(
        `The launcher '${file}' is not a supported npm shim. Select the native executable or JavaScript CLI entry point in Settings.`,
      );
    await access(target);
    if (/\.exe$/i.test(target)) return { file: target, prefixArgs: [] };
    let node: string;
    try {
      node = await findExecutable(join(dirname(file), 'node.exe'), env, home);
    } catch {
      node = await findExecutable('node', env, home);
    }
    return { file: node, prefixArgs: [target] };
  }
  if (/\.[cm]?js$/i.test(file))
    return { file: await findExecutable('node', env, home), prefixArgs: [file] };
  return { file, prefixArgs: [] };
}

export async function detectAgents(settings: AppSettings, home: string): Promise<AgentInstall[]> {
  return await Promise.all(
    (Object.keys(AGENT_LABELS) as AgentId[]).map(async (id) => {
      const command = settings.agentCommands[id];
      try {
        const executable = await resolveExecutable(command, process.env, home);
        let version: string | undefined;
        let error: string | undefined;
        try {
          const result = await execFileAsync(
            executable.file,
            [...executable.prefixArgs, '--version'],
            { timeout: 5000, windowsHide: true, maxBuffer: 65536 },
          );
          version = result.stdout
            .trim()
            .split('\n')[0]
            ?.replace(/\x1b\[[0-9;]*m/g, '')
            .slice(0, 160);
        } catch {
          error = 'Executable found; its version command did not finish successfully.';
        }
        return {
          id,
          label: AGENT_LABELS[id],
          command,
          available: true,
          path: executable.file,
          version,
          error,
        };
      } catch (error) {
        return {
          id,
          label: AGENT_LABELS[id],
          command,
          available: false,
          error: (error as Error).message,
        };
      }
    }),
  );
}
