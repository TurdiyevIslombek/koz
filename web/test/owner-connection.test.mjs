import test from 'node:test';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
import {createOwnerConnection} from '../src/owner-connection.js';

async function until(condition){for(let i=0;i<100;i++){if(condition())return;await delay(5);}throw Error('Connection did not settle');}
function harness(api){
 const calls=[],streams=[];
 class Source{
  constructor(url){this.url=url;streams.push(this);}
  close(){this.closed=true;}
  packet(data){this.onmessage({data:JSON.stringify(data)});}
 }
 const connection=createOwnerConnection({api,EventSource:Source,retryMs:5,
  ...Object.fromEntries(['Session','Snapshot','Packet','Disconnect','SignedOut','InvalidPacket'].map(name=>['on'+name,value=>calls.push([name,value])]))
 });
 return {connection,calls,streams};
}

test('SSE failure rechecks session, retries downtime, and replaces the old snapshot without replaying commands',async()=>{
 let restarted=false,down=false;const requests=[];
 const h=harness(async path=>{requests.push(path);if(down)throw Error('Offline');if(path==='session')return {authenticated:true};return {server:restarted?2:1};});
 try{
  await h.connection.start();const old=h.streams[0];
  down=true;old.onerror();assert.equal(old.closed,true);assert.equal(h.calls.at(-1)[0],'Disconnect');
  await until(()=>requests.filter(p=>p==='session').length>=3);
  restarted=true;down=false;await until(()=>h.streams.length===2);
  assert.deepEqual(h.calls.filter(c=>c[0]==='Snapshot').map(c=>c[1].server),[1,2]);
  old.packet({event:'stale'});assert.equal(h.calls.some(c=>c[0]==='Packet'),false);
  h.streams[1].packet({event:'fresh'});assert.deepEqual(h.calls.at(-1),['Packet',{event:'fresh'}]);
  assert.ok(requests.every(p=>['session','snapshot'].includes(p)));
 }finally{h.connection.stop();}
});

test('expired password sessions request sign-in and do not reconnect an unauthorized stream',async()=>{
 let authorized=true;const h=harness(async path=>path==='session'?{authenticated:authorized,configured:true}:{});
 try{
  await h.connection.start();authorized=false;h.streams[0].onerror();
  await until(()=>h.calls.some(c=>c[0]==='SignedOut'));
  assert.equal(h.streams.length,1);assert.equal(h.streams[0].closed,true);
  const count=h.calls.length;await delay(20);assert.equal(h.calls.length,count);
 }finally{h.connection.stop();}
});

test('entering demo or signing out cancels a pending connection and stale stream callbacks',async()=>{
 let release;const h=harness(path=>path==='session'?Promise.resolve({authenticated:true}):new Promise(resolve=>release=resolve));
 const attempt=h.connection.start();await until(()=>Boolean(release));h.connection.stop();release({server:'late'});await attempt;
 assert.equal(h.streams.length,0);assert.equal(h.calls.some(c=>c[0]==='Snapshot'),false);
});

test('a source reset refreshes its snapshot and keeps only one stream',async()=>{
 let snapshot=0;const h=harness(async path=>path==='session'?{authenticated:true}:{revision:++snapshot});
 try{
  await h.connection.start();const old=h.streams[0];old.packet({reset:true});await until(()=>h.streams.length===2);
  assert.equal(old.closed,true);old.onerror();assert.equal(h.streams[1].closed,undefined);
  assert.deepEqual(h.calls.filter(c=>c[0]==='Snapshot').map(c=>c[1].revision),[1,2]);
 }finally{h.connection.stop();}
});
