import http from 'node:http';
import { randomBytes, createHash, scryptSync, timingSafeEqual } from 'node:crypto';
import { readFile, writeFile, appendFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { resolve, extname } from 'node:path';
import { WebSocketServer, WebSocket } from 'ws';
import { readEvent, parseStrict, validateCommandData, ContractError } from '../src/protocol.js';
import { createModel, ingest, liveView, summaryFor, invalidateLive } from '../src/model.js';

import { connectRunner } from './runner-link.mjs';
import { createFakeRunner } from './fake-runner.mjs';

const id=()=>randomBytes(16).toString('hex'),hash=v=>createHash('sha256').update(v).digest('hex');
const root=fileURLToPath(new URL('../',import.meta.url));
export async function createApplication({password='',dataDir=resolve(root,'.data'),persist=true,localRunnerUrl=null,localAccess=false,retryMs=1000}={}){
 const realModel=createModel(),sessions=new Map(),subscribers=new Set(),attempts=new Map();
 let model=realModel,realSaved=[],fake=null,link=null,closing=false;
 let transport={mode:localRunnerUrl?'local':'inbound',url:localRunnerUrl,state:'disconnected',source:'runner',replayOwned:false};
 let runner=null,runnerSession=null,tokenHash=null,saved=[],commandTimer=null,activeTrial=null;
 const subscriberSessions=new Map();
 const passwordSalt=randomBytes(16),passwordHash=password?scryptSync(password,passwordSalt,32):null;
 const historyFile=resolve(dataDir,'events.ndjson'),metaFile=resolve(dataDir,'owner.json');
 if(persist){await mkdir(dataDir,{recursive:true,mode:0o700});try{const meta=JSON.parse(await readFile(metaFile,'utf8'));tokenHash=meta.tokenHash||null;saved=meta.saved||[];}catch{}try{for(const line of (await readFile(historyFile,'utf8')).split('\n').filter(Boolean)){const row=JSON.parse(line);if(row.expiresAt>Date.now())ingest(model,row.event,row.receivedAt);}}catch{}}
 realSaved=saved;
 // A persisted old heartbeat never reconnects a device after a web restart.
 model.statusAt=0;
 let persistence=Promise.resolve();
 const persistMeta=async()=>{if(model!==realModel)return;realSaved=saved;if(persist){const content=JSON.stringify({tokenHash,saved});persistence=persistence.catch(()=>{}).then(()=>writeFile(metaFile,content,{mode:0o600}));await persistence;}};
 const broadcast=packet=>{for(const response of subscribers)response.write(`data: ${JSON.stringify(packet)}\n\n`);};
 const receive=event=>{
  const at=Date.now(),prior=model.status;
  const unchanged=event.type==='status'&&prior?.session_id===event.session_id&&prior?.job_id===event.job_id&&prior?.trial_id===event.trial_id&&prior?.revision===event.revision&&JSON.stringify(prior.data)===JSON.stringify(event.data);
  if(!ingest(model,event,at))return;
  if(unchanged)model.events=model.events.filter(r=>r.event!==event);
  if(persist&&model===realModel&&!unchanged){const row=model.events.find(r=>r.event===event);if(row)persistence=persistence.then(()=>appendFile(historyFile,JSON.stringify({...row,receivedAt:Math.floor(at/60000)*60000})+'\n',{mode:0o600})).catch(()=>broadcast({error:'INTERNAL_ERROR'}));}
  if(event.type==='status'&&!event.trial_id&&['idle','running'].includes(event.data.state))activeTrial=null;
  if(event.type==='command_result'&&event.data.result==='rejected'&&model.pending?.command==='begin_trial')activeTrial=null;
  if(event.type==='status'&&model.status===event)transport={...transport,state:'connected'};
  broadcast({event,receivedAt:at,activeTrial,transport});
 };
 const json=(res,status,data)=>{res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(JSON.stringify(data));};
 const authenticated=req=>{const token=(req.headers.cookie||'').split(';').map(s=>s.trim()).find(s=>s.startsWith('koz_session='))?.slice(12);const expires=sessions.get(token);return expires&&expires>Date.now();};
 const body=async req=>{const chunks=[];let size=0;for await(const chunk of req){size+=chunk.length;if(size>32768)throw new ContractError('INVALID_COMMAND');chunks.push(chunk);}return parseStrict(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks)),32768,'INVALID_COMMAND');};
 const server=http.createServer(async(req,res)=>{
  res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','no-referrer');
  const url=new URL(req.url,'http://localhost');
  if(!['localhost','127.0.0.1','[::1]'].includes((req.headers.host||'').replace(/:\d+$/,'')))return json(res,403,{code:'AUTH_REQUIRED'});
  try{
   if(url.pathname.startsWith('/api/')){
    if(req.headers['sec-fetch-site']==='cross-site'||req.method!=='GET'&&req.headers.origin&&req.headers.origin!==`http://${req.headers.host}`)return json(res,403,{code:'AUTH_REQUIRED'});
    if(url.pathname==='/api/health'&&req.method==='GET')return json(res,200,{service:'koz-web',workspace:hash(resolve(root))});
    if(url.pathname==='/api/session'&&req.method==='GET'){
     if(localAccess&&!passwordHash&&!authenticated(req)){const session=randomBytes(32).toString('hex');sessions.set(session,Date.now()+8*3600000);res.setHeader('Set-Cookie',`koz_session=${session}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800`);return json(res,200,{authenticated:true,configured:false,transport});}
     return json(res,200,{authenticated:Boolean(authenticated(req)),configured:Boolean(passwordHash),transport});
    }
    if(url.pathname==='/api/login'&&req.method==='POST'){
     const key=req.socket.remoteAddress,rate=attempts.get(key)||{count:0,until:Date.now()+300000};
     if(rate.until<Date.now()){rate.count=0;rate.until=Date.now()+300000;}rate.count++;attempts.set(key,rate);
     const data=await body(req);
     if(!data||typeof data!=='object')return json(res,401,{code:'AUTH_REQUIRED'});
     if(rate.count>8||!passwordHash||typeof data.password!=='string'||data.password.length>256||Object.keys(data).length!==1||!timingSafeEqual(passwordHash,scryptSync(data.password,passwordSalt,32)))return json(res,401,{code:'AUTH_REQUIRED'});
     attempts.delete(key);const session=randomBytes(32).toString('hex');sessions.set(session,Date.now()+8*3600000);res.setHeader('Set-Cookie',`koz_session=${session}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800`);return json(res,200,{ok:true});
    }
    if(!authenticated(req))return json(res,401,{code:'AUTH_REQUIRED'});
    if(url.pathname==='/api/logout'&&req.method==='POST'){sessions.clear();for(const client of subscribers)client.end();subscribers.clear();res.setHeader('Set-Cookie','koz_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0');return json(res,200,{ok:true});}
    if(url.pathname==='/api/snapshot'&&req.method==='GET'){
     const rows=model.events.filter(r=>r.expiresAt>Date.now());
     const latest=model.status&&{event:model.status,receivedAt:model.statusAt};
     return json(res,200,{events:latest?[...rows.filter(r=>r.event!==model.status),latest]:rows,pending:model.pending,statusAt:model.statusAt,activeTrial,saved,transport});
    }
    if(url.pathname==='/api/events'&&req.method==='GET'){
     res.writeHead(200,{'Content-Type':'text/event-stream','Cache-Control':'no-store','Connection':'keep-alive'});res.write(': connected\n\n');subscribers.add(res);subscriberSessions.set(res,sessions.get((req.headers.cookie||'').split(';').map(s=>s.trim()).find(s=>s.startsWith('koz_session='))?.slice(12)));req.on('close',()=>{subscribers.delete(res);subscriberSessions.delete(res);});return;
    }
    if(url.pathname==='/api/replay'&&req.method==='POST'){
     if(!localRunnerUrl)throw new ContractError('INVALID_COMMAND');
     const data=await body(req);if(!data||Object.keys(data).join(',')!=='action'||!['start','stop'].includes(data.action))throw new ContractError('INVALID_COMMAND');
     if(data.action==='stop'){if(fake){await fake.close();fake=null;}else if(transport.source==='replay')throw new ContractError('BUSY');}
     else {if(runner?.readyState===WebSocket.OPEN&&transport.source!=='replay')throw new ContractError('BUSY');if(fake){await fake.close();fake=null;}try{fake=await createFakeRunner({port:Number(new URL(localRunnerUrl).port)});}catch(error){if(error.code==='EADDRINUSE')throw new ContractError('BUSY');throw error;}}
     transport={...transport,replayOwned:Boolean(fake)};broadcast({transport});return json(res,200,{transport});
    }
    if(url.pathname==='/api/runner-token'&&req.method==='POST'){
     if(localRunnerUrl)throw new ContractError('INVALID_COMMAND');
     const token=randomBytes(32).toString('hex');tokenHash=hash(token);runner?.close(1008,'AUTH_REQUIRED');runner=null;runnerSession=null;await persistMeta();return json(res,200,{token});
    }
    if(url.pathname==='/api/commands'&&req.method==='POST'){
     const input=await body(req);
     if(!input||Object.keys(input).sort().join(',')!=='command,data')throw new ContractError('INVALID_COMMAND');
     if(!runner||runner.readyState!==WebSocket.OPEN||liveView(model).offline)throw new ContractError('AUTH_REQUIRED');
     validateCommandData(input.command,input.data,model.status.data.capabilities);
     const state=model.status.data.state;
     if(input.command==='start_job'&&!['idle','held','refused'].includes(state)||input.command==='begin_trial'&&(!['idle','held','refused'].includes(state)||model.trial)||input.command==='finish_trial'&&!model.trial)throw new ContractError('BUSY');
     if(input.command==='start_job'&&model.trial&&model.events.some(r=>r.event.trial_id===model.trial&&r.event.job_id&&['recipe','observation','decision'].includes(r.event.type)))throw new ContractError('BUSY');
     if(model.pending&&!model.pending.failed&&input.command!=='stop_job')throw new ContractError('BUSY');
     const command={v:1,type:'command',command_id:id(),session_id:runnerSession,job_id:input.command==='start_job'?id():input.command==='begin_trial'?null:model.status.job_id,trial_id:input.command==='begin_trial'?id():model.trial,expires_at:Math.floor(Date.now()/1000)+10,command:input.command,data:input.data};
     model.pending={command_id:command.command_id,command:command.command,job_id:command.job_id,session_id:command.session_id,trial_id:command.trial_id,expires_at:command.expires_at};
     if(input.command==='begin_trial')activeTrial={trial_id:command.trial_id,...input.data};
     runner.send(JSON.stringify(command));clearTimeout(commandTimer);commandTimer=setTimeout(()=>{if(model.pending?.command_id===command.command_id){model.pending=null;broadcast({commandExpired:command.command_id});}},10000);
     return json(res,202,model.pending);
    }
    if(url.pathname==='/api/summaries'&&req.method==='POST'){
     const data=await body(req);if(!data||Object.keys(data).join(',')!=='trial_id')throw new ContractError('INVALID_COMMAND');
     const record=model.events.find(r=>r.event.type==='trial_result'&&r.event.trial_id===data.trial_id&&r.expiresAt>Date.now());if(!record)throw new ContractError('INVALID_COMMAND');
     const summary=summaryFor(record.event);if(!saved.some(s=>s.trial_id===summary.trial_id))saved.push(summary);await persistMeta();return json(res,200,{saved});
    }
    if(url.pathname.startsWith('/api/summaries/')&&req.method==='DELETE'){const trial=url.pathname.slice(15);if(!/^[a-f0-9]{32}$/.test(trial))throw new ContractError('INVALID_COMMAND');saved=saved.filter(s=>s.trial_id!==trial);await persistMeta();return json(res,200,{saved});}
    return json(res,404,{code:'INVALID_COMMAND'});
   }
   if(req.method!=='GET'&&req.method!=='HEAD')return json(res,405,{code:'INVALID_COMMAND'});
   const name=url.pathname==='/'?'index.html':decodeURIComponent(url.pathname).replace(/^\//,'');
   const path=resolve(root,'dist',name);if(!path.startsWith(resolve(root,'dist')+'/'))return json(res,404,{code:'INVALID_COMMAND'});
   const content=await readFile(path);const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.ttf':'font/ttf','.txt':'text/plain'};
   res.setHeader('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
   res.writeHead(200,{'Content-Type':`${types[extname(path)]||'application/octet-stream'}; charset=utf-8`,'Cache-Control':'no-cache'});res.end(req.method==='HEAD'?undefined:content);
  }catch(error){json(res,error instanceof ContractError?400:500,{code:error instanceof ContractError?error.code:'INTERNAL_ERROR'});}
 });
 function disconnected(){
  if(closing)return;
  invalidateLive(model);clearTimeout(commandTimer);
  transport={...transport,state:'disconnected'};broadcast({transport});
 }
 function attachRunner(ws,source='runner'){
  runner?.terminate();runner=ws;runnerSession=null;
  if(source!==transport.source){
   if(source==='replay'){realSaved=saved;model=createModel();saved=[];}
   else {model=realModel;saved=realSaved;}
   activeTrial=null;
  }
  invalidateLive(model);
  transport={...transport,source,state:'connecting',replayOwned:Boolean(fake)};
  broadcast({reset:true,transport});
  ws.on('message',(data,isBinary)=>{if(runner!==ws)return;try{
   if(isBinary)throw new ContractError();const event=readEvent(new TextDecoder('utf-8',{fatal:true}).decode(data));
   if(!runnerSession){if(event.type!=='status')throw new ContractError();runnerSession=event.session_id;}
   if(event.session_id!==runnerSession)throw new ContractError();receive(event);
  }catch{ws.send(JSON.stringify({v:1,type:'protocol_error',code:'INVALID_EVENT'}));ws.close(1008,'INVALID_EVENT');}});
  ws.on('close',()=>{if(runner===ws){runner=null;runnerSession=null;disconnected();}});ws.on('error',()=>{});
 }
 const wss=new WebSocketServer({noServer:true,maxPayload:32768,perMessageDeflate:false});
 server.on('upgrade',(req,socket,head)=>{
  const supplied=req.headers.authorization?.startsWith('Bearer ')?req.headers.authorization.slice(7):'';
  if(localRunnerUrl||req.url!=='/v1/runner'||!supplied||!tokenHash||!timingSafeEqual(Buffer.from(tokenHash,'hex'),Buffer.from(hash(supplied),'hex'))){socket.end('HTTP/1.1 401 Unauthorized\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{"code":"AUTH_REQUIRED"}');return;}
  wss.handleUpgrade(req,socket,head,ws=>attachRunner(ws));
 });
 if(localRunnerUrl)link=connectRunner({url:localRunnerUrl,onSocket:attachRunner,onWaiting:disconnected,retryMs});
 const freshness=setInterval(()=>{
  if(transport.state==='connected'&&liveView(model).offline){invalidateLive(model);transport={...transport,state:'waiting'};broadcast({transport});}
 },250);freshness.unref();
 const maintenance=setInterval(()=>{
  for(const [session,expires]of sessions)if(expires<Date.now())sessions.delete(session);
  const before=realModel.events.length;realModel.events=realModel.events.filter(r=>r.expiresAt>Date.now());if(model!==realModel)model.events=model.events.filter(r=>r.expiresAt>Date.now());
  if(persist&&before!==realModel.events.length)persistence=persistence.then(()=>writeFile(historyFile,realModel.events.map(r=>JSON.stringify({...r,receivedAt:Math.floor(r.receivedAt/60000)*60000})).join('\n')+'\n',{mode:0o600})).catch(()=>broadcast({error:'INTERNAL_ERROR'}));
  for(const res of subscribers){if(subscriberSessions.get(res)<Date.now()){res.end();subscribers.delete(res);subscriberSessions.delete(res);}else res.write(': heartbeat\n\n');}
 },30000);maintenance.unref();
 return {server,get model(){return model;},close:async()=>{closing=true;link?.close();await fake?.close();clearInterval(freshness);clearInterval(maintenance);clearTimeout(commandTimer);runner?.terminate();for(const r of subscribers)r.end();wss.close();await persistence;await new Promise(resolve=>server.close(resolve));}};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
 const env=resolve(root,'.env');if(existsSync(env))process.loadEnvFile(env);
 const app=await createApplication({password:process.env.KOZ_OWNER_PASSWORD||'',localRunnerUrl:'ws://127.0.0.1:8765',localAccess:true});
 const port=Number(process.env.PORT)||4173;app.server.listen(port,'127.0.0.1',()=>console.log(`Koʻz web: http://127.0.0.1:${port}`));
 for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>app.close().then(()=>process.exit(0)));
}
