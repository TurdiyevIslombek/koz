import validateSchema from './generated/recipe.js';
import { messages } from './generated/messages.js';
export { messages };
export const CODES = Object.keys(messages);
export const codeMessage = (code, language = 'uz') => (messages[code] || messages.INTERNAL_ERROR)[language] || messages.INTERNAL_ERROR.uz;
export class ContractError extends Error { constructor(code = 'INVALID_EVENT') { super(code); this.code = code; } }
const fail = code => { throw new ContractError(code); };
const obj = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const integer = (v, min = 0, max = 2147483647) => Number.isInteger(v) && v >= min && v <= max;
const number = (v, min, max) => typeof v === 'number' && Number.isFinite(v) && v >= min && v <= max;
const one = (...values) => v => values.includes(v);
const nullable = test => v => v === null || test(v);
const id = v => typeof v === 'string' && /^[a-f0-9]{32}$/.test(v);
const code = one(...CODES);
const list = (test, min = 0, max = 10) => v => Array.isArray(v) && v.length >= min && v.length <= max && v.every(test);
const closed = (value, spec) => obj(value) && Object.keys(value).length === Object.keys(spec).length && Object.entries(spec).every(([k,test]) => Object.hasOwn(value,k) && test(value[k]));
const checks = one('target_visible','target_centered','counts_available','motion_available','privacy_approved');
const results = one('pass','fail','unknown');
const labels = one('left','center','right','lost','detected','clear','risk','approved','blocked','known','unknown');
export const changes = {
  'color_finder.hue_center':[0,179,true], 'color_finder.hue_half_width':[1,30,true],
  'color_finder.saturation_min':[50,255,true], 'color_finder.value_min':[30,255,true],
  'color_finder.min_area_ratio':[.001,.25], 'motion_zone.pixel_delta':[10,80,true],
  'motion_zone.min_changed_ratio':[.01,.5], 'person_detector.min_confidence':[.3,.95],
  'brain.turn_gain':[.1,2], 'brain.deadband':[.02,.25]
};
export const isChange = v => closed(v,{setting:one(...Object.keys(changes)),before:v=>typeof v==='number',after:v=>typeof v==='number'}) && v.before!==v.after && [v.before,v.after].every(n=>{const [min,max,int]=changes[v.setting];return number(n,min,max)&&(!int||Number.isInteger(n));});
export const isCount = v => closed(v,{state:one('known','unknown'),value:nullable(integer),reason:nullable(code)}) && (v.state==='known' ? v.value!==null&&v.reason===null : v.value===null&&v.reason!==null);

// JSON.parse silently accepts duplicate keys. The wire and import formats explicitly do not.
export function parseStrict(text, maxBytes = 32768, errorCode = 'INVALID_EVENT') {
  if(typeof text!=='string'||new TextEncoder().encode(text).length>maxBytes) fail(errorCode);
  let at=0; const ws=()=>{while(/[ \t\n\r]/.test(text[at]||'')&&at<text.length)at++;};
  const string=()=>{const start=at++;while(at<text.length){const c=text[at++];if(c==='"'){try{return JSON.parse(text.slice(start,at));}catch{fail(errorCode);}}if(c==='\\')at++;}fail(errorCode);};
  const value=depth=>{
    if(depth>12)fail(errorCode);ws();const c=text[at];
    if(c==='"')return string();
    if(c==='{') {at++;ws();const result={},seen=new Set();if(text[at]==='}'){at++;return result;}for(;;){ws();if(text[at]!=='"')fail(errorCode);const key=string();if(seen.has(key))fail(errorCode);seen.add(key);ws();if(text[at++]!==':')fail(errorCode);Object.defineProperty(result,key,{value:value(depth+1),enumerable:true,writable:true,configurable:true});ws();const end=text[at++];if(end==='}')return result;if(end!==',')fail(errorCode);}}
    if(c==='['){at++;ws();const result=[];if(text[at]===']'){at++;return result;}for(;;){result.push(value(depth+1));ws();const end=text[at++];if(end===']')return result;if(end!==',')fail(errorCode);}}
    for(const [literal,val] of [['true',true],['false',false],['null',null]])if(text.startsWith(literal,at)){at+=literal.length;return val;}
    const token=text.slice(at).match(/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/);if(!token)fail(errorCode);at+=token[0].length;const n=Number(token[0]);if(!Number.isFinite(n))fail(errorCode);return n;
  };
  const result=value(0);ws();if(at!==text.length)fail(errorCode);return result;
}

export function validateRecipe(recipe, capabilities = null) {
  if(new TextEncoder().encode(JSON.stringify(recipe)).length>16384||!validateSchema(recipe))fail('INVALID_RECIPE');
  const order=['privacy_guard','face_blur','color_finder','motion_zone','person_detector','line_counter','looming'];
  const types=recipe.blocks.map(b=>b.type);
  if(new Set(types).size!==types.length||types.some((t,i)=>i>0&&order.indexOf(t)<=order.indexOf(types[i-1])))fail('INVALID_RECIPE');
  for(const b of recipe.blocks){
    if(b.type==='motion_zone'){const [l,t,r,bt]=b.settings.rect;if(!(l<r&&t<bt))fail('INVALID_RECIPE');}
    if(b.type==='line_counter'){const [a,c]=b.settings.line;if(a[0]===c[0]&&a[1]===c[1])fail('INVALID_RECIPE');}
    if(b.type==='looming'&&capabilities&&!capabilities.includes('looming'))fail('UNSUPPORTED_CAPABILITY');
  }
  const alert=recipe.actions.find(a=>a.type==='alert');
  if(alert&&!(alert.template==='motion_detected'?types.includes('motion_zone'):types.includes('person_detector')))fail('INVALID_RECIPE');
  return recipe;
}

