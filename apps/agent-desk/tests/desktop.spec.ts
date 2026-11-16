import { test as base, expect } from '@playwright/test';
import { readFile, readdir, realpath, writeFile } from 'node:fs/promises';
import path from 'node:path';
import type { ProviderProfile, TerminalInfo } from '../src/shared/types';
import {
  createDesktopFixture,
  fixtureSessionId,
  type LocalFixture,
} from './support/desktop-fixture';
import {
  button,
  clickButton,
  enterTerminal,
  field,
  fillMultiline,
  launchNativeDriver,
  visible,
  visibleText,
  type Driver,
  type UiElement,
} from './support/native-driver';

interface NativeFixture extends LocalFixture {
  browser: Driver;
}

const test = base.extend<{ desktop: NativeFixture }>({
  desktop: async ({}, use, testInfo) => {
    const fixture = await createDesktopFixture();
    let session: Awaited<ReturnType<typeof launchNativeDriver>> | undefined;
    try {
      session = await launchNativeDriver(fixture);
      const browser = session.browser;
      await visible(browser, '[aria-label="Search sessions"]');
      await button(browser, /Desktop resume fixture/);
      const runtime = await browser.execute(() => ({
        hasBridge: Boolean(window.desk),
        tauri: '__TAURI_INTERNALS__' in window,
        nodeAvailable: typeof (window as unknown as { require?: unknown }).require !== 'undefined',
        origin: location.origin,
      }));
      expect(runtime).toMatchObject({ hasBridge: true, tauri: true, nodeAvailable: false });
      expect(runtime.origin).not.toMatch(/^https?:\/\/(?:localhost|127\.0\.0\.1):\d+/);
      await browser.execute(() => {
        const diagnostics = window as unknown as { desktopErrors: string[] };
        diagnostics.desktopErrors = [];
        window.addEventListener('error', (event) => diagnostics.desktopErrors.push(event.message));
        window.addEventListener('unhandledrejection', (event) =>
          diagnostics.desktopErrors.push(String(event.reason)),
        );
      });
      await use({ ...fixture, browser });
      expect(
        await browser.execute(
          () => (window as unknown as { desktopErrors: string[] }).desktopErrors,
        ),
        'renderer JavaScript errors',
      ).toEqual([]);
    } finally {
      if (session) {
        const screenshot = testInfo.outputPath('desktop.png');
        await session.browser
          .saveScreenshot(screenshot)
          .then(() =>
            testInfo.attach('Native desktop', { path: screenshot, contentType: 'image/png' }),
          )
          .catch(() => undefined);
        if (testInfo.status !== testInfo.expectedStatus) {
          const source = testInfo.outputPath('page-source.html');
          await session.browser
            .getPageSource()
            .then((html) => writeFile(source, html))
            .then(() =>
              testInfo.attach('WebView source', { path: source, contentType: 'text/html' }),
            )
            .catch(() => undefined);
        }
        await testInfo.attach('Native driver output', {
          body: session.output(),
          contentType: 'text/plain',
        });
        await session.browser
          .execute(async () => {
            for (const terminal of await window.desk.terminals())
              await window.desk.terminalClose(terminal.id);
          })
          .catch(() => undefined);
        await session.close();
      }
      await fixture.cleanup();
    }
  },
});

async function navigation(browser: Driver, name: string): Promise<void> {
  const nav = await visible(browser, 'nav[aria-label="Main navigation"]');
  await clickButton(browser, new RegExp(`^${name}`), nav);
}

async function dialog(browser: Driver, title: string): Promise<UiElement> {
  const element = await visible(browser, '[role="dialog"]');
  expect(await element.$('h2').getText()).toBe(title);
  return element;
}

async function terminals(browser: Driver): Promise<TerminalInfo[]> {
  return await browser.execute(async () => await window.desk.terminals());
}

async function profileCard(browser: Driver): Promise<UiElement> {
  let result: UiElement | undefined;
  await browser.waitUntil(
    async () => {
      for (const article of await browser.$$('article')) {
        if (
          (await article.isDisplayed()) &&
          (await article.getText()).includes('Desktop mock gateway')
        ) {
          result = article;
          return true;
        }
      }
      return false;
    },
    { timeout: 10000, interval: 100, timeoutMsg: 'The saved connection card was not shown.' },
  );
  return result!;
}

