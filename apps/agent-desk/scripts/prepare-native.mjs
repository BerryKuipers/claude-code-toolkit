import { access, copyFile, mkdir } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Arch } from 'electron-builder';
import { patchNodePty } from './patch-node-pty.mjs';

export async function prepareNative(
  appDirectory,
  platform = process.platform,
  arch = process.arch,
) {
  const directory = join(resolve(appDirectory), 'node_modules', 'node-pty');
  await patchNodePty(directory);
  if (platform !== 'win32') return;
  if (!['x64', 'arm64'].includes(arch))
    throw new Error(`Unsupported Windows terminal architecture: ${arch}.`);
  const prebuilt = join(directory, 'prebuilds', `win32-${arch}`);
  const assets = ['conpty.dll', 'OpenConsole.exe'];
  for (const file of assets) await access(join(prebuilt, 'conpty', file));
  const release = join(directory, 'build', 'Release');
  try {
    await access(join(release, 'conpty.node'));
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    await access(join(prebuilt, 'conpty.node'));
    return;
  }
  await mkdir(join(release, 'conpty'), { recursive: true });
  for (const file of assets)
    await copyFile(join(prebuilt, 'conpty', file), join(release, 'conpty', file));
  process.stdout.write(
    'Prepared bundled Windows terminal DLLs beside the rebuilt native module.\n',
  );
}

export default async function afterExtract(context) {
  await prepareNative(
    context.packager.info.appDir,
    context.electronPlatformName,
    Arch[context.arch],
  );
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await prepareNative(process.cwd());
  process.stdout.write('Verified native terminal runtime and cleanup patch.\n');
}