const observation = d => {
  if(!closed(d,{round:nullable(v=>integer(v,1,3)),privacy:one('approved','blocked','unknown'),occupancy:nullable(isCount),entered:nullable(isCount),exited:nullable(isCount),coverage:one('complete','gapped'),target:nullable(one('left','center','right','lost','unknown')),motion:nullable(one('detected','clear','unknown')),looming:nullable(one('risk','clear','unknown')),alert:nullable(one('motion_detected','count_changed')),unknown_reason:nullable(code)}))return false;
  const counts=[d.occupancy,d.entered,d.exited];
  const unknown=counts.some(c=>c?.state==='unknown')||[d.target,d.motion,d.looming].includes('unknown')||d.privacy!=='approved';
  if(unknown !== (d.unknown_reason!==null))return false;
  if(counts.some(c=>c?.state==='unknown'&&c.reason!==d.unknown_reason))return false;
  if(d.privacy!=='approved'&&(counts.some(c=>c?.state==='known')||[d.target,d.motion,d.looming].some(c=>c!==null&&c!=='unknown')||d.alert!==null))return false;
  return true;
};
const decision = (d,e) => closed(d,{round:v=>integer(v,1,3),evidence_seq:list(v=>integer(v,1,Number.MAX_SAFE_INTEGER),1,10),check:checks,result:results,next:one('run','adjust','stop'),next_revision:nullable(v=>integer(v,1,3)),change:nullable(isChange),code:nullable(code)}) &&
  (d.next==='adjust'?e.revision<3&&d.next_revision===e.revision+1&&d.change!==null&&d.code===null : d.next==='run'?d.next_revision===e.revision&&d.change===null&&d.code===null&&d.result==='pass':d.next_revision===null&&d.change===null&&d.code!==null);
const agentChange = v => closed(v,{from_revision:n=>integer(n,1,2),to_revision:n=>integer(n,2,3),check:checks,before_label:labels,change:isChange,executed:one(true),after_label:labels,after_result:results})&&v.to_revision===v.from_revision+1;
const trialResult = d => closed(d,{demo:one('red_ball','classroom','privacy_guard'),index:v=>integer(v,1,10),result:results,basis:one('owner_report'),reason:one('none','missed_target','wrong_direction','count_mismatch','privacy_miss','safety_stop','interrupted','unknown'),expected_count:nullable(integer),observed_count:nullable(isCount),fault_code:nullable(code),evidence:one('complete','incomplete'),agent_changes:list(agentChange,0,2)}) &&
  (d.demo==='classroom'||d.expected_count===null&&d.observed_count===null) && (d.result!=='pass'||d.reason==='none'&&(d.demo==='privacy_guard'||d.observed_count?.state!=='unknown'));
const specs={
  status:d=>closed(d,{state:one('idle','planning','checking','evaluating','running','held','refused'),camera_on:v=>typeof v==='boolean',privacy:one('approved','blocked','unknown'),school:v=>typeof v==='boolean',motor:one('not_present','disarmed','enabled','stop_commanded'),opencv_major:one(5,null),capabilities:list(one('rtsp','recorded_fixture','looming','scene_tripwire'),0,4)}),
  recipe:(d,e)=>closed(d,{origin:one('planner','import','adjustment'),caused_by:nullable(v=>integer(v,1,Number.MAX_SAFE_INTEGER)),recipe:r=>{try{validateRecipe(r);return true;}catch{return false;}}})&&(d.origin==='adjustment'?d.caused_by!==null:d.caused_by===null),
  observation,decision,
  command_result:d=>closed(d,{command_id:id,result:one('accepted','rejected'),code:nullable(code)})&&(d.result==='accepted'?d.code===null:d.code!==null),
  fault:d=>closed(d,{code,effect:one('off','held')}),trial_result:trialResult
};
export function validateEvent(e, now=Date.now()) {
  if(!closed(e,{v:one(1),type:one(...Object.keys(specs)),session_id:id,seq:v=>integer(v,1,Number.MAX_SAFE_INTEGER),job_id:nullable(id),trial_id:nullable(id),revision:nullable(v=>integer(v,1,3)),minute:v=>integer(v,0,Math.floor(now/60000)+1),data:obj})||!specs[e.type](e.data,e))fail();
  if(['recipe','observation','decision'].includes(e.type)&&(e.job_id===null||e.revision===null))fail();
  if(e.type==='trial_result'&&e.trial_id===null)fail();
  return e;
}
export const readEvent = (text,now) => validateEvent(parseStrict(text),now);
export const readRecipe = text => validateRecipe(parseStrict(text,16384,'INVALID_RECIPE'));
export function validateCommandData(command,data,capabilities=[]) {
  let valid=false;
  if(command==='start_job') {
    valid=closed(data,{input:one('prompt'),language:one('uz','ru','en'),text:v=>typeof v==='string'&&Array.from(v.trim()).length>0&&Array.from(v).length<=2000});
    if(!valid&&closed(data,{input:one('recipe'),recipe:obj})){validateRecipe(data.recipe,capabilities);valid=true;}
  } else if(command==='stop_job')valid=closed(data,{});
  else if(command==='begin_trial')valid=closed(data,{demo:one('red_ball','classroom','privacy_guard'),index:v=>integer(v,1,10)});
  else if(command==='finish_trial')valid=closed(data,{result:results,reason:one('none','missed_target','wrong_direction','count_mismatch','privacy_miss','safety_stop','interrupted','unknown'),expected_count:nullable(integer)})&&(data.result!=='pass'||data.reason==='none');
  if(!valid)fail('INVALID_COMMAND');return data;
}
export function newId(){return [...crypto.getRandomValues(new Uint8Array(16))].map(n=>n.toString(16).padStart(2,'0')).join('');}
