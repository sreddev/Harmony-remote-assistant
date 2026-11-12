// Render a local HTML page in headless Edge, wait for Mermaid, strip scripts, save as MHTML.
// Usage: node snap.mjs <page.html | http://url> <out.mhtml>  (a URL keeps local paths out of the MHTML)
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import os from 'node:os';
import path from 'node:path';

const [page, out] = process.argv.slice(2);
const edge = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const port = 9333;
const profile = mkdtempSync(path.join(os.tmpdir(), 'edge-snap-'));
const proc = spawn(edge, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--window-size=1280,900', 'about:blank'], { stdio: 'ignore' });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let target;
for (let i = 0; i < 50 && !target; i++) {
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === 'page'); }
  catch { await sleep(200); }
}
if (!target) { proc.kill(); throw new Error('Edge did not start'); }

const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map();
ws.onmessage = (m) => { const r = JSON.parse(m.data); if (pending.has(r.id)) { pending.get(r.id)(r); pending.delete(r.id); } };
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const evalJs = async (expression) => (await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })).result?.result?.value;

await send('Page.enable');
await send('Page.navigate', { url: /^https?:/.test(page) ? page : pathToFileURL(page).href });
let ok = false;
for (let i = 0; i < 100 && !ok; i++) { await sleep(300); ok = (await evalJs('document.documentElement.dataset.rendered')) === '1'; }
const svgs = await evalJs('document.querySelectorAll("pre.mermaid svg").length');
await evalJs('document.fonts.ready.then(() => true)');
// Smoke-test any page simulator, then switch it to its static view.
const simTest = await evalJs(`(function(){var b=document.getElementById('btn-step');if(!b)return 'no simulator';
  for(var i=0;i<4;i++)b.click();var n=document.querySelectorAll('#console div').length;
  var cur=document.querySelectorAll('.steps li.cur').length;document.getElementById('btn-reset').click();
  return 'console lines '+n+', highlighted '+cur;})()`);
console.log('simulator:', simTest);
await evalJs('window.__staticExport ? (window.__staticExport(), "exported") : "none"');
// Remove scripts so the saved file is static, and drop the render flag.
await evalJs('document.querySelectorAll("script").forEach(s => s.remove()); delete document.documentElement.dataset.rendered; true');
const snap = await send('Page.captureSnapshot', { format: 'mhtml' });
writeFileSync(out, snap.result.data);
console.log(JSON.stringify({ rendered: ok, diagrams: svgs, bytes: snap.result.data.length, out }));
ws.close(); proc.kill();
