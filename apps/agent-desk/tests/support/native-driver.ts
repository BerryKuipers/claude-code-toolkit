import { spawn, type ChildProcess } from 'node:child_process';
import { access } from 'node:fs/promises';
import { createServer } from 'node:net';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { remote } from 'webdriverio';
import type { LocalFixture } from './desktop-fixture';

export type Driver = Awaited<ReturnType<typeof remote>>;
export type UiElement = Awaited<ReturnType<Driver['$']>>;
export type UiScope = Driver | UiElement;

async function unusedPort(): Promise<number> {
  const server = createServer();
  await new Promise<void>((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('No native driver port available.');
  await new Promise<void>((resolve, reject) =>
    server.close((error) => (error ? reject(error) : resolve())),
  );
  return address.port;
}

export async function terminateDriver(child: ChildProcess): Promise<void> {
  if (!child.pid) return;
  if (process.platform === 'win32') {
    await new Promise<void>((resolve) => {
      const task = spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], { stdio: 'ignore' });
      task.once('error', () => resolve());
      task.once('exit', () => resolve());
    });
  } else {
    try {
      process.kill(-child.pid, 'SIGTERM');
    } catch {
      child.kill('SIGTERM');
    }
  }
}

export async function launchNativeDriver(fixture: LocalFixture): Promise<{
  browser: Driver;
  output(): string;
  close(): Promise<void>;
}> {
  const appDirectory = path.resolve(import.meta.dirname, '../..');
  const binary =
    process.env.AGENT_DESK_BINARY ??
    path.join(
      appDirectory,
      'src-tauri',
      'target',
      'release',
      process.platform === 'win32' ? 'agent-desk.exe' : 'agent-desk',
    );
  await access(binary);
  const port = await unusedPort();
  let output = '';
  let startupError: Error | undefined;
  const driverArgs = ['--port', String(port)];
  if (process.env.TAURI_NATIVE_DRIVER)
    driverArgs.push('--native-driver', process.env.TAURI_NATIVE_DRIVER);
  const child = spawn(process.env.TAURI_DRIVER ?? 'tauri-driver', driverArgs, {
    env: fixture.env,
    detached: process.platform !== 'win32',
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  const capture = (data: Buffer): void => {
    output = (output + data.toString()).slice(-40000);
  };
  child.stdout?.on('data', capture);
  child.stderr?.on('data', capture);
  child.once('error', (error) => {
    startupError = error;
  });
  let browser: Driver | undefined;
  try {
    const deadline = Date.now() + 30000;
    let ready = false;
    while (Date.now() < deadline) {
      if (startupError) throw startupError;
      if (child.exitCode !== null) throw new Error(`tauri-driver exited: ${output}`);
      try {
        ready = (
          await fetch(`http://127.0.0.1:${port}/status`, {
            signal: AbortSignal.timeout(1000),
          })
        ).ok;
      } catch {
        ready = false;
      }
      if (ready) break;
      await delay(100);
    }
    if (!ready) throw new Error(`tauri-driver did not start: ${output}`);
    const capabilities: WebdriverIO.Capabilities & {
      'tauri:options': { application: string };
    } = {
      'tauri:options': { application: binary },
      'wdio:enforceWebDriverClassic': true,
    };
    browser = await remote({
      hostname: '127.0.0.1',
      port,
      path: '/',
      capabilities,
      logLevel: 'error',
      connectionRetryTimeout: 45000,
      connectionRetryCount: 0,
    });
    await browser.setTimeout({ implicit: 0, script: 15000, pageLoad: 30000 });
    return {
      browser,
      output: () => output,
      close: async () => {
        await browser?.deleteSession().catch(() => undefined);
        await terminateDriver(child);
      },
    };
  } catch (cause) {
    await browser?.deleteSession().catch(() => undefined);
    await terminateDriver(child);
    throw new Error(`${cause instanceof Error ? cause.message : String(cause)}\n${output}`);
  }
}

export async function visible(
  browser: Driver,
  selector: string,
  scope: UiScope = browser,
): Promise<UiElement> {
  let result: UiElement | undefined;
  await browser.waitUntil(
    async () => {
      const matches = await scope.$$(selector);
      const shown: UiElement[] = [];
      for (const element of matches) {
        if (await element.isDisplayed()) shown.push(element);
      }
      if (shown.length > 1) throw new Error(`Ambiguous visible selector: ${selector}`);
      result = shown[0];
      return Boolean(result);
    },
    { timeout: 12000, interval: 100, timeoutMsg: `No visible element: ${selector}` },
  );
  return result!;
}

export async function visibleText(browser: Driver, selector: string): Promise<string> {
  return await (await visible(browser, selector)).getText();
}

export async function field(
  browser: Driver,
  name: string,
  scope: UiScope = browser,
): Promise<UiElement> {
  const direct = await scope.$$(`[aria-label="${name}"]`);
  for (const element of direct) if (await element.isDisplayed()) return element;
  const label = await visible(browser, `label=${name}`, scope);
  const control = await label.getAttribute('for');
  if (!control) throw new Error(`Field label '${name}' has no associated control.`);
  return await visible(browser, `[id="${control}"]`, scope);
}

export async function button(
  browser: Driver,
  name: string | RegExp,
  scope: UiScope = browser,
): Promise<UiElement> {
  let found: UiElement | undefined;
  await browser.waitUntil(
    async () => {
      const matches: UiElement[] = [];
      for (const element of await scope.$$('button')) {
        if (!(await element.isDisplayed())) continue;
        const label = await element.getComputedLabel();
        if (typeof name === 'string' ? label === name : name.test(label)) matches.push(element);
      }
      if (matches.length > 1) throw new Error(`Ambiguous button name: ${name}`);
      found = matches[0];
      return Boolean(found);
    },
    { timeout: 12000, interval: 100, timeoutMsg: `No visible button: ${name}` },
  );
  return found!;
}

export async function clickButton(
  browser: Driver,
  name: string | RegExp,
  scope: UiScope = browser,
): Promise<void> {
  await (await button(browser, name, scope)).click();
}

export async function enterTerminal(browser: Driver, command: string): Promise<void> {
  await browser.execute(() => {
    const host = [...document.querySelectorAll<HTMLElement>('.terminal-surface')].find(
      (element) => element.getClientRects().length > 0,
    );
    const input = host?.querySelector<HTMLTextAreaElement>('.xterm-helper-textarea');
    if (!input) throw new Error('The live terminal input was not found.');
    input.focus();
  });
  await browser.keys(command);
  await browser.keys('Enter');
}
