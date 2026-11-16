import { execFile, spawn, type ChildProcess } from 'node:child_process';
import { access } from 'node:fs/promises';
import { createServer } from 'node:net';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { promisify } from 'node:util';
import { remote } from 'webdriverio';
import type { LocalFixture } from './desktop-fixture';

export type Driver = Awaited<ReturnType<typeof remote>>;
export type UiElement = Awaited<ReturnType<Driver['$']>>;
export type UiScope = Driver | UiElement;

const execute = promisify(execFile);

async function windowsDebugPolicy(
  binary: string,
  browserArguments: string,
  capture: (data: Buffer) => void,
): Promise<() => Promise<void>> {
  const powershell = async (script: string, environment: Record<string, string> = {}) =>
    await execute('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', script], {
      env: { ...process.env, ...environment },
      windowsHide: true,
      timeout: 10000,
      maxBuffer: 65536,
    });
  const identity = await powershell(
    '([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)',
  );
  if (identity.stdout.trim().toLowerCase() !== 'true') return async () => undefined;
  if (process.env.GITHUB_ACTIONS !== 'true' || process.env.RUNNER_ENVIRONMENT !== 'github-hosted')
    throw new Error(
      'WebView2 ignores environment debugging overrides in elevated processes. Run local desktop tests from a non-administrator terminal. Temporary machine policy is configured only on GitHub-hosted Windows runners.',
    );

  const environment = { AGENT_DESK_POLICY_NAME: path.basename(binary) };
  const prefix = [
    "$ErrorActionPreference = 'Stop'",
    '$root = [Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]::LocalMachine, [Microsoft.Win32.RegistryView]::Registry64)',
    "$policyPath = 'SOFTWARE\\Policies\\Microsoft\\Edge\\WebView2\\AdditionalBrowserArguments'",
    '$name = $env:AGENT_DESK_POLICY_NAME',
  ].join('; ');
  const previous = await powershell(
    `${prefix};
    $key = $root.OpenSubKey($policyPath, $false)
    try {
      $snapshot = [pscustomobject]@{ keyExisted = ($null -ne $key); existed = $false; kind = $null; value = $null }
      if ($key -and $key.GetValueNames() -contains $name) {
        $snapshot.existed = $true
        $snapshot.kind = $key.GetValueKind($name).ToString()
        $snapshot.value = $key.GetValue($name, $null, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
      }
      [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes([System.Management.Automation.PSSerializer]::Serialize($snapshot)))
    } finally {
      if ($key) { $key.Dispose() }
      $root.Dispose()
    }`,
    environment,
  );
  const snapshot = previous.stdout.trim();
  if (!snapshot) throw new Error('Could not preserve the existing WebView2 debugging policy.');
  let restored = false;
  const restore = async (): Promise<void> => {
    if (restored) return;
    await powershell(
      `${prefix};
      $snapshot = [System.Management.Automation.PSSerializer]::Deserialize([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($env:AGENT_DESK_POLICY_SNAPSHOT)))
      $key = $root.OpenSubKey($policyPath, $true)
      try {
        if ($snapshot.existed) {
          if (-not $key) { $key = $root.CreateSubKey($policyPath) }
          $value = $snapshot.value
          switch ($snapshot.kind) {
            'Binary' { $value = [byte[]]$value }
            'None' { $value = [byte[]]$value }
            'DWord' { $value = [int]$value }
            'QWord' { $value = [long]$value }
            'MultiString' { $value = [string[]]$value }
            'String' { $value = [string]$value }
            'ExpandString' { $value = [string]$value }
            default { throw 'Unsupported original WebView2 policy value type.' }
          }
          $key.SetValue($name, $value, [Microsoft.Win32.RegistryValueKind][Enum]::Parse([Microsoft.Win32.RegistryValueKind], $snapshot.kind))
        } elseif ($key) {
          $key.DeleteValue($name, $false)
        }
        $removeEmptyKey = -not $snapshot.keyExisted -and $key -and $key.ValueCount -eq 0 -and $key.SubKeyCount -eq 0
        if ($key) { $key.Dispose(); $key = $null }
        if ($removeEmptyKey) { $root.DeleteSubKey($policyPath, $false) }
      } finally {
        if ($key) { $key.Dispose() }
        $root.Dispose()
      }`,
      { ...environment, AGENT_DESK_POLICY_SNAPSHOT: snapshot },
    );
    restored = true;
    capture(Buffer.from('Restored the prior app-scoped WebView2 debugging policy.\n'));
  };
  try {
    await powershell(
      `${prefix};
      $key = $root.CreateSubKey($policyPath)
      try { $key.SetValue($name, $env:AGENT_DESK_POLICY_ARGUMENTS, [Microsoft.Win32.RegistryValueKind]::String) }
      finally { $key.Dispose(); $root.Dispose() }`,
      { ...environment, AGENT_DESK_POLICY_ARGUMENTS: browserArguments },
    );
  } catch (cause) {
    await restore();
    throw cause;
  }
  capture(
    Buffer.from('Configured temporary app-scoped HKLM WebView2 debugging on the elevated hosted runner.\n'),
  );
  return restore;
}

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
  if (!child.pid || child.exitCode !== null || child.signalCode !== null) return;
  if (process.platform === 'win32') {
    try {
      await execute('taskkill', ['/pid', String(child.pid), '/T', '/F'], {
        windowsHide: true,
        timeout: 5000,
        maxBuffer: 4096,
      });
    } catch (cause) {
      if (child.exitCode === null && child.signalCode === null)
        throw new Error(`Could not terminate native test process ${child.pid}.`, { cause });
    }
  } else {
    try {
      process.kill(-child.pid, 'SIGTERM');
    } catch {
      child.kill('SIGTERM');
    }
  }
}

