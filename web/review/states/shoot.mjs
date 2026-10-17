// Screenshots of every Live state, in Uzbek, Russian and English, light and dark, at 360 px.
// Drives the installed Google Chrome over its DevTools protocol (no Playwright needed) against the
// local web app (npm start, port 4173) and the stand-in runner scripts/ui_states.py (port 8765).
// The camera picture in the eye is drawn by ui_states.py; nothing is filmed.
//   node web/review/states/shoot.mjs [outDir] [state ...]
import { spawn } from 'node:child_process';
import { mkdir, writeFile, mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import WebSocket from 'ws';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const out = process.argv[2] || join(root, 'web/review/states/shots');
const only = process.argv.slice(3);
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const WEB = 'http://127.0.0.1:4173';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const WIDTH = Number(process.env.KOZ_SHOOT_WIDTH || 360);   // 360 = phone; e.g. 1280 for desktop
const JOBS = { car: 'chase the red ball', refused: 'Who is this person? Tell me his name.' };
const COUNT = 'count people entering the shop';
const STATES = [   // [ui_states.py state, the web step it should reach, what to do there]
  ['idle', 'idle'], ['planning', 'planning'], ['testing', 'testing'], ['running', 'running'],
  ['confirming', 'confirming'], ['privacy', 'privacyStop'], ['stopped', 'stoppedByYou', 'stop'],
  ['camera_lost', 'cameraLost'], ['refused', 'refused'], ['car', 'running']];

async function chrome() {
  const profile = await mkdtemp(join(tmpdir(), 'koz-shoot-'));
  const child = spawn(CHROME, ['--headless=new', '--remote-debugging-port=9339', `--user-data-dir=${profile}`,
    '--no-first-run', '--hide-scrollbars', '--window-size=360,800', 'about:blank'], { stdio: 'ignore' });
  for (let i = 0; i < 50; i++) {
    try {
      const pages = await (await fetch('http://127.0.0.1:9339/json/list')).json();
      const page = pages.find(p => p.type === 'page');
      if (page) return { child, url: page.webSocketDebuggerUrl };
    } catch {}
    await sleep(200);
  }
  throw Error('Chrome did not start');
}

function cdp(url) {
  const ws = new WebSocket(url), waiting = new Map();
  let id = 0;
  ws.on('message', data => { const message = JSON.parse(data); waiting.get(message.id)?.(message); waiting.delete(message.id); });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const n = ++id; waiting.set(n, m => m.error ? reject(Error(`${method}: ${m.error.message}`)) : resolve(m.result));
    ws.send(JSON.stringify({ id: n, method, params }));
  });
  return new Promise(resolve => ws.on('open', () => resolve({ send, close: () => ws.close() })));
}

const value = async (page, expression) => (await page.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })).result.value;
async function waitFor(page, expression, ms = 20000) {
  const end = Date.now() + ms;
  while (Date.now() < end) { if (await value(page, expression)) return true; await sleep(150); }
  throw Error(`timed out: ${expression}`);
}
const step = page => value(page, "document.querySelector('.status')?.dataset.step||''");

function runner(state) {
  const python = join(root, '.venv/bin/python');
  const child = spawn(python, [join(root, 'scripts/ui_states.py'), state], { stdio: ['ignore', 'pipe', 'inherit'] });
  return new Promise(resolve => child.stdout.on('data', text => { if (String(text).includes('ui_states:')) resolve(child); }));
}

async function startJob(page, text) {
  await value(page, `location.hash='setup'`);
  await waitFor(page, "Boolean(document.querySelector('#prompt'))");
  await value(page, `(()=>{const p=document.querySelector('#prompt');p.value=${JSON.stringify(text)};p.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await waitFor(page, "!document.querySelector('#test').disabled");
  await value(page, "document.querySelector('#prompt-form').requestSubmit()");
}

async function setLook(page, language, theme) {
  await value(page, `(()=>{const s=document.querySelector('#language');if(s.value!=='${language}'){s.value='${language}';s.dispatchEvent(new Event('change',{bubbles:true}));}})()`);
  await value(page, `(()=>{if(document.documentElement.dataset.theme!=='${theme}')document.querySelector('#theme').click();})()`);
}

async function shoot(page, file) {
  const height = await value(page, 'Math.ceil(document.documentElement.scrollHeight)');
  await page.send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: Math.max(800, height), deviceScaleFactor: 2, mobile: WIDTH < 760 });
  await sleep(250);
  const { data } = await page.send('Page.captureScreenshot', { format: 'png' });
  await writeFile(file, Buffer.from(data, 'base64'));
  await page.send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: 800, deviceScaleFactor: 2, mobile: WIDTH < 760 });
}

await mkdir(out, { recursive: true });
const { child: browser, url } = await chrome();
const page = await cdp(url);
await page.send('Page.enable');
await page.send('Runtime.enable');
await page.send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: 800, deviceScaleFactor: 2, mobile: WIDTH < 760 });
const report = [];
try {
  for (const [state, target, action] of STATES.filter(([s]) => !only.length || only.includes(s))) {
    const python = await runner(state);
    try {
      await page.send('Page.navigate', { url: `${WEB}/#live` });
      await waitFor(page, "document.querySelector('.connection-strip')?.textContent.length>0");
      await sleep(1800);   // the web app reconnects to the new runner
      if (state !== 'idle') { await startJob(page, JOBS[state] || COUNT); await waitFor(page, "location.hash==='#live'"); }
      const wanted = action === 'stop' ? 'running' : target;
      await waitFor(page, `document.querySelector('.status')?.dataset.step===${JSON.stringify(wanted)}`, 30000);
      if (action === 'stop') {
        await value(page, "document.querySelector('[data-action=stop]').click()");
        await waitFor(page, `document.querySelector('.status')?.dataset.step===${JSON.stringify(target)}`);
      }
      for (const theme of ['light', 'dark']) for (const language of ['uz', 'ru', 'en']) {
        await setLook(page, language, theme);
        if (state === 'testing') {   // a fresh 3-second round for each picture
          await value(page, "document.querySelector('[data-action=stop]')?.click()");
          await waitFor(page, "Boolean(document.querySelector('[data-action=retry]:not([disabled])'))");
          await value(page, "document.querySelector('[data-action=retry]').click()");
          await waitFor(page, "document.querySelector('.status')?.dataset.step==='testing'");
          await sleep(1100);
        } else await sleep(700);
        const file = join(out, `${state}-${language}-${theme}${WIDTH === 360 ? '' : '-' + WIDTH}.png`);
        await shoot(page, file);
        report.push({ state, language, theme, step: await step(page), file });
      }
    } finally { python.kill('SIGINT'); await sleep(600); }
  }
} finally { page.close(); browser.kill(); }
await writeFile(join(out, 'shots.json'), JSON.stringify(report, null, 1) + '\n');
console.log(`${report.length} screenshots in ${out}`);
