import test from 'node:test';
import assert from 'node:assert/strict';
import {createDynamoStore} from '../server/dynamo.mjs';
import {FakeDynamo} from './fake-dynamo.mjs';
import {sampleEvidence,known,unknown} from '../src/demo.js';
import {summaryFor} from '../src/model.js';

const row=event=>({event,receivedAt:Date.now()});
function fixture(){const client=new FakeDynamo(),store=createDynamoStore({table:'koz-web',region:'ap-southeast-2',client});return {client,store};}
test('DynamoDB TTL, duplicate transactions, rounded receipts and owner-scoped pagination',async()=>{
 const {client,store}=fixture(),base=sampleEvidence()[0];base.trial_id=null;
 for(let seq=1;seq<=6;seq++)await store.append(row({...base,seq}));
 const original=structuredClone([...client.rows.values()].find(r=>r.sk.S.endsWith('0000000000000001')));
 assert.equal(await store.append(row({...base,seq:1})),false);
 assert.deepEqual(client.rows.get(client.key(original)),original);
 assert.equal(Number(original.expires_at.N),base.minute*60+604800);
 assert.equal(JSON.parse(original.value.S).receivedAt%60000,0);
 const first=await store.history({session:base.session_id,limit:2});assert.deepEqual(first.rows.map(r=>r.event.seq),[6,5]);assert.ok(first.nextCursor);
 const next=await store.history({session:base.session_id,limit:2,cursor:first.nextCursor});assert.deepEqual(next.rows.map(r=>r.event.seq),[4,3]);
 const cursor=JSON.parse(Buffer.from(first.nextCursor,'base64url'));cursor.pk.S='OWNER#someone-else';
 await assert.rejects(store.history({session:base.session_id,cursor:Buffer.from(JSON.stringify(cursor)).toString('base64url')}),{code:'INVALID_COMMAND'});
 for(const record of client.rows.values())record.expires_at={N:'1'};
 assert.deepEqual((await store.history({session:base.session_id})).rows,[]);
 assert.deepEqual((await store.load()).events,[]);
 assert.ok(client.requests.filter(r=>r.name==='QueryCommand').every(r=>r.input.FilterExpression.includes('expires_at > :now')));
});
test('crossing totals use increases, skip trials/evaluation and occupancy, and mark gaps/disconnects',async()=>{
 const {store}=fixture(),events=sampleEvidence(),status=events[0],observation=events.find(e=>e.type==='observation');
 status.trial_id=null;status.data.state='running';status.seq=1;await store.append(row(status));
 observation.trial_id=null;observation.data.round=null;observation.data.target=null;observation.data.occupancy=known(500);observation.data.entered=known(2);observation.data.exited=known(1);observation.seq=2;
 await store.append(row(observation));await store.append(row(observation));
 await store.append(row({...observation,seq:3,data:{...observation.data,entered:known(5),exited:known(1)}}));
 await store.append(row({...observation,seq:4,data:{...observation.data,entered:known(4),exited:known(1)}}));
 await store.append(row({...observation,seq:5,trial_id:'a'.repeat(32)}));
 await store.append(row({...observation,seq:6,data:{...observation.data,round:1,entered:known(50)}}));
 let totals=(await store.totals()).rows;assert.equal(totals.length,1);assert.equal(totals[0].entered,5);assert.equal(totals[0].exited,1);assert.equal(totals[0].open,true);
 await store.append(row({...observation,seq:7,data:{...observation.data,entered:unknown('FRAME_STALE'),exited:unknown('FRAME_STALE'),occupancy:unknown('FRAME_STALE'),unknown_reason:'FRAME_STALE',coverage:'gapped'}}));
 totals=(await store.totals()).rows;assert.equal(totals[0].entered,5);assert.equal(totals[0].incomplete,true);
 await store.disconnected();assert.equal((await store.totals()).rows[0].incomplete,true);
 await store.append(row({...status,seq:8,data:{...status.data,state:'idle',camera_on:false}}));assert.equal((await store.totals()).rows[0].open,false);
});
test('saved summaries have no TTL, repeat saves preserve them, and deletion is durable',async()=>{
 const {client,store}=fixture(),summary=summaryFor(sampleEvidence().find(e=>e.type==='trial_result'));
 await store.saveSummary(summary);await store.saveSummary({...summary,result:'fail'});
 const saved=[...client.rows.values()].find(r=>r.sk.S.startsWith('SUMMARY#'));
 assert.equal('expires_at' in saved,false);assert.deepEqual((await store.summaries()).rows,[summary]);
 await store.deleteSummary(summary.trial_id);assert.deepEqual((await store.summaries()).rows,[]);
});
test('crossings across UTC days retain high-water counts and expire 30 days after each day ends',async()=>{
 const {client,store}=fixture(),observation=sampleEvidence().find(e=>e.type==='observation');
 const today=Math.floor(Date.now()/86400000),yesterday=today-1;
 observation.trial_id=null;observation.minute=yesterday*1440+100;observation.data.round=null;observation.data.target=null;observation.data.entered=known(10);observation.data.exited=known(2);
 await store.append(row(observation));await store.append(row({...observation,seq:observation.seq+1,minute:today*1440,data:{...observation.data,entered:known(13),exited:known(3)}}));
 const first=(await store.totals({date:new Date(yesterday*86400000).toISOString().slice(0,10)})).rows[0];
 const second=(await store.totals()).rows[0];assert.equal(first.entered,10);assert.equal(second.entered,3);assert.equal(second.exited,1);
 for(const record of client.rows.values())if(record.sk.S.startsWith('TOTAL#')){const date=JSON.parse(record.value.S).date;assert.equal(Number(record.expires_at.N),Date.parse(date)/1000+31*86400);}
});