async function windowsProcessState(child: ChildProcess): Promise<string> {
  const state = `pid=${child.pid ?? 'not started'} exit=${child.exitCode} signal=${child.signalCode}`;
  if (!child.pid) return state;
  try {
    const { stdout } = await execute(
      'powershell.exe',
      [
        '-NoProfile',
        '-NonInteractive',
        '-Command',
        [
          '$all = @(Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId, Name, CommandLine)',
          '$owned = [System.Collections.Generic.HashSet[uint32]]::new()',
          '[void]$owned.Add([uint32]$env:AGENT_DESK_DIAGNOSTIC_PID)',
          'do { $changed = $false; foreach ($entry in $all) { if ($owned.Contains($entry.ParentProcessId) -and $owned.Add($entry.ProcessId)) { $changed = $true } } } while ($changed)',
          "$processes = @($all | Where-Object { $owned.Contains($_.ProcessId) } | ForEach-Object { [pscustomobject]@{ ProcessId = $_.ProcessId; ParentProcessId = $_.ParentProcessId; Name = $_.Name; DebugPort = [regex]::Match([string]$_.CommandLine, '--remote-debugging-port=(\\d+)').Groups[1].Value; DebugPipe = ([string]$_.CommandLine -match '(?:^|\\s)--remote-debugging-pipe(?:\\s|$)') } })",
          '$listeners = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $owned.Contains($_.OwningProcess) } | Select-Object LocalAddress, LocalPort, OwningProcess)',
          'ConvertTo-Json -Compress -Depth 4 -InputObject @{ processes = $processes; listeners = $listeners }',
        ].join('; '),
      ],
      {
        env: { ...process.env, AGENT_DESK_DIAGNOSTIC_PID: String(child.pid) },
        windowsHide: true,
        timeout: 5000,
        maxBuffer: 65536,
      },
    );
    return `${state}\nOwned process transport: ${stdout.trim()}`;
  } catch {
    return state;
  }
}