test('finds and resumes a local session through the real PTY, preserving it across views', async ({
  desktop,
}, testInfo) => {
  const { browser, invocations, project } = desktop;
  const search = await field(browser, 'Search sessions');
  await search.setValue('not-a-fixture');
  await expect
    .poll(() => visibleText(browser, '.session-list .list-empty strong'))
    .toBe('No matching sessions');
  expect(await visibleText(browser, '.library-footer > span:first-child')).toBe('0 sessions');
  await search.setValue('Desktop resume fixture');
  await (await field(browser, 'Filter sessions by agent')).selectByAttribute('value', 'claude');
  await clickButton(browser, /Desktop resume fixture/);
  await expect
    .poll(() => visibleText(browser, '[aria-label="Session conversation"]'))
    .toContain('Recorded fixture answer');
  await clickButton(browser, 'Resume session');
  const live = await visible(browser, '[aria-label="Live agent workspace"]');
  const terminalText = async (): Promise<string> =>
    String((await live.$('.xterm-accessibility-tree').getProperty('textContent')) ?? '');
  await expect.poll(terminalText).toContain('FAKE_AGENT_READY');
  const original = (await terminals(browser))[0];
  expect(original.status).toBe('running');
  const invocation = JSON.parse((await readFile(invocations, 'utf8')).trim().split('\n').at(-1)!);
  expect(invocation.nativeId).toBe(fixtureSessionId);
  expect(await realpath(invocation.cwd)).toBe(await realpath(project));
  await enterTerminal(browser, '/status');
  await expect.poll(terminalText).toContain('FAKE_STATUS_1');
  await navigation(browser, 'Skills');
  expect(await visibleText(browser, 'h1*=Skills')).toMatch(/^Skills/);
  await navigation(browser, 'Workspace');
  await expect.poll(terminalText).toContain('FAKE_STATUS_1');
  await enterTerminal(browser, '/status');
  await expect.poll(terminalText).toContain('FAKE_STATUS_2');
  expect((await terminals(browser))[0].id).toBe(original.id);
  expect((await readFile(invocations, 'utf8')).trim().split('\n')).toHaveLength(1);
  const screenshot = testInfo.outputPath('live-terminal.png');
  await browser.saveScreenshot(screenshot);
  await testInfo.attach('Native terminal after resume', {
    path: screenshot,
    contentType: 'image/png',
  });
  await (await visible(browser, '.terminal-tabs button[aria-label^="Close "]', live)).click();
  await clickButton(browser, 'Stop and close', await dialog(browser, 'Stop this running session?'));
  await expect.poll(async () => (await terminals(browser)).length).toBe(0);
});

test('creates and edits a skill, then disables and restores its original file', async ({
  desktop,
}) => {
  const { browser, claude } = desktop;
  await navigation(browser, 'Skills');
  await clickButton(browser, 'Create skill');
  const create = await dialog(browser, 'Create a skill');
  await (await field(browser, 'Name', create)).setValue('desktop-smoke-skill');
  await (await field(browser, 'Save in', create)).selectByVisibleText(path.join(claude, 'skills'));
  await (
    await field(browser, 'Description', create)
  ).setValue('A fixture skill for desktop integration checks.');
  await fillMultiline(
    browser,
    await field(browser, 'Instructions · Markdown', create),
    '# Fixture instructions\n\nKeep this skill local.',
  );
  await clickButton(browser, 'Create skill', create);
  await create.waitForDisplayed({ reverse: true });
  await visible(browser, 'h2=desktop-smoke-skill');
  const file = path.join(claude, 'skills', 'desktop-smoke-skill', 'SKILL.md');
  await expect.poll(() => readFile(file, 'utf8')).toContain('Keep this skill local.');
  await clickButton(browser, 'Edit');
  const editor = await field(browser, 'Skill Markdown source');
  const edited = (await editor.getValue()) + '\n\nVerified desktop editing survives a reload.\n';
  await fillMultiline(browser, editor, edited);
  await clickButton(browser, 'Save');
  await expect.poll(() => readFile(file, 'utf8')).toBe(edited);
  await clickButton(browser, 'Disable skill');
  await button(browser, 'Restore skill');
  expect(await readdir(path.dirname(file))).toEqual(['SKILL.md.disabled']);
  await clickButton(browser, 'Restore skill');
  await button(browser, 'Disable skill');
  expect(await readFile(file, 'utf8')).toBe(edited);
});

