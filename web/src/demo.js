import { newId } from './protocol.js';
export const known=value=>({state:'known',value,reason:null});
export const unknown=reason=>({state:'unknown',value:null,reason});
export function recipeFor(kind='counter',language='uz'){
 const blocks=[{type:'privacy_guard',settings:{}},{type:'face_blur',settings:{}}];
 if(kind==='red_ball')blocks.push({type:'color_finder',settings:{hue_center:0,hue_half_width:10,saturation_min:120,value_min:80,min_area_ratio:.01}});
 else if(kind!=='privacy_guard')blocks.push({type:'person_detector',settings:{min_confidence:.5}},{type:'line_counter',settings:{line:[[.5,0],[.5,1]]}});
 return {version:1,language,camera:{source:'device_camera',size:'320x240',fps:10},blocks,brain:kind==='red_ball'?{type:'flybrain',settings:{turn_gain:.5,deadband:.1}}:{type:'none'},actions:kind==='red_ball'?[{type:'dashboard'},{type:'motors',max_speed_ratio:.15}]:[{type:'dashboard'}],privacy:{school:kind==='classroom'}};
}
export class DemoRunner {
 constructor(emit){this.emit=emit;this.session=newId();this.job=newId();this.trial=null;this.seq=0;this.revision=1;this.kind='counter';this.state='running';this.reason=null;this.count=7;this.entered=24;this.exited=17;this.timers=new Set();this.recipe=recipeFor();this.offline=false;this.heartbeat=setInterval(()=>{if(!this.offline){this.status();if(this.state==='running')this.observation();}},1000);}
 event(type,data,{revision=this.revision,minute=Math.floor(Date.now()/60000),job=this.job,trial=this.trial}={}){const e={v:1,type,session_id:this.session,seq:++this.seq,job_id:job,trial_id:trial,revision,minute,data:structuredClone(data)};this.emit(e,Date.now());return e;}
 later(fn,ms){const timer=setTimeout(()=>{this.timers.delete(timer);fn();},ms);this.timers.add(timer);}
 status(){const blocked=this.reason?.startsWith('PRIVATE_');this.event('status',{state:this.state,camera_on:this.state!=='idle',privacy:blocked?'blocked':this.reason?.startsWith('PRIVACY_')||this.state==='checking'?'unknown':this.state==='idle'?'unknown':'approved',school:this.recipe.privacy.school,motor:this.kind==='red_ball'?(this.state==='running'?'enabled':'stop_commanded'):'not_present',opencv_major:5,capabilities:[]},{revision:this.state==='idle'?null:this.revision});}
 observation(round=null,target='center'){
  const privacy=this.reason?.startsWith('PRIVATE_')?'blocked':this.reason?.startsWith('PRIVACY_')||this.state==='checking'?'unknown':'approved';
  const reason=this.reason|| (privacy!=='approved'?'PRIVACY_UNAVAILABLE':null);
  const isCounter=['counter','classroom'].includes(this.kind),isBall=this.kind==='red_ball';
  return this.event('observation',{round,privacy,occupancy:isCounter?(reason?unknown(reason):known(this.count)):null,entered:isCounter?(reason?unknown(reason):known(this.entered)):null,exited:isCounter?(reason?unknown(reason):known(this.exited)):null,coverage:reason||this.gapped?'gapped':'complete',target:isBall?(reason?'unknown':target):null,motion:null,looming:null,alert:null,unknown_reason:reason});
 }
 seed(){this.status();this.event('recipe',{origin:'planner',caused_by:null,recipe:this.recipe});this.observation();}
 setState(value){this.offline=false;this.reason=null;this.gapped=false;this.state='running';this.count=7;this.entered=24;this.exited=17;
  if(value==='offline'){this.offline=true;return;}
  if(value==='zero'){this.count=0;this.exited=24;}
  else if(value==='paused'){this.state='checking';this.reason='PRIVACY_UNAVAILABLE';}
  else if(value==='gap')this.gapped=true;
  else if(value==='stopped')this.state='idle';
  else if(value!=='running')this.reason=value;
  if(this.reason?.startsWith('PRIVATE_'))this.state='held';
  this.status();if(this.state!=='idle')this.observation();
 }
 cross(){if(this.state!=='running'||this.reason||this.offline)return;this.count++;this.entered++;this.observation();}
 command(command,data,language,wire=null){
  const envelope=wire?{command_id:wire.command_id,command,session_id:wire.session_id,job_id:wire.job_id,trial_id:wire.trial_id,expires_at:wire.expires_at}:{command_id:newId(),command,trial_id:this.trial,expires_at:Math.floor(Date.now()/1000)+10};
  this.later(()=>this.event('command_result',{command_id:envelope.command_id,result:'accepted',code:null},{revision:null}),100);
  if(command==='stop_job'){
   for(const t of this.timers)clearTimeout(t);this.timers.clear();
   this.later(()=>this.event('command_result',{command_id:envelope.command_id,result:'accepted',code:null},{revision:null}),100);
   this.later(()=>{this.state='idle';this.reason=null;this.status();},550);
  } else if(command==='start_job'){
   this.job=wire?.job_id||newId();this.trial=wire?.trial_id??this.trial;this.revision=1;this.reason=null;this.state='planning';this.count=this.entered=this.exited=0;
   this.recipe=data.input==='recipe'?structuredClone(data.recipe):recipeFor(this.kind,language);this.kind=this.recipe.brain.type==='flybrain'?'red_ball':this.recipe.privacy.school?'classroom':this.recipe.blocks.some(b=>b.type==='person_detector')?'counter':'privacy_guard';
   this.later(()=>this.status(),180);
   this.later(()=>{this.event('recipe',{origin:data.input==='recipe'?'import':'planner',caused_by:null,recipe:this.recipe});this.state='evaluating';this.status();this.evalEvidence=this.observation(1,this.kind==='red_ball'?'right':'center').seq;},500);
   this.later(()=>{if(this.kind==='red_ball'){const evidence=this.evalEvidence;const before=this.recipe.brain.settings.turn_gain;const after=before===.4?.3:.4;const decision=this.event('decision',{round:1,evidence_seq:[evidence],check:'target_centered',result:'fail',next:'adjust',next_revision:2,change:{setting:'brain.turn_gain',before,after},code:null});this.revision=2;this.recipe.brain.settings.turn_gain=after;this.event('recipe',{origin:'adjustment',caused_by:decision.seq,recipe:structuredClone(this.recipe)});this.status();this.evalEvidence=this.observation(2,'center').seq;}const evidence=this.evalEvidence;this.event('decision',{round:this.revision,evidence_seq:[evidence],check:this.kind==='red_ball'?'target_centered':this.kind==='privacy_guard'?'privacy_approved':'counts_available',result:'pass',next:'run',next_revision:this.revision,change:null,code:null});this.state='running';this.status();this.observation();},1400);
  } else if(command==='begin_trial'){
   this.trial=wire?.trial_id||newId();this.trialInfo=data;this.job=null;this.state='idle';this.kind=data.demo;envelope.trial_id=this.trial;this.later(()=>this.status(),250);
  } else if(command==='finish_trial'){
   const observed=this.trialInfo.demo==='classroom'?(this.reason||this.gapped?unknown(this.reason||'FRAME_STALE'):known(this.entered)):null;
   const invalidPass=data.result==='pass'&&this.trialInfo.demo!=='privacy_guard'&&(observed?.state==='unknown'||this.offline);
   this.later(()=>{this.event('trial_result',{demo:this.trialInfo.demo,index:this.trialInfo.index,result:invalidPass?'unknown':data.result,basis:'owner_report',reason:invalidPass?'unknown':data.reason,expected_count:this.trialInfo.demo==='classroom'?data.expected_count:null,observed_count:observed,fault_code:this.reason,evidence:'complete',agent_changes:[]});this.state='idle';this.trial=null;this.status();},350);
  }
  return envelope;
 }
 destroy(){clearInterval(this.heartbeat);for(const t of this.timers)clearTimeout(t);this.timers.clear();}
}

