import { spawn, spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync } from 'node:fs';
import { mkdir, open, readFile, rm, stat, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const fingerprint = createHash('sha256').update(root).digest('hex');
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
export async function probeWeb(url) {
  try {
    const response = await fetch(`${url}/api/health`, { signal: AbortSignal.timeout(800) });
    const body = await response.json().catch(() => null);
    return body?.service === 'koz-web' && body.workspace === fingerprint ? 'ours' : 'occupied';
  } catch (error) {
    return error.cause?.code === 'ECONNREFUSED' ? 'absent' : 'occupied';
  }
}
export async function launch({ port = 4173, openBrowser = true } = {}) {
  if (Number(process.versions.node.split('.')[0]) < 22) throw Error('Node.js 22 or newer is required.');
  const url = `http://127.0.0.1:${port}`, data = resolve(root, '.data');
  await mkdir(data, { recursive: true, mode: 0o700 });
  const show = () => {
    if (openBrowser) {
      const opened = spawnSync('/usr/bin/open', [`${url}/#live`], { stdio: 'ignore' });
      if (opened.status !== 0) throw Error(`Open ${url} in your browser.`);
    }
  };
  const initial = await probeWeb(url);
  if (initial === 'ours') { show(); return { url, reused: true }; }
  if (initial === 'occupied') throw Error(`Port ${port} is already used by another program. It was left untouched.`);
  const lock = resolve(data, 'launcher.lock');
  let ownLock = false;
  try {
    try { await mkdir(lock); ownLock = true; } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      let alive = true;
      try { const pid = Number(await readFile(resolve(lock, 'pid'), 'utf8')); if (pid > 0) process.kill(pid, 0); } catch (error) { if (error.code === 'ESRCH' || error.code === 'ENOENT' && Date.now() - (await stat(lock)).mtimeMs > 30000) alive = false; }
      if (!alive) { await rm(lock, { recursive: true }); await mkdir(lock); ownLock = true; }
      else {
        for (let i = 0; i < 100; i++) { await pause(200); if (await probeWeb(url) === 'ours') { show(); return { url, reused: true }; } }
        throw Error('Koʻz is still starting. Try the launcher again shortly.');
      }
    }
    await writeFile(resolve(lock, 'pid'), String(process.pid), { mode: 0o600 });
    if (!existsSync(resolve(root, 'node_modules/esbuild')) || !existsSync(resolve(root, 'node_modules/ws')) || !existsSync(resolve(root, 'node_modules/ajv'))) {
      const installed = spawnSync('npm', ['ci', '--no-audit', '--no-fund'], { cwd: root, stdio: 'inherit' });
      if (installed.status !== 0) throw Error('Dependencies could not be installed. Check your internet connection and try again.');
    }
    const built = spawnSync(process.execPath, ['scripts/build.mjs'], { cwd: root, stdio: 'inherit' });
    if (built.status !== 0) throw Error('The web build failed. See the launcher output.');
    const log = await open(resolve(data, 'startup.log'), 'a', 0o600);
    const child = spawn(process.execPath, ['server/index.mjs'], {
      cwd: root, detached: true, env: { ...process.env, PORT: String(port) }, stdio: ['ignore', log.fd, log.fd]
    });
    let failed = false; child.on('error', () => { failed = true; }); child.unref(); await log.close();
    for (let i = 0; i < 100; i++) {
      if (failed) break;
      if (await probeWeb(url) === 'ours') { show(); return { url, reused: false, pid: child.pid }; }
      await pause(200);
    }
    child.kill('SIGTERM');
    throw Error('Koʻz did not become ready. Details are in web/.data/startup.log.');
  } finally { if (ownLock) await rm(lock, { recursive: true, force: true }); }
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    if (existsSync(resolve(root, '.env'))) process.loadEnvFile(resolve(root, '.env'));
    const result = await launch({ port: Number(process.env.PORT) || 4173, openBrowser: process.env.KOZ_NO_BROWSER !== '1' });
    console.log(`Koʻz: ${result.url}`);
  } catch (error) {
    const message = error.message;
    console.error(message);
    if (process.env.KOZ_NO_BROWSER !== '1') spawnSync('/usr/bin/osascript', ['-e', 'on run argv\ndisplay dialog (item 1 of argv) buttons {"OK"} default button "OK" with title "Koʻz"\nend run', message], { stdio: 'ignore' });
    process.exitCode = 1;
  }
}