async function launchWindowsWebview(
  binary: string,
  fixture: LocalFixture,
  capture: (data: Buffer) => void,
): Promise<{ process: ChildProcess; debuggerAddress: string; restorePolicy(): Promise<void> }> {
  const port = await unusedPort();
  const debuggerAddress = `127.0.0.1:${port}`;
  const browserArguments = `--remote-debugging-port=${port} --remote-debugging-address=127.0.0.1`;
  const restorePolicy = await windowsDebugPolicy(binary, browserArguments, capture);
  let child: ChildProcess | undefined;
  try {
    child = spawn(binary, [], {
      env: {
        ...fixture.env,
        TAURI_AUTOMATION: 'true',
        TAURI_WEBVIEW_AUTOMATION: 'true',
        WEBVIEW2_USER_DATA_FOLDER: path.join(fixture.data, 'webview'),
        WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: browserArguments,
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let startupError: Error | undefined;
    child.stdout?.on('data', capture);
    child.stderr?.on('data', capture);
    child.once('error', (error) => {
      startupError = error;
    });
    capture(
      Buffer.from(`Windows app started with its isolated fixture WebView2 profile; pid=${child.pid}.\n`),
    );
    const deadline = Date.now() + 30000;
    let endpointStatus = 'No response';
    while (Date.now() < deadline) {
      if (startupError) throw startupError;
      if (child.exitCode !== null || child.signalCode !== null)
        throw new Error('The Windows app exited before its WebView2 became ready.');
      const version = await fetch(`http://${debuggerAddress}/json/version`, {
        signal: AbortSignal.timeout(1000),
      })
        .then(async (response) => {
          endpointStatus = `HTTP ${response.status}`;
          return response.ok
            ? ((await response.json()) as { Browser?: string; webSocketDebuggerUrl?: string })
            : undefined;
        })
        .catch((cause: { name?: string; cause?: { code?: string } }) => {
          endpointStatus = cause.cause?.code ?? cause.name ?? 'Transport error';
          return undefined;
        });
      if (version?.webSocketDebuggerUrl) {
        capture(
          Buffer.from(`Windows WebView2 is ready: ${version.Browser ?? 'version unavailable'}.\n`),
        );
        return { process: child, debuggerAddress, restorePolicy };
      }
      await delay(200);
    }
    throw new Error(
      `The Windows app did not expose its loopback WebView2 endpoint within 30 seconds (${endpointStatus}).`,
    );
  } catch (cause) {
    const state = child ? await windowsProcessState(child) : 'Windows app was not started.';
    try {
      if (child) await terminateDriver(child);
    } finally {
      await restorePolicy();
    }
    throw new Error(`${cause instanceof Error ? cause.message : String(cause)}\n${state}`);
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
  let windowsApp: ChildProcess | undefined;
  let restoreWindowsPolicy: (() => Promise<void>) | undefined;
  const close = async (): Promise<void> => {
    try {
      await browser?.deleteSession().catch(() => undefined);
    } finally {
      try {
        if (windowsApp) await terminateDriver(windowsApp);
      } finally {
        try {
          await terminateDriver(child);
        } finally {
          await restoreWindowsPolicy?.();
        }
      }
    }
  };
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
      'tauri:options'?: { application: string };
      'ms:edgeChromium'?: boolean;
    } = {
      'wdio:enforceWebDriverClassic': true,
    };
    if (process.platform === 'win32') {
      const webview = await launchWindowsWebview(binary, fixture, capture);
      windowsApp = webview.process;
      restoreWindowsPolicy = webview.restorePolicy;
      capabilities.browserName = 'webview2';
      capabilities['ms:edgeChromium'] = true;
      capabilities['ms:edgeOptions'] = { debuggerAddress: webview.debuggerAddress };
    } else {
      capabilities['tauri:options'] = { application: binary };
    }
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
      close,
    };
  } catch (cause) {
    if (windowsApp) capture(Buffer.from(`${await windowsProcessState(windowsApp)}\n`));
    await close();
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

export async function fillMultiline(
  browser: Driver,
  element: UiElement,
  value: string,
): Promise<void> {
  const [first, ...lines] = value.split('\n');
  await element.setValue(first);
  for (const line of lines) {
    await browser.keys('Enter');
    if (line) await element.addValue(line);
  }
  const entered = await element.getValue();
  if (entered !== value)
    throw new Error('Native textarea input did not preserve the supplied text.');
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
