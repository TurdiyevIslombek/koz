// The deployed web app seen by a judge with no login (Oct 21): every response it loads, its pictures, and
// whether the eye exists. Prints numbers and names only. node web/review/cloud/judges_probe.mjs https://IP/ [outDir]
import { spawn } from 'node:child_process';
import { mkdtemp, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import WebSocket from 'ws';
const URL0 = process.argv[2], OUT = process.argv[3];
const sleep = ms => new Promise(r => setTimeout(r, ms));
const profile = await mkdtemp(join(tmpdir(), 'koz-judge-'));
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', '--remote-debugging-port=9342', `--user-data-dir=${profile}`, '--no-first-run', 'about:blank'], { stdio: 'ignore' });
let target; for (let i = 0; i < 50 && !target; i++) { try { target = (await (await fetch('http://127.0.0.1:9342/json/list')).json()).find(p => p.type === 'page'); } catch {} await sleep(200); }
const ws = new WebSocket(target.webSocketDebuggerUrl), waiting = new Map(), responses = [], sockets = []; let id = 0;
ws.on('message', d => { const m = JSON.parse(d);
  if (m.method === 'Network.responseReceived') responses.push(`${m.params.response.status} ${m.params.response.mimeType} ${new URL(m.params.response.url).pathname}`);
  if (m.method === 'Network.webSocketCreated') sockets.push(new URL(m.params.url).pathname);
  waiting.get(m.id)?.(m); waiting.delete(m.id); });
await new Promise(r => ws.on('open', r));
const send = (method, params = {}) => new Promise(r => { const n = ++id; waiting.set(n, m => r(m.result)); ws.send(JSON.stringify({ id: n, method, params })); });
const run = async e => (await send('Runtime.evaluate', { expression: e, returnByValue: true })).result.value;
try {
  await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  for (const hash of ['#live', '#trials']) {
    await send('Page.navigate', { url: URL0 + hash }); await sleep(5000);
    const page = await run(`({tabs:[...document.querySelectorAll('.tabs a')].map(a=>a.hash),eye:Boolean(document.querySelector('#live-eye,#eye-picture,#eye-large')),images:[...document.querySelectorAll('img')].map(i=>i.getAttribute('src')),backgrounds:[...document.querySelectorAll('*')].map(e=>getComputedStyle(e).backgroundImage).filter(b=>b!=='none').length,notice:document.querySelector('.notice')?.textContent.trim().slice(0,120)||null,startButtons:document.querySelectorAll('#prompt-form,[data-action=stop],[data-action=retry]').length})`);
    console.log(hash, JSON.stringify(page));
    if (OUT) { const { data } = await send('Page.captureScreenshot', { format: 'png' }); await writeFile(join(OUT, `judges${hash.slice(1)}.png`), Buffer.from(data, 'base64')); }
  }
  console.log('responses:', [...new Set(responses)].join(' | '));
  console.log('websockets:', sockets.join(', ') || 'none');
  const drawings = responses.filter(r => /image\/svg\+xml,/.test(r));   // inline drawings in the stylesheet (the dropdown arrow), not pictures
  console.log('any picture responses:', responses.filter(r => /image\//.test(r) && !drawings.includes(r)).join(' | ') || 'none', `(+ ${drawings.length} inline drawing(s) from the stylesheet)`);
} finally { ws.close(); chrome.kill(); }
