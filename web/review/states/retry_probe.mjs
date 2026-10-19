// "Try again" in a real browser (Codex's findings 2 and 3, Oct 19): it keeps the job's camera even
// after a page reload, and inside a trial whose one job already ran it offers one button, "Finish
// trial and try again", which closes the trial (unknown, interrupted) and starts the job again, with
// no BUSY error. Needs the local web app (cd web && npm run build && node server/index.mjs) and the
// rig with two camera slots (a DRAWN picture; nothing filmed):
//   .venv/bin/python scripts/ui_states.py running --cameras mac_camera,esp32_cam
//   node web/review/states/retry_probe.mjs
// Headless Chrome. Reads the commands the page sends (camera_id) and the page's own state.
import { spawn } from 'node:child_process';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import WebSocket from 'ws';

const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
let failures = 0;
const check = (ok, what) => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${what}`); if (!ok) failures++; };

const profile = await mkdtemp(join(tmpdir(), 'koz-probe-'));
const browser = spawn(CHROME, ['--headless=new', '--remote-debugging-port=9341', `--user-data-dir=${profile}`, '--no-first-run', 'about:blank'], { stdio: 'ignore' });
let target;
for (let i = 0; i < 50 && !target; i++) { try { target = (await (await fetch('http://127.0.0.1:9341/json/list')).json()).find(p => p.type === 'page'); } catch {} await sleep(200); }
const ws = new WebSocket(target.webSocketDebuggerUrl), waiting = new Map(), sent = []; let id = 0;
ws.on('message', d => {
  const m = JSON.parse(d);
  if (m.method === 'Network.requestWillBeSent' && m.params.request.url.endsWith('/api/commands')) sent.push(JSON.parse(m.params.request.postData));
  waiting.get(m.id)?.(m); waiting.delete(m.id);
});
await new Promise(r => ws.on('open', r));
const send = (method, params = {}) => new Promise(r => { const n = ++id; waiting.set(n, m => r(m.result)); ws.send(JSON.stringify({ id: n, method, params })); });
const run = async expression => (await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })).result.value;
const step = () => run("document.querySelector('.status')?.dataset.step");
async function waitStep(steps, ms = 20000) {
  for (const end = Date.now() + ms; Date.now() < end; await sleep(250)) if (steps.includes(await step())) return true;
  return false;
}
const go = async screen => { await run(`location.hash='${screen}'`); await sleep(500); };
const click = async action => { await run(`document.querySelector('[data-action="${action}"]')?.click()`); };
const errorNotice = () => run("document.querySelector('.notice.error')?.textContent||null");
const starts = () => sent.filter(c => c.command === 'start_job');
async function submitPrompt(text) {
  await go('setup');
  if (text) await run(`(()=>{const p=document.querySelector('#prompt');p.value=${JSON.stringify(text)};p.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await sleep(200);
  await run("document.querySelector('#prompt-form').requestSubmit()");
}
async function stopJob() {
  await click('stop');
  check(await waitStep(['stoppedByYou']), 'Stop ends the job');
}

try {
  await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
  await send('Page.navigate', { url: 'http://127.0.0.1:4173/#setup' });
  await sleep(3000);

  // Finding 2: the job runs on the second camera; after a reload, Try again still uses it.
  await run("(()=>{const s=document.querySelector('#camera-choice');s.value='esp32_cam';s.dispatchEvent(new Event('change',{bubbles:true}));})()");
  await sleep(300);
  await submitPrompt('count people entering the shop');
  check(await waitStep(['testing', 'running']), 'the job starts');
  check(starts().at(-1)?.data.camera_id === 'esp32_cam', 'it was started on esp32_cam');
  const stored = await run("sessionStorage.getItem('koz-last-camera')");
  check(stored && Object.keys(JSON.parse(stored)).sort().join() === 'camera_id,job_id,session_id', `this tab keeps only session, job and camera: ${stored}`);
  await stopJob();
  await run('location.reload()');
  await sleep(3000);
  await go('live');
  check(await run("Boolean(document.querySelector('[data-action=retry]'))"), 'after the reload, Try again is offered');
  await click('retry');
  check(await waitStep(['testing', 'running']), 'Try again starts the job');
  check(starts().at(-1)?.data.camera_id === 'esp32_cam', `Try again kept the camera: ${starts().at(-1)?.data.camera_id}`);
  check(!(await errorNotice()), 'no error');
  await stopJob();

  // Finding 3: a trial whose one job already ran offers "Finish trial and try again", not a BUSY error.
  await go('trials');
  await run("(()=>{const s=document.querySelector('#trial-demo');s.value='classroom';s.dispatchEvent(new Event('change',{bubbles:true}));})()");
  await sleep(300);
  await click('begin-trial');
  await sleep(1500);
  await submitPrompt(null);   // Begin trial filled in the classroom example
  check(await waitStep(['testing', 'running']), 'the trial job starts');
  const trialCamera = starts().at(-1)?.data.camera_id;
  await stopJob();
  const offer = await run("(()=>{const b=document.querySelector('[data-action=\"finish-retry\"]');return {button:b?.textContent.trim()||null,plainRetry:Boolean(document.querySelector('[data-action=retry]')),note:document.querySelector('.status .small.muted')?.textContent||null};})()");
  check(offer.button && !offer.plainRetry, `one button: "${offer.button}"`);
  check(Boolean(offer.note), `with the note: "${offer.note}"`);
  const before = sent.length;
  await click('finish-retry');
  check(await waitStep(['testing', 'running'], 15000), 'the trial is finished and the job starts again');
  const after = sent.slice(before).map(c => c.command);
  check(after.join() === 'finish_trial,start_job', `commands sent: ${after.join(', ')}`);
  check(sent.slice(before)[0]?.data.result === 'unknown' && sent.slice(before)[0]?.data.reason === 'interrupted', 'the trial is saved as unknown, interrupted');
  check(starts().at(-1)?.data.camera_id === trialCamera, `same camera: ${starts().at(-1)?.data.camera_id}`);
  check(!(await errorNotice()), `no error: ${await errorNotice()}`);
  await click('stop');
  await sleep(1500);
} finally { ws.close(); browser.kill(); }
console.log(failures ? `${failures} FAILED` : 'all retry checks passed');
process.exitCode = failures ? 1 : 0;
