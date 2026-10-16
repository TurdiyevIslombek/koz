import test from 'node:test';
import assert from 'node:assert/strict';
import {once} from 'node:events';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createApplication} from '../server/index.mjs';
import {createModel,ingest,liveView,expiry} from '../src/model.js';
import {sampleEvidence} from '../src/demo.js';

test('restart snapshots preserve historical receipts without making an old status fresh or invalid',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'koz-web-restart-'));
 const receivedAt=Math.floor(Date.now()/60000)*60000,events=sampleEvidence().slice(0,3);
 events[0].data.planner='ollama';
 await writeFile(join(dir,'events.ndjson'),events.map(event=>JSON.stringify({event,receivedAt,expiresAt:expiry(event,receivedAt)})).join('\n')+'\n');
 let app;
 try{
  app=await createApplication({dataDir:dir,localAccess:true});app.server.listen(0,'127.0.0.1');await once(app.server,'listening');
  const origin=`http://127.0.0.1:${app.server.address().port}`;
  const session=await fetch(origin+'/api/session');
  const cookie=session.headers.get('set-cookie').split(';')[0];
  const snapshot=await (await fetch(origin+'/api/snapshot',{headers:{Cookie:cookie}})).json();
  assert.equal(snapshot.statusAt,0);assert.equal(snapshot.events.length,3);
  const browser=createModel();for(const row of snapshot.events){assert.ok(row.receivedAt>0);ingest(browser,row.event,row.receivedAt);}
  browser.statusAt=snapshot.statusAt;
  assert.equal(liveView(browser).state,'unknown');assert.equal(liveView(browser).target,'unknown');assert.ok(browser.recipe);
 }finally{await app?.close();await rm(dir,{recursive:true,force:true});}
});
