import test from 'node:test';import assert from 'node:assert/strict';
import { createModel,ingest,liveView,evidenceChains,trialRows,summaryFor,expiry,DAY,trialUsed,clockOffset,localTime } from '../src/model.js';
import { sampleEvidence,known,unknown,recipeFor,DemoRunner } from '../src/demo.js';
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function counter(){const m=createModel(),events=sampleEvidence();const s=events[0];s.data.state='running';s.trial_id=null;s.minute=Math.floor(Date.now()/60000);const o=events[2];o.trial_id=null;o.minute=s.minute;o.data.round=null;o.data.target=null;o.data.occupancy=known(0);o.data.entered=known(7);o.data.exited=known(7);ingest(m,s);ingest(m,o);return {m,s,o};}
test('measured zero stays zero; offline after 3s becomes unknown, never stopped',()=>{const {m}=counter();assert.equal(liveView(m).counts[0].value,0);const view=liveView(m,m.statusAt+3001);assert.equal(view.state,'unknown');assert.equal(view.counts[0].state,'unknown');assert.equal(view.counts[0].value,null);});
test('unknown_reason is exposed exactly, not replaced with a generic message',()=>{const {m,o}=counter();const next=structuredClone(o);next.seq++;for(const k of ['occupancy','entered','exited'])next.data[k]=unknown('FRAME_STALE');next.data.unknown_reason='FRAME_STALE';ingest(m,next);assert.equal(liveView(m).reason,'FRAME_STALE');assert.equal(liveView(m).state,'unknown');});
test('duplicates and late statuses never refresh live or retained expiry',()=>{const {m,s}=counter();const before=m.statusAt;assert.equal(ingest(m,s,Date.now()+100),false);assert.equal(m.statusAt,before);const late={...s,seq:2,data:{...s.data,state:'idle'}};ingest(m,late);assert.equal(m.statusAt,before);assert.equal(liveView(m).state,'running');});
test('accepted stop acknowledgement does not fabricate stopped or change zero',()=>{const {m,s}=counter();const command='a'.repeat(32);m.pending={command_id:command,command:'stop_job'};ingest(m,{...s,type:'command_result',seq:4,revision:null,data:{command_id:command,result:'accepted',code:null}});assert.equal(liveView(m).state,'running');assert.equal(liveView(m).counts[0].value,0);assert.equal(m.pending.result,'accepted');ingest(m,{...s,seq:5,data:{...s.data,state:'idle',camera_on:false}});assert.equal(liveView(m).state,'stopped');assert.equal(m.pending,null);});
test('proof badge requires full matching executed chain; missing or tampered setting never earns it',()=>{for(const missing of [null,'recipe','status','observation']){const events=sampleEvidence();const m=createModel();for(const e of events){if(missing&&e.revision===2&&e.type===missing)continue;ingest(m,e);}assert.equal(evidenceChains(m)[0].complete,missing===null);}const events=sampleEvidence();events.find(e=>e.type==='recipe'&&e.revision===2).data.recipe.camera.fps=5;const m=createModel();events.forEach(e=>ingest(m,e));assert.equal(evidenceChains(m)[0].complete,false);});
test('ten trial rows preserve pass/fail/unknown; saved summaries exclude raw event fields',()=>{const m=createModel();sampleEvidence().forEach(e=>ingest(m,e));const rows=trialRows(m,'red_ball');assert.equal(rows.length,10);assert.deepEqual(rows.slice(0,3).map(r=>r.result.data.result),['pass','fail','unknown']);const summary=summaryFor(rows[0].result);for(const key of ['minute','session_id','seq','job_id'])assert.equal(key in summary,false);assert.equal(expiry(rows[0].result,Date.now()),rows[0].result.minute*60000+7*DAY);});
test('interactive demo runs a validated adjustment and confirms stop asynchronously',async()=>{const m=createModel(),runner=new DemoRunner(e=>ingest(m,e));try{runner.seed();runner.state='idle';runner.status();m.pending=runner.command('start_job',{input:'recipe',recipe:recipeFor('red_ball')},'uz');await sleep(1600);assert.equal(liveView(m).state,'running');assert.equal(evidenceChains(m).at(-2).complete,true);m.pending=runner.command('stop_job',{},'uz');assert.equal(liveView(m).state,'running');await sleep(600);assert.equal(liveView(m).state,'stopped');}finally{runner.destroy();}});
test('a fault after idle still displays its fixed reason; expired proof cannot earn a badge',()=>{const {m,s}=counter();ingest(m,{...s,seq:4,data:{...s.data,state:'idle'}});ingest(m,{...s,type:'fault',seq:5,revision:null,data:{code:'PRIVATE_BATHROOM',effect:'off'}});assert.equal(liveView(m).reason,'PRIVATE_BATHROOM');const proof=createModel();sampleEvidence().forEach(e=>ingest(proof,e));proof.events.forEach(r=>r.expiresAt=Date.now()-1);assert.deepEqual(evidenceChains(proof),[]);assert.equal(trialRows(proof,'red_ball').some(r=>r.result),false);});
test('a missing cited observation or unrelated status cannot complete evidence or settle a command',()=>{const events=sampleEvidence();events.find(e=>e.type==='decision').data.evidence_seq.push(999);const m=createModel();events.forEach(e=>ingest(m,e));assert.equal(evidenceChains(m)[0].complete,false);const {m:live,s}=counter();live.pending={command:'start_job',job_id:'f'.repeat(32),session_id:s.session_id};ingest(live,{...s,seq:5});assert.ok(live.pending);});
test('a trial result settles finish_trial and closes the trial at once, even when the job was already idle',()=>{
 const {m,s}=counter(),trial='c'.repeat(32);
 ingest(m,{...s,seq:4,trial_id:trial,job_id:null,data:{...s.data,state:'idle'}});
 assert.equal(m.trial,trial);assert.equal(trialUsed(m),false);   // a trial without a job yet
 ingest(m,{...s,seq:5,trial_id:trial,data:{...s.data,state:'idle'}});
 assert.equal(trialUsed(m),true);                                // its one job has run
 m.pending={command_id:'d'.repeat(32),command:'finish_trial',job_id:s.job_id,session_id:s.session_id,trial_id:trial,expires_at:Math.floor(Date.now()/1000)+10};
 const result={...sampleEvidence().find(e=>e.type==='trial_result'),session_id:s.session_id,job_id:s.job_id,trial_id:trial,seq:6,minute:s.minute};
 assert.equal(ingest(m,result),true);
 assert.equal(m.pending,null);assert.equal(m.trial,null);assert.equal(trialUsed(m),false);
});
test('a viewer clock 5 s off still sees a fresh status as live (Oct 22: the Mac was 5 s fast)',()=>{
 const {s}=counter(),viewerNow=Date.now(),serverNow=viewerNow-5000;   // the server stamps with its own clock
 const asIs=createModel();ingest(asIs,{...s,seq:9},serverNow);
 assert.equal(liveView(asIs,viewerNow).offline,true);                  // the bug: compared as it is
 const offset=clockOffset(serverNow,viewerNow),fixed=createModel();ingest(fixed,{...s,seq:9},localTime(serverNow,offset));
 assert.equal(offset,5000);assert.equal(liveView(fixed,viewerNow).offline,false);
 assert.equal(clockOffset(undefined,viewerNow),0);assert.equal(clockOffset(Number.NaN,viewerNow),0);   // an old server: no correction
 assert.equal(localTime(0,offset),0);                                  // "no status yet" stays 0
});
