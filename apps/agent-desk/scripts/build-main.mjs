import { build } from 'esbuild';

await build({
  entryPoints: ['src/main/index.ts'],
  bundle: true,
  platform: 'node',
  target: 'node24',
  format: 'cjs',
  outfile: 'dist/main/index.cjs',
  external: ['electron', 'node-pty'],
  sourcemap: true,
});
await build({
  entryPoints: ['src/main/preload.ts'],
  bundle: true,
  platform: 'node',
  target: 'node24',
  format: 'cjs',
  outfile: 'dist/main/preload.cjs',
  external: ['electron'],
  sourcemap: true,
});