// Synthetic evidence for exploring the proof screen; not measured telemetry.
export function sampleEvidence(){
 const session=newId(),job=newId(),trial=newId(),minute=Math.floor(Date.now()/60000)-5,events=[];let seq=0;
 const e=(type,data,revision=1,offset=0)=>{const event={v:1,type,session_id:session,seq:++seq,job_id:job,trial_id:trial,revision,minute:minute+offset,data:structuredClone(data)};events.push(event);return event;};
 const recipe=recipeFor('red_ball');const state={state:'evaluating',camera_on:true,privacy:'approved',school:false,motor:'stop_commanded',opencv_major:5,capabilities:[]};
 const obs={round:1,privacy:'approved',occupancy:null,entered:null,exited:null,coverage:'complete',target:'right',motion:null,looming:null,alert:null,unknown_reason:null};
 e('status',state);e('recipe',{origin:'planner',caused_by:null,recipe});const before=e('observation',obs);
 const change={setting:'brain.turn_gain',before:.5,after:.4};const decision=e('decision',{round:1,evidence_seq:[before.seq],check:'target_centered',result:'fail',next:'adjust',next_revision:2,change,code:null});
 recipe.brain.settings.turn_gain=.4;e('recipe',{origin:'adjustment',caused_by:decision.seq,recipe},2);e('status',state,2);e('observation',{...obs,round:2,target:'center'},2);
 e('trial_result',{demo:'red_ball',index:1,result:'pass',basis:'owner_report',reason:'none',expected_count:null,observed_count:null,fault_code:null,evidence:'complete',agent_changes:[{from_revision:1,to_revision:2,check:'target_centered',before_label:'right',change,executed:true,after_label:'center',after_result:'pass'}]},2,1);
 for(const [index,result,reason,fault]of [[2,'fail','wrong_direction','CHECK_FAILED'],[3,'unknown','unknown','FRAME_STALE']]){const event=e('trial_result',{demo:'red_ball',index,result,basis:'owner_report',reason,expected_count:null,observed_count:null,fault_code:fault,evidence:index===3?'incomplete':'complete',agent_changes:[]},1,2);event.trial_id=newId();event.job_id=newId();}
 return events;
}
