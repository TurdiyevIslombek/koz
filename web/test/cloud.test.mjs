import test from 'node:test';
import assert from 'node:assert/strict';
import {once} from 'node:events';
import http from 'node:http';
import {WebSocket} from 'ws';
import {setTimeout as delay} from 'node:timers/promises';
import {createCloudApplication} from '../server/cloud.mjs';
import {createDynamoStore} from '../server/dynamo.mjs';
import {requestPolicy,passwordVerifier} from '../server/security.mjs';
import {FakeDynamo} from './fake-dynamo.mjs';
import {sampleEvidence} from '../src/demo.js';

const publicOrigin='https://203.0.113.20',password='test-owner-password-only';
const config=()=>({KOZ_OWNER_PASSWORD:password,KOZ_PUBLIC_ORIGIN:publicOrigin,KOZ_TABLE:'koz-web',AWS_REGION:'eu-central-1',KOZ_DATA_DIR:'/private/tmp/koz-cloud-unused',PORT:'4173'});
async function fixture(client=new FakeDynamo()){
 const env=config(),storage=createDynamoStore({table:'koz-web',region:'eu-central-1',client}),app=await createCloudApplication(env,{storage});assert.equal(env.KOZ_OWNER_PASSWORD,undefined);
 app.server.listen(0,'127.0.0.1');await once(app.server,'listening');const origin=`http://127.0.0.1:${app.server.address().port}`;let cookie='';
 const headers={Host:new URL(publicOrigin).host,'X-Forwarded-Proto':'https',Origin:publicOrigin};
 const request=async(path,data,method=data===undefined?'GET':'POST',owner=true,extra={})=>{
  return new Promise((resolve,reject)=>{const req=http.request(`${origin}/api/${path}`,{method,headers:{...headers,...(owner?{Cookie:cookie}:{}),'Content-Type':'application/json',...extra}},res=>{let text='';res.on('data',chunk=>text+=chunk);res.on('end',()=>resolve({status:res.statusCode,body:JSON.parse(text),cookie:res.headers['set-cookie']?.[0]}));});req.on('error',reject);req.end(method==='GET'?undefined:JSON.stringify(data));});
 };
 const login=await request('login',{password});if(login.status!==200)await app.close();assert.equal(login.status,200);assert.match(login.cookie,/; Secure/);assert.match(login.cookie,/HttpOnly/);assert.match(login.cookie,/SameSite=Strict/);cookie=login.cookie.split(';')[0];
 const runner=async()=>{const token=(await request('runner-token',{})).body.token;const ws=new WebSocket(`${origin.replace('http:','ws:')}/v1/runner`,{headers:{Host:headers.Host,'X-Forwarded-Proto':'https',Authorization:`Bearer ${token}`}});await once(ws,'open');return {ws,token};};
 return {app,request,runner,client,origin,headers};
}
test('proxy headers require loopback, exact public host/origin, HTTPS and secure owner sessions',async()=>{
 const request=(address,headers)=>({url:'/api/login',method:'POST',socket:{remoteAddress:address},headers});
 const h={host:'203.0.113.20','x-forwarded-proto':'https',origin:publicOrigin};
 assert.equal(requestPolicy(request('198.51.100.2',h),publicOrigin).allowed,false);
 assert.equal(requestPolicy(request('127.0.0.1',h),publicOrigin).allowed,true);
 assert.equal(requestPolicy(request('127.0.0.1',{...h,host:'evil.example'}),publicOrigin).allowed,false);
 assert.equal(requestPolicy(request('127.0.0.1',{...h,origin:'https://evil.example'}),publicOrigin).originOK,false);
 assert.equal(requestPolicy(request('127.0.0.1',{...h,origin:undefined}),publicOrigin).originOK,false);
 const verify=passwordVerifier(password);assert.equal(verify.verify(password),true);assert.equal(verify.verify('wrong'),false);
 const f=await fixture();try{
  assert.equal((await fetch(f.origin+'/api/health')).status,200);
  assert.equal((await f.request('session',undefined,'GET',false)).body.authenticated,false);
  assert.equal((await f.request('login',{password},'POST',false,{Origin:'https://evil.example'})).status,403);
  assert.equal((await f.request('login',{password},'POST',false,{'X-Forwarded-Proto':'http'})).status,403);
 }finally{await f.app.close();}
});
test('Bedrock/cameras connect; anonymous judges see only the selected job and cannot command or mint tokens',async()=>{
 const f=await fixture();let ws;
 try{
  ({ws}=await f.runner());const events=sampleEvidence();for(const e of events){if(e.type==='status'){e.data.planner='bedrock';e.data.cameras=['mac_camera','esp32_cam'];}ws.send(JSON.stringify(e));}await delay(50);
  const owner=(await f.request('snapshot')).body;assert.equal(owner.events.find(r=>r.event.type==='status').event.data.planner,'bedrock');
  const hidden=await f.request('public/snapshot',undefined,'GET',false);assert.deepEqual(hidden.body.events,[]);assert.equal(hidden.body.published,false);
  for(const path of ['commands','runner-token','replay','publication','summaries'])assert.equal((await f.request(path,{},'POST',false)).status,401);
  assert.equal((await f.request('snapshot',undefined,'GET',false)).status,401);
  assert.equal((await f.request('history',undefined,'GET',false)).status,401);
  const chosen=events[0],trial=events.find(e=>e.type==='trial_result');await f.request('summaries',{trial_id:trial.trial_id});
  assert.equal((await f.request('publication',{session_id:chosen.session_id,job_id:chosen.job_id,summary_ids:[trial.trial_id]})).status,200);
  const visible=(await f.request('public/snapshot',undefined,'GET',false)).body;assert.ok(visible.events.length>0);assert.ok(visible.events.every(r=>r.event.job_id===chosen.job_id&&r.event.type!=='command_result'));assert.equal(visible.saved.length,1);assert.equal(visible.pending,null);assert.ok(visible.statusAt>0);
  ws.send(JSON.stringify({...chosen,seq:100,job_id:'c'.repeat(32)}));await delay(20);
  const switched=(await f.request('public/snapshot',undefined,'GET',false)).body;assert.equal(switched.statusAt,0);assert.ok(switched.events.every(r=>r.event.job_id===chosen.job_id));
  assert.equal((await f.request('replay',{action:'start'})).status,400);
  await f.request('publication',null);assert.deepEqual((await f.request('public/snapshot',undefined,'GET',false)).body.events,[]);
 }finally{ws?.terminate();await f.app.close();}
});
test('cloud commands use the same socket; prompts/passwords/tokens never reach durable storage; restart is Unknown',async()=>{
 const f=await fixture();let ws,token;
 try{
  ({ws,token}=await f.runner());const status=sampleEvidence()[0];status.data.state='idle';status.job_id=status.trial_id=status.revision=null;status.data.planner='bedrock';status.data.cameras=['esp32_cam'];ws.send(JSON.stringify(status));await delay(30);
  const incoming=once(ws,'message'),text='PRIVATE PROMPT NEVER STORED';
  assert.equal((await f.request('commands',{command:'start_job',data:{input:'prompt',language:'en',text,camera_id:'esp32_cam'}})).status,202);
  const command=JSON.parse((await incoming)[0]);assert.equal(command.data.text,text);assert.equal(command.data.camera_id,'esp32_cam');
  ws.send(JSON.stringify({...status,seq:2,type:'command_result',data:{command_id:command.command_id,result:'accepted',code:null}}));await delay(30);
  await f.app.close();const disk=JSON.stringify([...f.client.rows.values()]);for(const secret of [text,password,token])assert.equal(disk.includes(secret),false);
  const restarted=await fixture(f.client);try{const snap=(await restarted.request('snapshot')).body;assert.equal(snap.statusAt,0);assert.equal(snap.pending,null);assert.equal(snap.transport.state,'disconnected');}finally{await restarted.app.close();}
 }finally{ws?.terminate();if(f.app.server.listening)await f.app.close();}
});
test('storage failure does not block live updates and makes proof explicitly incomplete',async()=>{
 const f=await fixture();let ws;
 try{({ws}=await f.runner());f.client.fail=true;for(const e of sampleEvidence())ws.send(JSON.stringify(e));await delay(50);const snap=(await f.request('snapshot')).body;assert.ok(snap.events.length);assert.equal(snap.storageIncomplete,true);assert.equal(snap.transport.state,'connected');}finally{f.client.fail=false;ws?.terminate();await f.app.close();}
});
test('the public event stream filters private jobs and resets immediately when sharing is revoked',async()=>{
 const f=await fixture();let ws,stream;const packets=[];
 try{
  ({ws}=await f.runner());const chosen=sampleEvidence()[0];ws.send(JSON.stringify(chosen));await delay(20);
  await f.request('publication',{session_id:chosen.session_id,job_id:chosen.job_id,summary_ids:[]});
  await new Promise((resolve,reject)=>{stream=http.get(`${f.origin}/api/events/public`,{headers:f.headers},res=>{let buffer='';res.on('data',chunk=>{buffer+=chunk;let end;while((end=buffer.indexOf('\n\n'))>=0){const block=buffer.slice(0,end);buffer=buffer.slice(end+2);if(block.startsWith('data: '))packets.push(JSON.parse(block.slice(6)));else if(block.startsWith(': connected'))resolve();}});});stream.on('error',reject);});
  ws.send(JSON.stringify({...chosen,seq:2}));await delay(20);assert.equal(packets.at(-1).event.job_id,chosen.job_id);
  ws.send(JSON.stringify({...chosen,seq:100,job_id:'e'.repeat(32)}));await delay(20);assert.deepEqual(packets.at(-1),{reset:true});assert.equal(JSON.stringify(packets).includes('e'.repeat(32)),false);
  ws.send(JSON.stringify({...chosen,seq:50}));await delay(20);assert.deepEqual(packets.at(-1),{reset:true});assert.equal((await f.request('public/snapshot',undefined,'GET',false)).body.statusAt,0);
  const beforeRevoking=packets.length;await f.request('publication',null);for(let i=0;packets.length===beforeRevoking&&i<100;i++)await delay(5);assert.deepEqual(packets.at(-1),{reset:true});assert.equal(packets.length,beforeRevoking+1);
  const before=packets.length;ws.send(JSON.stringify({...chosen,seq:101}));await delay(20);assert.equal(packets.length,before);
 }finally{stream?.destroy();ws?.terminate();await f.app.close();}
});
test('cloud startup validates configuration and removes the plaintext password even on failure',async()=>{
 for(const change of [{KOZ_OWNER_PASSWORD:'short'},{KOZ_PUBLIC_ORIGIN:'http://example.com'},{KOZ_PUBLIC_ORIGIN:'https://example.com/path'},{AWS_REGION:'us-east-1'},{KOZ_DATA_DIR:'relative'},{PORT:'bad'}]){
  const env={...config(),...change};await assert.rejects(createCloudApplication(env,{storage:{close(){}}}));assert.equal(env.KOZ_OWNER_PASSWORD,undefined);
 }
});
test('cloud has no preview route and rejects binary/image-bearing input before SSE or storage',async()=>{
 const f=await fixture();let ws;
 try{
  assert.equal((await f.request('eye',undefined,'GET',false)).status,404);
  assert.equal((await f.request('eye')).status,404);
  const eye=new WebSocket(f.origin.replace('http:','ws:')+'/api/eye',{headers:f.headers});eye.on('error',()=>{});
  const code=await new Promise(resolve=>eye.on('unexpected-response',(_req,res)=>{resolve(res.statusCode);res.resume();eye.terminate();}));assert.equal(code,404);
  for(const input of [Buffer.alloc(32,255),JSON.stringify({...sampleEvidence()[0],image:'data:image/jpeg;base64,forbidden'})]){
   ({ws}=await f.runner());const closed=once(ws,'close');ws.send(input);await closed;
   const snapshot=(await f.request('public/snapshot',undefined,'GET',false)).body;assert.deepEqual(snapshot.events,[]);
   assert.doesNotMatch(JSON.stringify([...f.client.rows.values()]),/base64|data:image|"preview"/);
  }
 }finally{ws?.terminate();await f.app.close();}
});