test('validates and saves native settings with a backup and retains unknown fields', async ({
  desktop,
}) => {
  const { browser, claude, data } = desktop;
  await clickButton(browser, 'Settings');
  await clickButton(browser, 'Native configuration');
  const source = await field(browser, 'Claude Code settings source');
  const original = await readFile(path.join(claude, 'settings.json'), 'utf8');
  await source.setValue('{not valid json');
  await clickButton(browser, 'Save file');
  await visible(browser, '.error-box[role="alert"]');
  expect(await readFile(path.join(claude, 'settings.json'), 'utf8')).toBe(original);
  const updated = JSON.stringify({ ...JSON.parse(original), effortLevel: 'high' }, null, 2);
  await fillMultiline(browser, source, updated);
  await clickButton(browser, 'Save file');
  await expect.poll(() => readFile(path.join(claude, 'settings.json'), 'utf8')).toBe(updated);
  expect(JSON.parse(updated).fixtureUnrecognizedSetting.keep).toBe(true);
  const backups = await readdir(path.join(data, 'backups', 'configs'));
  expect(backups).toHaveLength(1);
  expect(await readFile(path.join(data, 'backups', 'configs', backups[0]), 'utf8')).toBe(original);
  await navigation(browser, 'Sessions');
  await clickButton(browser, 'Settings');
  await clickButton(browser, 'Native configuration');
  expect(await (await field(browser, 'Claude Code settings source')).getValue()).toBe(updated);
});

test('saves a connection, tests a local endpoint and chooses a model from its real catalogue', async ({
  desktop,
}) => {
  const { browser, data, gatewayUrl, requests } = desktop;
  await navigation(browser, 'Models & connections');
  await clickButton(browser, 'Add connection');
  const create = await dialog(browser, 'A new connection');
  await (await field(browser, 'Profile name', create)).setValue('Desktop mock gateway');
  await (await field(browser, 'Connect through', create)).selectByAttribute('value', 'local-proxy');
  await (await field(browser, 'Endpoint URL', create)).setValue(gatewayUrl);
  await (await field(browser, 'API key', create)).setValue('fixture-secret-only');
  const remember = await create.$('input[type="checkbox"]');
  if ((await remember.isEnabled()) && (await remember.isSelected())) await remember.click();
  await clickButton(browser, 'Save connection', create);
  await create.waitForDisplayed({ reverse: true });
  let card = await profileCard(browser);
  await clickButton(browser, 'Test connection', card);
  await expect
    .poll(async () => (await profileCard(browser)).getText())
    .toContain('Proxy is running');
  card = await profileCard(browser);
  await clickButton(browser, 'Models', card);
  const catalog = await dialog(browser, 'Explore available models');
  await (await field(browser, 'Search models', catalog)).setValue('Fixture coder');
  const freeOnly = await catalog.$('input[type="checkbox"]');
  if (!(await freeOnly.isSelected())) await freeOnly.click();
  await clickButton(browser, /Fixture coder/, catalog);
  const edit = await dialog(browser, 'Edit connection');
  expect(await (await field(browser, 'Model ID', edit)).getValue()).toBe('fixture/coder');
  await clickButton(browser, 'Save connection', edit);
  await edit.waitForDisplayed({ reverse: true });
  await expect
    .poll(async () => {
      const model = await visible(
        browser,
        '.connection-model > span:nth-child(2)',
        await profileCard(browser),
      );
      return await model.getProperty('innerText');
    })
    .toBe('fixture/coder');
  const profileFile = await readFile(path.join(data, 'profiles.json'), 'utf8');
  const profiles = JSON.parse(profileFile) as ProviderProfile[];
  expect(profiles.find((profile) => profile.name === 'Desktop mock gateway')).toMatchObject({
    provider: 'local-proxy',
    route: 'anthropic',
    baseUrl: gatewayUrl,
    model: 'fixture/coder',
  });
  expect(profileFile).not.toContain('fixture-secret-only');
  expect(profileFile).not.toContain('hasSecret');
  expect(requests).toContainEqual({ method: 'GET', url: '/healthz' });
  expect(requests).toContainEqual({ method: 'GET', url: '/v1/models' });
  expect(requests.every((request) => request.method === 'GET')).toBe(true);
});
