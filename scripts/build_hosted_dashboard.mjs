import './compile_hosted_validator.mjs';
import { build } from 'vite';
import { resolve } from 'node:path';
import { mkdir, copyFile } from 'node:fs/promises';

const output = resolve(process.argv[2] || 'build/hosted/dist');
await build({ build: { outDir: resolve(output, 'client'), emptyOutDir: true, sourcemap: false } });
await build({ configFile: false, publicDir: false, ssr: { noExternal: true, target: 'webworker' },
  build: { ssr: 'hosting/worker.mjs', outDir: resolve(output, 'server'), emptyOutDir: true,
    target: 'es2022', sourcemap: false, minify: true, rollupOptions: { output: { entryFileNames: 'index.js' } } } });
await mkdir(resolve(output, '.openai'), { recursive: true });
await copyFile('.openai/hosting.json', resolve(output, '.openai/hosting.json'));
