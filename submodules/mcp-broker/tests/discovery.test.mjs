import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { cp, mkdtemp, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { createServer } from 'node:net';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { describeUpstreamTool, searchTools } from '../dist/discovery.js';
import { callUpstreamTool, disconnectAll, getCachedTools, listUpstreamTools } from '../dist/upstream.js';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const fixture = { id: 'fixture', transport: 'stdio', command: process.execPath, args: [join(root, 'tests/fixtures/upstream.mjs')], env: {}, startMode: 'lazy' };

test('cold queries discover later pages; summaries stay small; schemas load on demand', async () => {
  try {
    assert.equal(getCachedTools(fixture.id), undefined);
    const result = await searchTools([fixture], [], { q: 'ROWS' });
    assert.equal(result.isError, false);
    const summaries = JSON.parse(result.content[0].text);
    assert.deepEqual(summaries.map(({ name }) => name), ['filtered_rows']);
    assert.equal(summaries[0].inputSchema, undefined);
    assert.equal(getCachedTools(fixture.id).length, 2);
    const described = JSON.parse((await describeUpstreamTool([fixture], { server: 'fixture', tool: 'filtered_rows' })).content[0].text);
    assert.deepEqual(described.inputSchema.required, ['status', 'limit']);
    assert.equal(described.annotations.readOnlyHint, true);
    assert.equal(described.outputSchema.type, 'object');
    const cached = await searchTools([{ ...fixture, command: 'must-not-start' }], [], { q: 'rows' });
    assert.deepEqual(cached, result);
  } finally {
    disconnectAll();
  }
});

test('server filters bound discovery and partial failures are visible', async () => {
  const missing = { ...fixture, id: 'broken', command: join(tmpdir(), 'missing-mcp-fixture'), args: [] };
  try {
    const scoped = await searchTools([fixture, missing], [], { servers: ['fixture'], q: 'rows' });
    assert.equal(scoped.content.length, 1);
    const partial = await searchTools([fixture, missing], [], { q: 'rows' });
    assert.equal(partial.isError, false);
    assert.match(partial.content[1].text, /Incomplete discovery.*broken/);
    const failed = await searchTools([missing], [], { q: 'rows' });
    assert.equal(failed.isError, true);
    assert.match(failed.content[1].text, /broken/);
    await assert.rejects(searchTools([fixture], [], { servers: ['unknown'] }), /Unknown server IDs/);
    await assert.rejects(searchTools([fixture], [], { q: 1 }), /must be a string/);
    await assert.rejects(describeUpstreamTool([fixture], { server: 'fixture', tool: 'absent' }), /Tool not found/);
    await assert.rejects(describeUpstreamTool([fixture], { server: 'unknown', tool: 'first' }), /Server not found/);
  } finally {
    disconnectAll();
  }
});

test('pagination retains output validation for tools from earlier pages', async () => {
  try {
    await listUpstreamTools(fixture);
    await assert.rejects(callUpstreamTool(fixture, 'first', { scenario: 'invalid' }), /output schema/);
    await assert.rejects(callUpstreamTool(fixture, 'first', { scenario: 'missing' }), /did not return structured content/);
    await assert.rejects(callUpstreamTool(fixture, 'first', { scenario: 'invalid-error' }), /output schema/);
    const valid = await callUpstreamTool(fixture, 'first', { scenario: 'valid' });
    assert.deepEqual(valid.structuredContent, { value: 42 });
    const error = await callUpstreamTool(fixture, 'first', { scenario: 'error' });
    assert.equal(error.isError, true);
    assert.equal(error.content[0].text, 'Fixture result');
  } finally {
    disconnectAll();
  }
});

test('repeated pagination cursors fail without caching an incomplete list', async () => {
  const cyclic = { ...fixture, id: 'cyclic', args: [...fixture.args, '--cycle'] };
  try {
    await assert.rejects(listUpstreamTools(cyclic), /Repeated tools\/list cursor/);
    assert.equal(getCachedTools(cyclic.id), undefined);
  } finally {
    disconnectAll();
  }
});

test('the stdio broker exposes describe and keeps invoke output and error flags intact', async () => {
  const temporary = await mkdtemp(join(tmpdir(), 'broker-discovery-'));
  let client;
  try {
    await cp(join(root, 'dist'), join(temporary, 'dist'), { recursive: true });
    await symlink(join(root, 'node_modules'), join(temporary, 'node_modules'), process.platform === 'win32' ? 'junction' : 'dir');
    await writeFile(join(temporary, 'package.json'), '{"type":"module"}');
    await writeFile(join(temporary, 'servers.config.json'), JSON.stringify({ servers: [fixture] }));
    client = new Client({ name: 'broker-test', version: '1.0.0' });
    await client.connect(new StdioClientTransport({ command: process.execPath, args: [join(temporary, 'dist/broker.js')], stderr: 'pipe' }));
    assert.ok((await client.listTools()).tools.some(({ name }) => name === 'broker.describe'));
    const search = await client.callTool({ name: 'broker.search', arguments: { q: 'rows' } });
    assert.equal(JSON.parse(search.content[0].text)[0].name, 'filtered_rows');
    const described = await client.callTool({ name: 'broker.describe', arguments: { server: 'fixture', tool: 'filtered_rows' } });
    assert.deepEqual(JSON.parse(described.content[0].text).inputSchema.required, ['status', 'limit']);
    const invoked = await client.callTool({ name: 'broker.invoke', arguments: { server: 'fixture', tool: 'filtered_rows', args: { status: 'done', limit: 1000 } } });
    assert.equal(invoked.isError, true);
    assert.equal(JSON.parse(invoked.content[0].text).rows.length, 1000);
    assert.deepEqual(JSON.parse(invoked.content[0].text).received, { status: 'done', limit: 1000 });
  } finally {
    await client?.close();
    await rm(temporary, { recursive: true, force: true });
  }
});

test('HTTP initializes and serves search, describe and invoke with parsed JSON bodies', async () => {
  const temporary = await mkdtemp(join(tmpdir(), 'broker-http-'));
  const probe = createServer();
  probe.listen(0, '127.0.0.1');
  await once(probe, 'listening');
  const port = probe.address().port;
  await new Promise((resolve, reject) => probe.close((error) => error ? reject(error) : resolve()));
  let brokerProcess;
  let client;
  try {
    await cp(join(root, 'dist'), join(temporary, 'dist'), { recursive: true });
    await symlink(join(root, 'node_modules'), join(temporary, 'node_modules'), process.platform === 'win32' ? 'junction' : 'dir');
    await writeFile(join(temporary, 'package.json'), '{"type":"module"}');
    await writeFile(join(temporary, 'servers.config.json'), JSON.stringify({ servers: [fixture] }));
    brokerProcess = spawn(process.execPath, [join(temporary, 'dist/http-broker.js')], {
      env: { ...process.env, BROKER_PORT: String(port) }, stdio: ['ignore', 'pipe', 'pipe'],
    });
    await new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error('HTTP broker did not start')), 10000);
      brokerProcess.once('error', (error) => { clearTimeout(timeout); reject(error); });
      brokerProcess.once('exit', (code) => { clearTimeout(timeout); reject(new Error(`HTTP broker exited: ${code}`)); });
      brokerProcess.stdout.on('data', (data) => {
        if (data.toString().includes('listening on port')) { clearTimeout(timeout); resolve(); }
      });
    });
    client = new Client({ name: 'broker-http-test', version: '1.0.0' });
    await client.connect(new StreamableHTTPClientTransport(new URL(`http://127.0.0.1:${port}/mcp`)));
    const search = await client.callTool({ name: 'broker.search', arguments: { q: 'rows' } });
    assert.equal(JSON.parse(search.content[0].text)[0].name, 'filtered_rows');
    const described = await client.callTool({ name: 'broker.describe', arguments: { server: 'fixture', tool: 'filtered_rows' } });
    assert.deepEqual(JSON.parse(described.content[0].text).inputSchema.required, ['status', 'limit']);
    const invoked = await client.callTool({ name: 'broker.invoke', arguments: { server: 'fixture', tool: 'first', args: { scenario: 'valid' } } });
    assert.deepEqual(invoked.structuredContent, { value: 42 });
  } finally {
    await client?.close();
    if (brokerProcess && brokerProcess.exitCode === null) {
      const exited = once(brokerProcess, 'exit');
      brokerProcess.kill('SIGTERM');
      await exited;
    }
    await rm(temporary, { recursive: true, force: true });
  }
});
