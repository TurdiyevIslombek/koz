import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {once} from 'node:events';
import {mkdtemp,readFile,readdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {setTimeout as delay} from 'node:timers/promises';
import {WebSocket,WebSocketServer} from 'ws';
import {createApplication} from '../server/index.mjs';
import {eyeRequestAllowed} from '../server/eye.mjs';
import {eyeClosed,readEyeClosed,validEyeJPEG,MAX_EYE_BYTES,MAX_EYE_WIDTH} from '../src/eye-protocol.js';
import {sampleEvidence} from '../src/demo.js';

// Construct a JPEG header in memory for transport tests. Not a camera or recorded fixture.
export function jpegHeader(width=320) {
 const data=Buffer.alloc(32); data.set([255,216,255,192,0,11,8,0,180,width>>8,width&255,1,1,17,0,255,218]);
 data[data.length-2]=255; data[data.length-1]=217; return data;
}
const until=async predicate=>{for(let n=0;n<300;n++){if(predicate())return;await delay(10);}throw Error('Timed out');};
async function fixture(t,{localAccess=true,persist=false}={}) {
 const upstream=http.createServer(),wss=new WebSocketServer({server:upstream,perMessageDeflate:false});
 const sockets={events:[],preview:[]},headers=[];
 wss.on('connection',(ws,req)=>{sockets[req.url==='/v1/preview'?'preview':'events'].push(ws);headers.push(req.headers);});
 upstream.listen(0,'127.0.0.1');await once(upstream,'listening');
 const dir=await mkdtemp(join(tmpdir(),'koz-eye-test-'));
 const app=await createApplication({localAccess,localRunnerUrl:`ws://127.0.0.1:${upstream.address().port}`,persist,dataDir:dir,retryMs:20,password:localAccess?'':'test-password'});
 app.server.listen(0,'127.0.0.1');await once(app.server,'listening');
 const origin=`http://127.0.0.1:${app.server.address().port}`,clients=[];
 t.after(async()=>{for(const ws of clients)ws.terminate();if(app.server.listening)await app.close();for(const group of Object.values(sockets))for(const ws of group)ws.terminate();await new Promise(r=>wss.close(r));await new Promise(r=>upstream.close(r));await rm(dir,{recursive:true,force:true});});
 const session=await fetch(origin+'/api/session');const cookie=session.headers.get('set-cookie')?.split(';')[0];
 await until(()=>sockets.events.length&&(!localAccess||sockets.preview.length));
 let seq=0;const base=sampleEvidence()[0];
 async function status(state='running',privacy='approved') {sockets.events.at(-1).send(JSON.stringify({...base,seq:++seq,data:{...base.data,state,privacy,camera_on:['running','evaluating','checking'].includes(state)}}));await until(()=>app.model.status?.seq===seq);}
 async function viewer(extra={}) {
  const ws=new WebSocket(origin.replace('http:','ws:')+'/api/eye',{headers:{Cookie:cookie,Origin:origin,...extra},perMessageDeflate:false});clients.push(ws);
  const packets=[];let responseHeaders;
  ws.on('upgrade',res=>responseHeaders=res.headers);ws.on('message',(data,binary)=>packets.push(binary?{binary,data}:{...JSON.parse(data),binary:false}));
  await once(ws,'open');await until(()=>packets.length);return {ws,packets,headers:responseHeaders};
 }
 return {app,sockets,headers,origin,cookie,status,viewer,dir};
}

test('preview grammar rejects extra fields, duplicates, malformed JPEGs and oversized frames',()=>{
 for(const reason of ['checking','not_running','not_fresh'])assert.deepEqual(readEyeClosed(JSON.stringify(eyeClosed(reason))),eyeClosed(reason));
 for(const text of ['{}','{"v":1,"v":1,"type":"preview","state":"closed","reason":"checking"}',JSON.stringify({...eyeClosed('checking'),frame:'no'}),JSON.stringify(eyeClosed('other'))])assert.throws(()=>readEyeClosed(text));
 assert.equal(validEyeJPEG(jpegHeader()),true);assert.equal(validEyeJPEG(jpegHeader(MAX_EYE_WIDTH)),true);assert.equal(validEyeJPEG(jpegHeader(MAX_EYE_WIDTH+1)),false);   // 640 px since Oct 18
 assert.equal(validEyeJPEG(Buffer.alloc(MAX_EYE_BYTES+1)),false);assert.equal(validEyeJPEG(Buffer.from('not a JPEG')),false);
});
test('eye requests require an owner, loopback address and exact same origin',()=>{
 const req={method:'GET',url:'/api/eye',headers:{host:'127.0.0.1:4173',origin:'http://127.0.0.1:4173'},socket:{remoteAddress:'127.0.0.1'}};
 assert.equal(eyeRequestAllowed(req,()=>true),true);
 assert.equal(eyeRequestAllowed(req,()=>false),false);
 assert.equal(eyeRequestAllowed({...req,socket:{remoteAddress:'198.51.100.7'}},()=>true),false);
 for(const origin of [undefined,'http://evil.example','null'])assert.equal(eyeRequestAllowed({...req,headers:{...req.headers,origin}},()=>true),false);
});
test('one local upstream serves memory-only JPEGs; closed, stops and disconnect discard them',async t=>{
 const f=await fixture(t,{persist:true});await f.status();const a=await f.viewer(),b=await f.viewer();
 assert.equal(f.sockets.preview.length,1);assert.ok(f.headers.every(h=>!h.origin));assert.equal(a.headers['cache-control'],'no-store');assert.equal(a.headers.etag,undefined);assert.equal(a.headers['sec-websocket-extensions'],undefined);
 const frame=jpegHeader();f.sockets.preview[0].send(frame);await until(()=>a.packets.at(-1).binary&&b.packets.at(-1).binary);
 assert.deepEqual(a.packets.at(-1).data,frame);
 f.sockets.preview[0].send(JSON.stringify(eyeClosed('checking')));await until(()=>a.packets.at(-1).reason==='checking');
 const c=await f.viewer();assert.equal(c.packets[0].binary,false);assert.equal(c.packets[0].reason,'checking');
 f.sockets.preview[0].send(frame);await until(()=>a.packets.at(-1).binary);
 await f.status('held','blocked');await until(()=>a.packets.at(-1).reason==='not_running');
 const cut=a.packets.length;f.sockets.preview[0].send(frame);await delay(30);assert.equal(a.packets.length,cut);
 await f.status();f.sockets.preview[0].send(frame);await until(()=>a.packets.at(-1).binary);
 f.sockets.preview[0].terminate();await until(()=>a.packets.at(-1).reason==='not_fresh');
 const d=await f.viewer();assert.equal(d.packets[0].binary,false);
 await until(()=>f.sockets.preview.length===2);f.sockets.preview[1].send(frame);await until(()=>a.packets.at(-1).binary);
 f.sockets.events[0].terminate();await until(()=>a.packets.at(-1).binary===false);
 const before=a.packets.length;f.sockets.preview[1].send(frame);await delay(30);assert.equal(a.packets.length,before);
 await f.app.close();
 for(const name of await readdir(f.dir)){
  assert.ok(['events.ndjson','owner.json'].includes(name));const bytes=await readFile(join(f.dir,name));
  assert.equal(bytes.includes(frame),false);assert.doesNotMatch(bytes.toString(),/data:image|base64|"preview"/);
 }
});
test('newest frame expires after one second even while status continues; rejoining gets no old image',async t=>{
 const f=await fixture(t);await f.status();const viewer=await f.viewer();f.sockets.preview[0].send(jpegHeader());await until(()=>viewer.packets.at(-1).binary);
 const late=await f.viewer();assert.equal(late.packets[0].binary,false);
 await until(()=>viewer.packets.at(-1).reason==='not_fresh');assert.equal(viewer.packets.at(-1).binary,false);
});
test('invalid upstream messages close and reconnect, never arriving at browser or event storage',async t=>{
 const f=await fixture(t);await f.status();const viewer=await f.viewer();
 for(const invalid of [JSON.stringify({...eyeClosed('checking'),extra:true}),JSON.stringify(eyeClosed('unknown')),Buffer.from('bad jpeg'),Buffer.alloc(MAX_EYE_BYTES+1)]){
  const count=f.sockets.preview.length;f.sockets.preview.at(-1).send(jpegHeader());await until(()=>viewer.packets.at(-1).binary);
  f.sockets.preview.at(-1).send(invalid);await until(()=>f.sockets.preview.length>count);
  assert.equal(viewer.packets.at(-1).binary,false);assert.ok(f.app.model.events.every(r=>r.event.type!=='preview'));
 }
});
test('unauthenticated and cross-origin sockets are refused, logout closes an existing eye',async t=>{
 const f=await fixture(t);await f.status();
 const remoteResponse=await new Promise(resolve=>{
  const req={url:'/api/eye',method:'GET',headers:{host:new URL(f.origin).host,origin:f.origin,cookie:f.cookie},socket:{remoteAddress:'198.51.100.7'}};
  const res={setHeader(){},writeHead(code){this.code=code;},end(){resolve(this.code);}};
  f.app.server.emit('request',req,res);
 });assert.equal(remoteResponse,403);
 for(const headers of [{Origin:f.origin},{Origin:'http://evil.example',Cookie:f.cookie}]){
  const ws=new WebSocket(f.origin.replace('http:','ws:')+'/api/eye',{headers});ws.on('error',()=>{});
  const code=await new Promise(resolve=>ws.on('unexpected-response',(_req,res)=>{resolve(res.statusCode);res.resume();ws.terminate();}));assert.equal(code,403);
 }
 const viewer=await f.viewer(),closed=once(viewer.ws,'close');
 await fetch(f.origin+'/api/logout',{method:'POST',headers:{Cookie:f.cookie,Origin:f.origin}});await closed;
});
test('session expiry terminates an already open eye stream',async t=>{
 const f=await fixture(t);await f.status();const viewer=await f.viewer();
 const closed=once(viewer.ws,'close');
 t.mock.timers.enable({apis:['Date'],now:Date.now()+9*3600000});
 await closed;assert.equal(viewer.ws.readyState,WebSocket.CLOSED);
 t.mock.timers.reset();
});
test('localAccess:false does not create a preview connection and has no HTTP or WebSocket eye route',async t=>{
 const f=await fixture(t,{localAccess:false});
 assert.equal((await fetch(f.origin+'/api/eye')).status,404);assert.equal(f.sockets.preview.length,0);
 const ws=new WebSocket(f.origin.replace('http:','ws:')+'/api/eye');ws.on('error',()=>{});
 const code=await new Promise(resolve=>ws.on('unexpected-response',(_req,res)=>{resolve(res.statusCode);res.resume();ws.terminate();}));assert.equal(code,404);
});
