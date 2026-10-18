// How smooth the eye is in a real browser (Oct 18): pictures per second actually shown, whether the
// eye element is rebuilt (each rebuild replays the fade), and the large view (opens on a tap, fills
// most of the screen, closes on Esc and when the job stops). Needs the local web app (npm start) and
// a runner with a running job's camera: scripts/ui_states.py running (a DRAWN picture). Headless
// Chrome, so the page counts as visible. Prints numbers; with an output folder, one screenshot of the
// large view (of the drawn picture only).
//   node web/review/states/eye_probe.mjs [outDir]
import { spawn } from 'node:child_process';
import { mkdtemp, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import WebSocket from 'ws';

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const out = process.argv[2];
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

const profile = await mkdtemp(join(tmpdir(), 'koz-probe-'));
const browser = spawn(CHROME, ['--headless=new', '--remote-debugging-port=9340', `--user-data-dir=${profile}`, '--no-first-run', 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 50 && !target; i++) { try { target = (await (await fetch('http://127.0.0.1:9340/json/list')).json()).find(p => p.type === 'page'); } catch {} await sleep(200); }
const ws = new WebSocket(target.webSocketDebuggerUrl), waiting = new Map(); let id = 0;
ws.on('message', d => { const m = JSON.parse(d); waiting.get(m.id)?.(m); waiting.delete(m.id); });
await new Promise(r => ws.on('open', r));
const send = (method, params = {}) => new Promise(r => { const n = ++id; waiting.set(n, m => r(m.result)); ws.send(JSON.stringify({ id: n, method, params })); });
const run = async expression => (await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })).result.value;

try {
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await send('Page.navigate', { url: 'http://127.0.0.1:4173/#live' });
  await sleep(3000);
  if (await run("document.querySelector('.status')?.dataset.step") !== 'running') {
    await run(`(async()=>{location.hash='setup';await new Promise(r=>setTimeout(r,400));const p=document.querySelector('#prompt');p.value='count people entering the shop';p.dispatchEvent(new Event('input',{bubbles:true}));await new Promise(r=>setTimeout(r,200));document.querySelector('#prompt-form').requestSubmit();})()`);
    await sleep(6000);
  }
  const shown = await run(`new Promise(resolve=>{let changes=0,rebuilt=0,fades=0,node=document.querySelector('#eye-picture');
    const watch=n=>new MutationObserver(list=>{for(const m of list){if(m.attributeName==='src'&&n.getAttribute('src'))changes++;if(m.attributeName==='hidden'&&!n.hidden)fades++;}}).observe(n,{attributes:true});
    watch(node);const rebuild=setInterval(()=>{const n=document.querySelector('#eye-picture');if(n!==node){rebuilt++;node=n;watch(n);}},20);
    setTimeout(()=>{clearInterval(rebuild);resolve({picturesPerSecond:changes/10,eyeRebuildsPerSecond:rebuilt/10,fadeReplays:fades,step:document.querySelector('.status')?.dataset.step});},10000);})`);
  console.log('eye in the page:', JSON.stringify(shown));
  await run("document.querySelector('#live-eye').click()");
  await sleep(500);
  const large = await run(`(()=>{const d=document.querySelector('#eye-large'),b=d.querySelector('img').getBoundingClientRect();return {open:d.open,picture:Boolean(d.querySelector('img').getAttribute('src')),size:Math.round(b.width)+'x'+Math.round(b.height)+' of '+innerWidth+'x'+innerHeight};})()`);
  console.log('large view:', JSON.stringify(large));
  if (out) { const { data } = await send('Page.captureScreenshot', { format: 'png' }); await writeFile(join(out, 'eye-large.png'), Buffer.from(data, 'base64')); }
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
  await sleep(300);
  console.log('after Esc, large view open:', await run("document.querySelector('#eye-large').open"));
  await run("document.querySelector('#live-eye').click()");
  await sleep(400);
  await run("document.querySelector('[data-action=stop]')?.click()");
  await sleep(1500);
  console.log('after Stop, large view open:', await run("document.querySelector('#eye-large').open"), '| eye closed:', await run("document.querySelector('#live-eye').classList.contains('is-closed')"));
} finally { ws.close(); browser.kill(); }
