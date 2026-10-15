import { validateEvent, ContractError } from './protocol.js';
export const DAY = 86400000;
const sameJob=(a,b)=>a&&b&&a.session_id===b.session_id&&a.job_id===b.job_id;
export const expiry=(event,receivedAt)=>Math.min(event.minute,Math.floor(receivedAt/60000))*60000+7*DAY;
export function createModel(){return {events:[],seen:new Set(),highest:new Map(),status:null,statusAt:0,observation:null,fault:null,recipe:null,pending:null,trial:null};}
export function invalidateLive(model){model.statusAt=0;model.observation=null;model.pending=null;}
export function ingest(model,event,receivedAt=Date.now()) {
  validateEvent(event,receivedAt);
  if(event.type==='observation'&&event.data.looming!==null&&!model.status?.data.capabilities.includes('looming'))throw new ContractError('INVALID_EVENT');
  const key=`${event.session_id}:${event.seq}`;
  if(model.seen.has(key)||expiry(event,receivedAt)<=Date.now())return false;
  model.seen.add(key);
  const highest=model.highest.get(event.session_id)||0;
  const fresh=event.seq>highest;
  model.highest.set(event.session_id,Math.max(highest,event.seq));
  model.events.push({event,receivedAt,expiresAt:expiry(event,receivedAt)});
  model.events=model.events.filter(r=>r.expiresAt>Date.now());
  if(event.type==='status'&&fresh){
    const changed=!sameJob(model.status,event);
    if(!model.statusAt||receivedAt-model.statusAt>3000)model.observation=null;
    if(changed){model.observation=null;model.fault=null;model.recipe=null;}
    model.status=event;model.statusAt=receivedAt;
    const matchesPending=model.pending&&(!model.pending.session_id||model.pending.session_id===event.session_id)&&(!model.pending.job_id||model.pending.job_id===event.job_id);
    if(matchesPending&&['stop_job','finish_trial'].includes(model.pending.command)&&event.data.state==='idle')model.pending=null;
    if(matchesPending&&model.pending?.command==='start_job'&&['running','held','refused'].includes(event.data.state))model.pending=null;
    if(model.pending?.command==='begin_trial'&&event.trial_id===model.pending.trial_id)model.pending=null;
    model.trial=event.trial_id;
    if(['running','idle'].includes(event.data.state)&&model.fault&&event.seq>model.fault.seq)model.fault=null;
  }
  if(event.type==='observation'&&fresh&&sameJob(model.status,event)&&event.revision===model.status.revision)model.observation=event;
  if(event.type==='recipe'&&(!model.recipe||!sameJob(model.recipe,event)||event.revision>=model.recipe.revision)&&(!model.status||sameJob(model.status,event)))model.recipe=event;
  if(event.type==='fault'&&fresh&&(!model.status||sameJob(model.status,event)))model.fault=event;
  if(event.type==='command_result'&&event.data.command_id===model.pending?.command_id){
    model.pending.result=event.data.result;model.pending.code=event.data.code;
    // An acknowledgement settles delivery only. Physical/job state still comes from status.
    if(event.data.result==='rejected')model.pending.failed=true;
  }
  return true;
}
export function liveView(model,now=Date.now()) {
  const offline=!model.status||now-model.statusAt>3000;
  const status=model.status?.data;
  const observation=model.observation?.data;
  const current=!offline&&sameJob(model.status,model.observation)&&model.status.revision===model.observation.revision;
  const gateOpen=status?.privacy==='approved'&&observation?.privacy==='approved';
  const active=['running','evaluating'].includes(status?.state);
  const unavailable=offline||!active||!current||!gateOpen||Boolean(model.fault);
  const reason=offline?null:model.fault?.data.code||(status?.state==='idle'?null:current?observation?.unknown_reason:null)||null;
  const field=name=>{
    const value=observation?.[name];
    if(value===null)return null;
    if(!current||unavailable)return {state:'unknown',value:null,reason};
    return value===undefined?null:value;
  };
  const counts=['occupancy','entered','exited'].map(field);
  const outputUnknown=counts.some(c=>c?.state==='unknown')||['target','motion','looming'].some(k=>observation?.[k]==='unknown');
  let state=offline?'unknown':status.state==='idle'?'stopped':status.state==='held'?'stopped':status.state==='refused'||status.privacy==='blocked'?'blocked':['checking','planning'].includes(status.state)?'paused':unavailable||outputUnknown?'unknown':status.state==='evaluating'?'evaluating':'running';
  if(model.fault&&!offline)state=model.fault.data.code.startsWith('PRIVATE_')?'blocked':'stopped';
  return {offline,state,reason,status,observation,current,unavailable,counts,coverage:observation?.coverage||'gapped',target:current&&!unavailable?observation.target:'unknown',motion:current&&!unavailable?observation.motion:'unknown',looming:current&&!unavailable?observation.looming:'unknown'};
}
const stable=v=>v&&typeof v==='object'?(Array.isArray(v)?v.map(stable):Object.fromEntries(Object.keys(v).sort().map(k=>[k,stable(v[k])]))):v;
const equal=(a,b)=>JSON.stringify(stable(a))===JSON.stringify(stable(b));
export function settingValue(recipe,setting){const [block,key]=setting.split('.');return block==='brain'?recipe.brain.settings?.[key]:recipe.blocks.find(b=>b.type===block)?.settings[key];}
function expectedAfter(recipe,change){const result=structuredClone(recipe);const [block,key]=change.setting.split('.');const target=block==='brain'?result.brain:result.blocks.find(b=>b.type===block);if(!target?.settings)return null;target.settings[key]=change.after;return result;}
export function checkLabel(data,check){
  if(check==='privacy_approved')return data.privacy;
  if(check.startsWith('target_'))return data.target;
  if(check==='motion_available')return data.motion;
  const counts=[data.occupancy,data.entered,data.exited].filter(Boolean);return counts.length&&counts.every(c=>c.state==='known')?'known':'unknown';
}
export function evidenceChains(model) {
  const events=model.events.filter(r=>r.expiresAt>Date.now()).map(r=>r.event);
  return events.filter(e=>e.type==='decision').map(decision=>{
    const d=decision.data;
    const related=events.filter(e=>sameJob(decision,e));
    const evidence=d.evidence_seq.map(seq=>related.find(e=>e.type==='observation'&&e.seq===seq&&e.revision===decision.revision&&e.data.round===d.round&&e.seq<decision.seq&&e.trial_id===decision.trial_id));
    const before=evidence.every(Boolean)?evidence.at(-1):null;
    const oldRecipe=related.find(e=>e.type==='recipe'&&e.revision===decision.revision&&e.seq<decision.seq&&e.trial_id===decision.trial_id);
    const nextRecipe=related.find(e=>e.type==='recipe'&&e.revision===d.next_revision&&e.data.origin==='adjustment'&&e.data.caused_by===decision.seq&&e.seq>decision.seq);
    const installed=related.find(e=>e.type==='status'&&e.revision===d.next_revision&&nextRecipe&&e.seq>nextRecipe.seq&&['evaluating','running'].includes(e.data.state));
    const after=related.find(e=>e.type==='observation'&&e.revision===d.next_revision&&installed&&e.seq>installed.seq);
    const complete=Boolean(d.next==='adjust'&&d.round===decision.revision&&before&&oldRecipe&&nextRecipe&&installed&&after&&settingValue(oldRecipe.data.recipe,d.change.setting)===d.change.before&&equal(expectedAfter(oldRecipe.data.recipe,d.change),nextRecipe.data.recipe));
    return {decision,before,after,nextRecipe,complete,beforeLabel:before?checkLabel(before.data,d.check):null,afterLabel:after?checkLabel(after.data,d.check):null};
  });
}
export function trialRows(model,demo) {
  const events=model.events.filter(r=>r.expiresAt>Date.now()).map(r=>r.event);
  return Array.from({length:10},(_,i)=>{
    const result=events.filter(e=>e.type==='trial_result'&&e.data.demo===demo&&e.data.index===i+1).at(-1);
    if(!result)return {index:i+1,result:null};
    const first=events.filter(e=>e.trial_id===result.trial_id).reduce((min,e)=>Math.min(min,e.minute),result.minute);
    return {index:i+1,result,durationMinutes:result.minute-first};
  });
}
export function summaryFor(event){
  if(event.type!=='trial_result')throw Error('INVALID_EVENT');
  return {trial_id:event.trial_id,...event.data,date:new Date(event.minute*60000).toISOString().slice(0,10)};
}
