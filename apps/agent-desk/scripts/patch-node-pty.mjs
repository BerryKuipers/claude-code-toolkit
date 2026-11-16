import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const version = '1.2.0-beta.18';
const patches = [
  {
    file: 'lib/windowsPtyAgent.js',
    originalHash: 'b7a03bcfa8d2f6cc766ece18757154e0356f6cc558be29f6f8a86f62ba872e38',
    changes: [
      {
        before: '        this._onError = new eventEmitter2_1.EventEmitter2();\n',
        after:
          '        this._onError = new eventEmitter2_1.EventEmitter2();\n        this._onProcessExit = new eventEmitter2_1.EventEmitter2();\n',
      },
      {
        before: "        this._inSocket.setEncoding('utf8');\n",
        after:
          "        this._inSocket.setEncoding('utf8');\n        this._outSocket.once('close', function () {\n            _this._clearConnectionTimeout();\n            _this._inSocket.destroy();\n            _this._conoutSocketWorker.dispose();\n        });\n",
      },
      {
        before: '    Object.defineProperty(WindowsPtyAgent.prototype, "onError", {\n',
        after:
          '    Object.defineProperty(WindowsPtyAgent.prototype, "onProcessExit", {\n        get: function () { return this._onProcessExit.event; },\n        enumerable: false,\n        configurable: true\n    });\n    Object.defineProperty(WindowsPtyAgent.prototype, "onError", {\n',
      },
      {
        before: '        this._exitCode = exitCode;\n',
        after: '        this._exitCode = exitCode;\n        this._onProcessExit.fire(exitCode);\n',
      },
    ],
  },
  {
    file: 'lib/windowsTerminal.js',
    originalHash: 'a805ed3bad53077b9e4572fd9ae23c4ef27b3029675e02e9b45bb3480950b3e5',
    changes: [
      {
        before:
          "        // The socket 'close' handler that drives 'exit' is only attached after\n        // ready_datapipe, which never fires when connect() fails.\n        _this._agent.onError(function () {\n            _this._close();\n            _this.emit('exit', _this._agent.exitCode);\n        });\n",
        after:
          "        var outputClosed = false;\n        var exitEmitted = false;\n        var finishExit = function () {\n            if (exitEmitted || !outputClosed || _this._agent.exitCode === undefined) return;\n            exitEmitted = true;\n            _this._close();\n            _this.emit('exit', _this._agent.exitCode);\n        };\n        _this._agent.onProcessExit(finishExit);\n        _this._agent.onError(function () {\n            outputClosed = true;\n            finishExit();\n        });\n        _this._socket.once('close', function () {\n            outputClosed = true;\n            finishExit();\n        });\n",
      },
      {
        before:
          "            // Cleanup after the socket is closed.\n            _this._socket.on('close', function () {\n                _this.emit('exit', _this._agent.exitCode);\n                _this._close();\n            });\n        });\n        _this._file = file;\n",
        after: '        });\n        _this._file = file;\n',
      },
      {
        before:
          "    WindowsTerminal.prototype.kill = function (signal) {\n        var _this = this;\n        this._deferNoArgs(function () {\n            if (signal) {\n                throw new Error('Signals not supported on windows.');\n            }\n            _this._close();\n            _this._agent.kill();\n        });\n    };\n",
        after:
          "    WindowsTerminal.prototype.kill = function (signal) {\n        var _this = this;\n        if (signal) throw new Error('Signals not supported on windows.');\n        if (this._killRequested) return;\n        this._killRequested = true;\n        this._deferreds = [];\n        var killConnected = function () {\n            _this._close();\n            _this._agent.kill();\n        };\n        if (this._agent.innerPid > 0) killConnected();\n        else this._socket.once('ready_datapipe', killConnected);\n    };\n",
      },
    ],
  },
];

const hash = (value) => createHash('sha256').update(value).digest('hex');

function replaceExact(source, before, after, file) {
  const index = source.indexOf(before);
  if (!before || index < 0 || source.indexOf(before, index + before.length) !== -1)
    throw new Error(
      `The pinned node-pty patch context does not match ${file}. Review the dependency before installing.`,
    );
  return source.slice(0, index) + after + source.slice(index + before.length);
}

function patchedSource(source, patch) {
  if (hash(source) === patch.originalHash)
    return patch.changes.reduce(
      (text, change) => replaceExact(text, change.before, change.after, patch.file),
      source,
    );
  let original = source;
  for (const change of [...patch.changes].reverse()) {
    original = replaceExact(original, change.after, change.before, patch.file);
  }
  if (hash(original) !== patch.originalHash)
    throw new Error(
      `The pinned node-pty source hash does not match ${patch.file}. Review the dependency before installing.`,
    );
  return source;
}

export async function patchNodePty(directory) {
  const root = resolve(directory);
  const metadata = JSON.parse(await readFile(join(root, 'package.json'), 'utf8'));
  if (metadata.name !== 'node-pty' || metadata.version !== version)
    throw new Error(
      `The Windows terminal patch requires node-pty ${version}; found ${metadata.name}@${metadata.version}.`,
    );
  const files = await Promise.all(
    patches.map(async (patch) => {
      const file = join(root, patch.file);
      const original = await readFile(file, 'utf8');
      return { file, original, patched: patchedSource(original, patch) };
    }),
  );
  for (const file of files)
    if (file.original !== file.patched) await writeFile(file.file, file.patched);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await patchNodePty(process.argv[2] || join(process.cwd(), 'node_modules', 'node-pty'));
  process.stdout.write(`Verified node-pty ${version} Windows output-drain and cleanup patch.\n`);
}
