// Local verification of the exact Worker bundle, using existing private runtime
// settings. This development adapter is not included in the Site checkout.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
import worker from '../build/hosted/dist/server/index.js';

const env = {};
for (const line of (await readFile('.env.dashboard', 'utf8')).split('\n')) {
  const match = /^(SUPABASE_URL|SUPABASE_SECRET_KEY)\s*=\s*(.*)$/.exec(line.trim());
  if (match) env[match[1]] = match[2].replace(/^(['"])(.*)\1$/, '$2');
}
const client = resolve('build/hosted/dist/client');
const mime = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml', '.json': 'application/json' };
env.ASSETS = { async fetch(request) {
  const path = new URL(request.url).pathname;
  const target = resolve(client, path === '/' ? 'index.html' : '.' + path);
  if (!target.startsWith(client + sep)) return new Response(null, { status: 404 });
  try { return new Response(await readFile(target), { headers: { 'Content-Type': mime[extname(target)] ?? 'application/octet-stream' } }); }
  catch { return new Response(null, { status: 404 }); }
} };
const server = createServer(async (req, res) => {
  if (!['127.0.0.1:8770', 'localhost:8770'].includes(req.headers.host)) { res.writeHead(403); res.end(); return; }
  try {
    const init = { method: req.method, headers: req.headers };
    if (!['GET', 'HEAD'].includes(req.method)) { init.body = req; init.duplex = 'half'; }
    const response = await worker.fetch(new Request(`http://${req.headers.host}${req.url}`, init), env);
    res.writeHead(response.status, Object.fromEntries(response.headers));
    res.end(Buffer.from(await response.arrayBuffer()));
  } catch { res.writeHead(503); res.end('temporarily_unavailable'); }
});
server.listen(8770, '127.0.0.1', () => console.log('Hosted dashboard preview: http://127.0.0.1:8770/'));
