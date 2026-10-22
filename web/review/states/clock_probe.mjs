// The page with a wrong clock (Oct 22: Islombek's Mac was 5 s fast, so every status looked 5 s old and
// the page said "No device connected" while the device was live). Opens the local web app in headless
// Chrome with Date.now() shifted, and reports whether the page sees the device. Needs the local web app
// (cd web && npm run build && node server/index.mjs) and a runner (scripts/ui_states.py idle).
//   node web/review/states/clock_probe.mjs
import { spawn } from 'node:child_process';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import WebSocket from 'ws';
const sleep = ms => new Promise(r => setTimeout(r, ms));
let failures = 0;
for (const skew of [0, 5000, -5000, 60000]) {
  const profile = await mkdtemp(join(tmpdir(), 'koz-clock-'));
  const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', '--remote-debugging-port=9343', `--user-data-dir=${profile}`, '--no-first-run', 'about:blank'], { stdio: 'ignore' });
  let target; for (let i = 0; i < 50 && !target; i++) { try { target = (await (await fetch('http://127.0.0.1:9343/json/list')).json()).find(p => p.type === 'page'); } catch {} await sleep(200); }
  const ws = new WebSocket(target.webSocketDebuggerUrl), waiting = new Map(); let id = 0;
  ws.on('message', d => { const m = JSON.parse(d); waiting.get(m.id)?.(m); waiting.delete(m.id); });
  await new Promise(r => ws.on('open', r));
  const send = (method, params = {}) => new Promise(r => { const n = ++id; waiting.set(n, m => r(m.result)); ws.send(JSON.stringify({ id: n, method, params })); });
  try {
    await send('Page.addScriptToEvaluateOnNewDocument', { source: `{const now=Date.now.bind(Date);Date.now=()=>now()+(${skew});}` });
    await send('Page.navigate', { url: 'http://127.0.0.1:4173/#live' });
    await sleep(5000);
    const seen = (await send('Runtime.evaluate', { expression: "document.querySelector('.connection-strip span')?.textContent", returnByValue: true })).result.value;
    const ok = /connected|ulangan|подключено/i.test(seen) && !/No device|ulanmagan|не подключено/i.test(seen);
    console.log(`${ok ? 'ok  ' : 'FAIL'} page clock ${skew >= 0 ? '+' : ''}${skew / 1000} s: "${seen}"`);
    if (!ok) failures++;
  } finally { ws.close(); chrome.kill(); await sleep(300); }
}
console.log(failures ? `${failures} FAILED` : 'the page sees the device whatever its clock says');
process.exitCode = failures ? 1 : 0;
