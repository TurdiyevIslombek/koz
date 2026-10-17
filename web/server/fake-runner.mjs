import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { WebSocketServer, WebSocket } from 'ws';
import { DemoRunner } from '../src/demo.js';
import { readCommand, validateEvent, newId } from '../src/protocol.js';

const fixturePath = new URL('../fixtures/runner-session.json', import.meta.url);

// A fixture-backed runner, never a camera. Each connection has its own replay/session.
export async function createFakeRunner({ port = 8765, timeScale = 1 } = {}) {
  const recording = JSON.parse(await readFile(fixturePath, 'utf8'));
  for (const row of recording.events) validateEvent(row.event);
  const server = http.createServer((_req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ service: 'koz-recorded-runner', source: 'replay' }));
  });
  const wss = new WebSocketServer({ server, maxPayload: 32768, perMessageDeflate: false });
  wss.on('headers', headers => headers.push('X-Koz-Source: replay'));
  const cleanups = new Set();
  wss.on('connection', (socket, request) => {
    // Replay has no video. Do not start another event replay on the preview socket.
    if (request.url === '/v1/preview') {
      socket.send(JSON.stringify({v:1,type:'preview',state:'closed',reason:'not_running'}));
      socket.on('error',()=>{});
      return;
    }
    const commandResults = new Map(), ids = new Map(), sequences = new Map(), replayTimers = new Set();
    const mappedId = id => {
      if (id === null) return null;
      if (!ids.has(id)) ids.set(id, newId());
      return ids.get(id);
    };
    const runner = new DemoRunner(event => {
      if (event.type === 'command_result') commandResults.set(event.data.command_id, event.data);
      if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify(event));
    });
    const cancelReplay = () => { for (const timer of replayTimers) clearTimeout(timer); replayTimers.clear(); };
    const cleanup = () => { cancelReplay(); runner.destroy(); cleanups.delete(cleanup); };
    cleanups.add(cleanup);
    socket.on('close', cleanup);
    socket.on('error', () => {});
    function replay(row) {
      const original = row.event, data = structuredClone(original.data);
      const job = mappedId(original.job_id), trial = mappedId(original.trial_id);
      if (runner.job !== job) { runner.reason = null; runner.gapped = false; }
      runner.job = job; runner.trial = trial; runner.revision = original.revision || runner.revision;
      if (original.type === 'status') runner.state = data.state;
      if (original.type === 'recipe') {
        runner.recipe = data.recipe;
        runner.kind = data.recipe.brain.type === 'flybrain' ? 'red_ball' : 'counter';
        if (data.caused_by !== null) data.caused_by = sequences.get(data.caused_by);
      }
      if (original.type === 'observation') {
        runner.reason = data.unknown_reason;
        runner.gapped = data.coverage === 'gapped';
        for (const [field, property] of [['occupancy','count'],['entered','entered'],['exited','exited']]) {
          if (data[field]?.state === 'known') runner[property] = data[field].value;
        }
      }
      if (original.type === 'decision') data.evidence_seq = data.evidence_seq.map(seq => sequences.get(seq));
      if (trial) runner.trialInfo = { demo: runner.kind === 'red_ball' ? 'red_ball' : 'classroom', index: 1 };
      const event = runner.event(original.type, data, { job, trial, revision: original.revision });
      sequences.set(original.seq, event.seq);
    }
    replay(recording.events[0]); // The first message is always status.
    for (const row of recording.events.slice(1)) {
      const timer = setTimeout(() => { replayTimers.delete(timer); replay(row); }, row.at_ms * timeScale);
      replayTimers.add(timer);
    }
    socket.on('message', (bytes, binary) => {
      let command;
      try {
        if (binary) throw Error('binary');
        command = readCommand(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
      } catch {
        socket.close(1008, 'INVALID_COMMAND');
        return;
      }
      const reject = code => runner.event('command_result', { command_id: command.command_id, result: 'rejected', code }, { revision: null });
      if (commandResults.has(command.command_id)) {
        runner.event('command_result', commandResults.get(command.command_id), { revision: null }); return;
      }
      if (command.expires_at < Math.floor(Date.now() / 1000)) return reject('COMMAND_EXPIRED');
      if (command.session_id !== runner.session) return reject('INVALID_COMMAND');
      if (command.command === 'start_job' && (!['idle','held','refused'].includes(runner.state) || !command.job_id || command.trial_id !== runner.trial)) return reject('BUSY');
      if (command.command === 'begin_trial' && (!['idle','held','refused'].includes(runner.state) || runner.trial || !command.trial_id || command.job_id !== null)) return reject('BUSY');
      if (command.command === 'finish_trial' && (!runner.trial || command.trial_id !== runner.trial)) return reject('INVALID_COMMAND');
      if (['stop_job','finish_trial'].includes(command.command) && command.job_id !== runner.job) return reject('INVALID_COMMAND');
      cancelReplay(); // A late replay step must never undo Stop or a new owner command.
      commandResults.set(command.command_id, { command_id: command.command_id, result: 'accepted', code: null });
      runner.command(command.command, command.data, command.data.language || 'uz', command);
    });
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(port, '127.0.0.1', resolve); });
  return {
    server,
    port: server.address().port,
    close: async () => {
      for (const cleanup of [...cleanups]) cleanup();
      for (const client of wss.clients) client.terminate();
      await new Promise(resolve => wss.close(resolve));
      await new Promise(resolve => server.close(resolve));
    }
  };
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    const fake = await createFakeRunner();
    console.log(`Koʻz recorded fixture: ws://127.0.0.1:${fake.port} (not camera measurements)`);
    for (const signal of ['SIGINT','SIGTERM']) process.on(signal, () => fake.close().then(() => process.exit(0)));
  } catch (error) {
    console.error(error.code === 'EADDRINUSE' ? 'Port 8765 is in use. The existing runner was left untouched.' : 'The recorded runner could not start.');
    process.exitCode = 1;
  }
}
