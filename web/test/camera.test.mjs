import test from 'node:test';
import assert from 'node:assert/strict';
import {once} from 'node:events';
import {setTimeout as delay} from 'node:timers/promises';
import {WebSocketServer} from 'ws';
import {createApplication} from '../server/index.mjs';
import {recipeFor,sampleEvidence} from '../src/demo.js';

test('camera slots survive snapshot and selected slots reach the runner in both start forms',async()=>{
 const wss=new WebSocketServer({port:0,host:'127.0.0.1'});await once(wss,'listening');
 const base=sampleEvidence()[0],commands=[];let seq=0,ws;
 const emit=(type,data)=>ws.send(JSON.stringify({...base,type,seq:++seq,job_id:null,trial_id:null,revision:null,data}));
 wss.on('connection',socket=>{
  ws=socket;emit('status',{...base.data,state:'idle',cameras:['mac_camera','esp32_cam']});
  ws.on('message',raw=>{const c=JSON.parse(raw);commands.push(c);emit('command_result',{command_id:c.command_id,result:'rejected',code:'UNSUPPORTED_CAPABILITY'});});
 });
 const app=await createApplication({persist:false,localAccess:true,localRunnerUrl:`ws://127.0.0.1:${wss.address().port}`});
 try{
  app.server.listen(0,'127.0.0.1');await once(app.server,'listening');const origin=`http://127.0.0.1:${app.server.address().port}`;
  const session=await fetch(origin+'/api/session');const cookie=session.headers.get('set-cookie').split(';')[0];
  const request=async(path,data)=>{const r=await fetch(`${origin}/api/${path}`,{method:data?'POST':'GET',headers:{Cookie:cookie,'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});return {status:r.status,body:await r.json()};};
  for(let i=0;!app.model.status&&i<100;i++)await delay(10);
  assert.deepEqual((await request('snapshot')).body.events.find(r=>r.event.type==='status').event.data.cameras,['mac_camera','esp32_cam']);
  for(const input of [{input:'prompt',language:'uz',text:'Sana'},{input:'recipe',recipe:recipeFor()}]){
   for(const [camera_id,code] of [['bad','INVALID_COMMAND'],['phone_ip_camera','UNSUPPORTED_CAPABILITY']]){
    const rejected=await request('commands',{command:'start_job',data:{...input,camera_id}});assert.equal(rejected.status,400);assert.equal(rejected.body.code,code);
   }
   const received=once(ws,'message');const accepted=await request('commands',{command:'start_job',data:{...input,camera_id:'esp32_cam'}});
   assert.equal(accepted.status,202);assert.equal(JSON.parse((await received)[0]).data.camera_id,'esp32_cam');
   for(let i=0;!app.model.pending?.failed&&i<100;i++)await delay(10);
   assert.equal(app.model.pending.code,'UNSUPPORTED_CAPABILITY');
  }
  assert.equal(commands.length,2);
 }finally{await app.close();for(const client of wss.clients)client.terminate();await new Promise(resolve=>wss.close(resolve));}
});
