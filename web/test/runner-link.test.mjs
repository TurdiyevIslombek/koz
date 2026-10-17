import test from 'node:test';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { WebSocketServer } from 'ws';
import { createApplication } from '../server/index.mjs';
import { createFakeRunner } from '../server/fake-runner.mjs';
import { liveView, evidenceChains } from '../src/model.js';
import { recipeFor, sampleEvidence, known } from '../src/demo.js';
import { launch, probeWeb } from '../scripts/open-web.mjs';

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(condition, timeout = 4000) {
  const end = Date.now() + timeout;
  while (!condition()) { if (Date.now() > end) throw Error('Condition timed out'); await delay(20); }
}
async function web(url, options = {}) {
  const app = await createApplication({ persist: false, localAccess: true, localRunnerUrl: url, retryMs: 80, ...options });
  app.server.listen(0, '127.0.0.1'); await once(app.server, 'listening');
  const origin = `http://127.0.0.1:${app.server.address().port}`;
  const session = await fetch(origin + '/api/session');
  const cookie = session.headers.get('set-cookie')?.split(';')[0];
  const api = async (path, data) => {
    const response = await fetch(`${origin}/api/${path}`, { method: data ? 'POST' : 'GET', headers: { Cookie: cookie, 'Content-Type':'application/json' }, body: data ? JSON.stringify(data) : undefined });
    return { status: response.status, data: await response.json() };
  };
  return { app, api, origin };
}

test('recorded socket replay contains zero, privacy hold and a verified adjustment; all four commands use that connection', async () => {
  const fake = await createFakeRunner({ port: 0, timeScale: .05 });
  const { app, api } = await web(`ws://127.0.0.1:${fake.port}`);
  try {
    await until(() => app.model.events.some(r => r.event.type === 'trial_result'));
    assert.equal((await api('snapshot')).data.transport.source, 'replay');
    assert.ok(app.model.events.some(r => r.event.type === 'observation' && r.event.data.occupancy?.value === 0));
    assert.ok(app.model.events.some(r => r.event.type === 'fault' && r.event.data.code === 'PRIVATE_BATHROOM'));
    assert.equal(evidenceChains(app.model).find(c => c.decision.data.next === 'adjust').complete, true);
    await until(() => app.model.status.data.state === 'idle');
    const sent = [];
    async function command(name, data, finished) {
      const response = await api('commands', { command: name, data });
      assert.equal(response.status, 202); sent.push(response.data.command_id);
      await until(() => app.model.events.some(r => r.event.type === 'command_result' && r.event.data.command_id === response.data.command_id));
      await until(finished);
    }
    await command('begin_trial', { demo:'classroom', index:2 }, () => Boolean(app.model.trial) && !app.model.pending);
    const trial = app.model.trial;
    await command('start_job', { input:'recipe', recipe:recipeFor('classroom') }, () => app.model.status.data.state === 'running');
    assert.equal(liveView(app.model).counts[0].value, 0);
    await command('stop_job', {}, () => app.model.status.data.state === 'idle');
    await command('finish_trial', { result:'pass', reason:'none', expected_count:0 }, () => !app.model.trial);
    assert.ok(app.model.events.some(r => r.event.type === 'trial_result' && r.event.trial_id === trial));
    assert.equal(new Set(sent).size, 4);
  } finally { await app.close(); await fake.close(); }
});

