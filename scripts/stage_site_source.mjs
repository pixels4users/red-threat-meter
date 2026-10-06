import { cp, mkdir, readFile, writeFile, lstat, rm } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';

// Publish a minimal Site repository. Analysis data, Python, secrets and the
// research skill library are never copied into this source checkout.
const target = resolve(process.argv[2] ?? 'data/sites/dashboard-source');
const files = ['package.json', 'package-lock.json', 'vite.config.js', 'theme.css', 'ui/components/card.css', 'ui/components/topic-shortcut.css', 'ui/components/signal-item.js', 'ui/components/signal-item.css',
  'config/dashboard.json', 'config/signal-presentation.json', 'config/newsletter.json', 'schemas/dashboard/report.schema.json',
  'scripts/compile_hosted_validator.mjs', 'scripts/build_hosted_dashboard.mjs',
  'hosting/worker.mjs', 'hosting/newsletter-proxy.mjs', 'hosting/newsletter-http.mjs'];
for (const name of files) {
  if (!(await lstat(name)).isFile()) throw new Error(`Expected regular source file: ${name}`);
  await mkdir(dirname(resolve(target, name)), { recursive: true });
  await cp(name, resolve(target, name));
}
// Remove only this generated frontend copy, not Site identity or Git history.
await rm(resolve(target, 'web'), { force: true, recursive: true });
await cp('web', resolve(target, 'web'), { recursive: true, filter: async source => {
  if ((await lstat(source)).isSymbolicLink()) throw new Error('Source symlink is not publishable');
  return true;
} });
const pkg = JSON.parse(await readFile('package.json', 'utf8'));
pkg.scripts = { build: 'node scripts/build_hosted_dashboard.mjs dist' };
await writeFile(resolve(target, 'package.json'), JSON.stringify(pkg, null, 2) + '\n');
await writeFile(resolve(target, '.gitignore'), 'node_modules/\ndist/\nhosting/.generated/\n.sites-runtime/\n.env*\n!.env.example\n');
await writeFile(resolve(target, '.env.example'), 'SUPABASE_URL=https://dubhsimiblpfcaudbvjb.supabase.co\nSUPABASE_SECRET_KEY=\n');
await writeFile(resolve(target, 'README.md'), '# Red Threat Alert — hosted dashboard\n\nFrontend and read-only HTTP adapter for published Supabase reports.\nCanonical source: https://github.com/pixels4users/red-threat-meter\nNo analysis data or credentials are stored here. Runtime secrets are configured in Sites.\n');
try {
  const identity = await readFile('.openai/hosting.json');
  await mkdir(resolve(target, '.openai'), { recursive: true });
  await writeFile(resolve(target, '.openai/hosting.json'), identity);
} catch (error) { if (error.code !== 'ENOENT') throw error; }
console.log(target);
