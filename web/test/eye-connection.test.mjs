import test from 'node:test';
import assert from 'node:assert/strict';
import {setTimeout as delay} from 'node:timers/promises';
import {createEyeConnection} from '../src/eye-connection.js';
import {eyeClosed} from '../src/eye-protocol.js';

function fixture(){
 const sockets=[],revoked=[];let next=0;
 class Socket {constructor(){sockets.push(this);}close(){this.closed=true;this.onclose?.();}message(data){this.onmessage({data});}}
 const frames=()=>{const bytes=new Uint8Array(32);bytes.set([255,216,255,192,0,11,8,0,180,1,64,1,1,17,0,255,218]);bytes.set([255,217],30);return bytes.buffer;};
 const connection=createEyeConnection({onChange(){},WebSocket:Socket,url:()=> 'ws://127.0.0.1/api/eye',retryMs:10,objects:{createObjectURL:()=>`blob:test-${++next}`,revokeObjectURL:url=>revoked.push(url)}});
 connection.sync({active:true,open:true});return {connection,sockets,revoked,frames};
}
test('browser discards/revokes frames on closed, stops and navigation; an old socket cannot reopen the eye',()=>{
 const f=fixture();try{
  f.sockets[0].message(f.frames());const first=f.connection.state.url;
  f.sockets[0].message(f.frames());assert.ok(f.revoked.includes(first));
  f.sockets[0].message(JSON.stringify(eyeClosed('checking')));assert.deepEqual(f.connection.state,{url:null,reason:'checking'});
  f.sockets[0].message(f.frames());f.connection.sync({active:true,open:false});assert.equal(f.connection.state.url,null);
  f.sockets[0].message(f.frames());assert.equal(f.connection.state.url,null);
  f.connection.sync({active:false,open:false});f.sockets[0].message(f.frames());assert.equal(f.connection.state.url,null);
 }finally{f.connection.stop();}
});
test('browser freshness timer closes the eye without waiting for server or event heartbeat',async()=>{
 const f=fixture();try{f.sockets[0].message(f.frames());assert.ok(f.connection.state.url);await delay(1050);assert.deepEqual(f.connection.state,{url:null,reason:'not_fresh'});assert.equal(f.revoked.length,1);}finally{f.connection.stop();}
});
test('disconnect, invalid protocol and broken image fail closed and recover without old frames',async()=>{
 const f=fixture();try{
  const previous=f.sockets[0];previous.message(f.frames());previous.onclose();assert.equal(f.connection.state.url,null);
  previous.message(f.frames());assert.equal(f.connection.state.url,null);
  await delay(20);assert.equal(f.sockets.length,2);previous.message(f.frames());assert.equal(f.connection.state.url,null);
  f.sockets[1].message(f.frames());f.connection.failedImage();assert.equal(f.connection.state.url,null);
  f.sockets[1].message('{"frame":"unexpected"}');assert.equal(f.sockets[1].closed,true);assert.equal(f.connection.state.url,null);
 }finally{f.connection.stop();}
});
