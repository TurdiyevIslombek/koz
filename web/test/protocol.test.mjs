import test from 'node:test';import assert from 'node:assert/strict';
import { parseStrict,readRecipe,validateEvent,validateCommandData,CODES,messages,codeMessage } from '../src/protocol.js';
import { recipeFor,sampleEvidence,known,unknown } from '../src/demo.js';
const observation=()=>sampleEvidence().find(e=>e.type==='observation');
test('cameras is an optional unique slot list; addresses, duplicates and unknown fields stay rejected',()=>{
 const status=()=>sampleEvidence()[0];
 for(const cameras of [[],['mac_camera'],['esp32_cam','phone_ip_camera','mac_camera']]){const e=status();e.data.cameras=cameras;e.data.planner='rules';assert.doesNotThrow(()=>validateEvent(e));}
 assert.doesNotThrow(()=>validateEvent(status()));
 for(const cameras of [null,{},'mac_camera',[0],['http://camera/stream'],['mac_camera','mac_camera'],['other'],[undefined]]){const e=status();e.data.cameras=cameras;assert.throws(()=>validateEvent(e));}
 const e=status();e.data.cameras=[];e.data.camera_url='http://camera';assert.throws(()=>validateEvent(e));
});
test('camera_id is a fixed optional start_job field for prompt and recipe; unsupported slots have a fixed rejection',()=>{
 for(const input of [{input:'prompt',language:'uz',text:'Sana'},{input:'recipe',recipe:recipeFor()}]){
  assert.doesNotThrow(()=>validateCommandData('start_job',input));
  for(const camera_id of ['mac_camera','esp32_cam','phone_ip_camera'])assert.doesNotThrow(()=>validateCommandData('start_job',{...input,camera_id},[],[camera_id]));
  for(const camera_id of ['http://camera/stream','other',null,0,{},undefined])assert.throws(()=>validateCommandData('start_job',{...input,camera_id}),{code:'INVALID_COMMAND'});
  for(const cameras of [[],['mac_camera']])assert.throws(()=>validateCommandData('start_job',{...input,camera_id:'esp32_cam'},[],cameras),{code:'UNSUPPORTED_CAPABILITY'});
  assert.throws(()=>validateCommandData('start_job',{...input,camera_url:'http://camera'}),{code:'INVALID_COMMAND'});
 }
 assert.throws(()=>validateCommandData('stop_job',{camera_id:'mac_camera'}),{code:'INVALID_COMMAND'});
 const recipe=recipeFor();recipe.camera.camera_id='mac_camera';assert.throws(()=>readRecipe(JSON.stringify(recipe)));
});
test('status accepts the optional planner enum and legacy shape, without opening the contract',()=>{
 const status=()=>sampleEvidence().find(e=>e.type==='status');
 const legacy=status();delete legacy.data.planner;assert.doesNotThrow(()=>validateEvent(legacy));assert.equal(Object.hasOwn(legacy.data,'planner'),false);
 for(const planner of ['rules','ollama','nebius','bedrock',null]){const e=status();e.data.planner=planner;assert.equal(validateEvent(e).data.planner,planner);}
 for(const planner of ['unknown','Gemma','Nebius','',false,0,{},[],undefined]){const e=status();e.data.planner=planner;assert.throws(()=>validateEvent(e));}
 for(const change of [e=>e.data.model='Gemma',e=>e.data.prompt='count people',e=>delete e.data.state,e=>e.planner='rules']){const e=status();e.data.planner='rules';change(e);assert.throws(()=>validateEvent(e));}
 const e=observation();e.data.planner='rules';assert.throws(()=>validateEvent(e));
});
test('strict JSON rejects duplicate keys, non-finite values, invalid syntax, depth and byte limits',()=>{for(const s of ['{"x":1,"x":2}','{"x":1,"\\u0078":2}','1e999','{"a":undefined}','[1,]','\u00a01','{"a":1}tail','['.repeat(14)+'0'+']'.repeat(14)])assert.throws(()=>parseStrict(s));assert.throws(()=>parseStrict('"é"',3));assert.equal(parseStrict('{"safe":0}').safe,0);});
test('schema and extra contract checks reject unsafe imports and accept three demo recipes',()=>{for(const demo of ['counter','classroom','red_ball','privacy_guard'])assert.equal(readRecipe(JSON.stringify(recipeFor(demo))).version,1);for(const change of [r=>r.extra='x',r=>r.blocks.shift(),r=>r.camera.url='rtsp://camera',r=>r.blocks[3].settings.line=[[0,0],[0,0]],r=>r.actions.push({type:'motors',max_speed_ratio:.9})]){const r=recipeFor();change(r);assert.throws(()=>readRecipe(JSON.stringify(r)));}});
test('unknown_reason and Count reason are coherent for all 40 fixed codes in all languages',()=>{assert.equal(CODES.length,40);for(const code of CODES){const e=observation();e.data.target='unknown';e.data.occupancy=unknown(code);e.data.unknown_reason=code;assert.doesNotThrow(()=>validateEvent(e));for(const language of ['uz','ru','en'])assert.equal(codeMessage(code,language),messages[code][language]);e.data.unknown_reason=null;assert.throws(()=>validateEvent(e));}});
test('unreadable video faults explain the input problem without sending a path',()=>{const e={...observation(),type:'fault',data:{code:'VIDEO_UNREADABLE',effect:'off'}};assert.doesNotThrow(()=>validateEvent(e));assert.equal(codeMessage(e.data.code,'en'),'video file not found or unreadable.');assert.throws(()=>validateEvent({...e,data:{...e.data,path:'/private/clip.mp4'}}));});
test('zero, lost, clear, and historical gaps do not require unknown_reason; null is unconfigured',()=>{const e=observation();e.data.target='lost';e.data.motion='clear';e.data.occupancy=known(0);e.data.coverage='gapped';assert.doesNotThrow(()=>validateEvent(e));e.data.privacy='unknown';assert.throws(()=>validateEvent(e));e.data.occupancy=unknown('PRIVACY_UNAVAILABLE');e.data.target=e.data.motion='unknown';e.data.unknown_reason='PRIVACY_UNAVAILABLE';assert.doesNotThrow(()=>validateEvent(e));});
test('wire is closed, rejects identities, unknown codes and future times',()=>{for(const change of [e=>e.data.name='Ali',e=>e.data.unknown_reason='CUSTOM',e=>e.minute=Math.floor(Date.now()/60000)+2,e=>e.job_id='bad',e=>e.revision=null]){const e=observation();change(e);assert.throws(()=>validateEvent(e));}});
test('command input is bounded and closed',()=>{assert.doesNotThrow(()=>validateCommandData('start_job',{input:'prompt',language:'uz',text:'Sana'}));assert.throws(()=>validateCommandData('start_job',{input:'prompt',language:'uz',text:'x'.repeat(2001)}));assert.throws(()=>validateCommandData('stop_job',{resume:true}));assert.throws(()=>validateCommandData('finish_trial',{result:'pass',reason:'interrupted',expected_count:null}));});
test('start_job may say which way is "in" (Oct 25), only for prompts and only two values',()=>{const p={input:'prompt',language:'en',text:'count people'};assert.doesNotThrow(()=>validateCommandData('start_job',{...p,entry:'left_to_right'}));assert.throws(()=>validateCommandData('start_job',{...p,entry:'up'}));});