test('close and silent heartbeat loss clear readings; reconnect never restores an old count or replays a command', async () => {
  const wss = new WebSocketServer({ port:0, host:'127.0.0.1' }); await once(wss, 'listening');
  const base = sampleEvidence()[0]; let seq = 0, current, connections = 0; const commands = [];
  const send = (type, data) => current.send(JSON.stringify({ ...base, trial_id:null, minute:Math.floor(Date.now()/60000), seq:++seq, type, data }));
  const status = { ...base.data, state:'running' };
  const observation = { ...sampleEvidence()[2].data, round:null, target:null, occupancy:known(7), entered:known(9), exited:known(2) };
  wss.on('connection', (socket,request) => { if(request.url==='/v1/preview'){socket.send(JSON.stringify({v:1,type:'preview',state:'closed',reason:'not_running'}));return;}current=socket; connections++;socket.on('message', data=>commands.push(JSON.parse(data)));send('status',status);if(connections===1)send('observation',observation); });
  const { app, api } = await web(`ws://127.0.0.1:${wss.address().port}`);
  try {
    await until(() => liveView(app.model).counts[0]?.value === 7);
    current.terminate();
    await until(() => app.model.statusAt === 0);
    assert.equal(liveView(app.model).state,'unknown');
    assert.equal(liveView(app.model).counts[0].value,null);
    assert.equal((await api('commands',{command:'stop_job',data:{}})).status,400);
    await until(() => connections === 2 && app.model.statusAt > 0);
    assert.equal(liveView(app.model).counts[0].value,null);
    assert.equal(commands.length,0);
    send('observation',{...observation,occupancy:known(0)});
    await until(() => liveView(app.model).counts[0]?.value === 0);
    await until(() => liveView(app.model).offline,4000);
    assert.equal(liveView(app.model).state,'unknown');
    assert.equal(liveView(app.model).counts[0].value,null);
    send('status',status);await delay(50);
    assert.equal(liveView(app.model).counts[0].value,null);
    send('observation',observation);await until(()=>liveView(app.model).counts[0]?.value===7);
    assert.equal((await api('replay',{action:'start'})).data.code,'BUSY');
  } finally { await app.close();for(const client of wss.clients)client.terminate();await new Promise(resolve=>wss.close(resolve)); }
});

test('local session remains same-origin; launcher reuses its own server; replay history never becomes real history', async () => {
  const fake = await createFakeRunner({port:0,timeScale:.02}), port=fake.port;
  const {app,api,origin}=await web(`ws://127.0.0.1:${port}`);let real;
  try {
    assert.equal((await fetch(origin+'/api/session',{headers:{'Sec-Fetch-Site':'cross-site'}})).status,403);
    assert.equal(await probeWeb(origin),'ours');
    assert.equal((await launch({port:app.server.address().port,openBrowser:false})).reused,true);
    await until(()=>app.model.events.some(r=>r.event.type==='trial_result'));
    const result=app.model.events.find(r=>r.event.type==='trial_result').event;
    await api('summaries',{trial_id:result.trial_id});
    assert.equal((await api('snapshot')).data.saved.length,1);
    await fake.close();
    real=new WebSocketServer({port,host:'127.0.0.1'});await once(real,'listening');
    real.on('connection',socket=>{const e=sampleEvidence()[0];e.trial_id=null;e.job_id=null;e.revision=null;e.data.state='idle';socket.send(JSON.stringify(e));});
    await until(()=>app.model.status?.job_id===null&&app.model.statusAt>0);
    const snapshot=(await api('snapshot')).data;
    assert.equal(snapshot.transport.source,'runner');
    assert.equal(snapshot.saved.length,0);
    assert.equal(snapshot.events.some(r=>r.event.type==='trial_result'),false);
  } finally {await app.close();if(real){for(const client of real.clients)client.terminate();await new Promise(resolve=>real.close(resolve));}else await fake.close();}
});

test('launcher starts a fresh local server and a second launch reuses it', async () => {
  const reserve = new WebSocketServer({ port:0, host:'127.0.0.1' });await once(reserve,'listening');
  const port=reserve.address().port;await new Promise(resolve=>reserve.close(resolve));
  const result=await launch({port,openBrowser:false});
  try {
    assert.equal(result.reused,false);assert.ok(result.pid>0);
    assert.equal(await probeWeb(result.url),'ours');
    assert.equal((await launch({port,openBrowser:false})).reused,true);
    const {stat}=await import('node:fs/promises');
    assert.ok((await stat(new URL('../../open-web.command',import.meta.url))).mode&0o111);
  } finally {process.kill(result.pid,'SIGTERM');await delay(100);}
});
