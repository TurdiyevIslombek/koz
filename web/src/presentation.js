// A missing report is not a rules-based plan. Null also covers imports and failed planning.
export function plannerPresentation(status,offline=false,cloud=false){
 if(offline)return {label:'unknown',disclosure:cloud?'cloudDepends':'plannerDepends'};
 const planner=status?.planner;
 return {
  label:planner===undefined?'plannerNotReported':planner===null?'plannerUnset':`planner_${planner}`,
  disclosure:cloud?(planner==='bedrock'?'cloudBedrock':planner==='nebius'?'cloudNebius':['rules','ollama'].includes(planner)?'cloudLocal':'cloudDepends'):(planner==='bedrock'?'bedrockPrivacy':planner==='nebius'?'crossBorder':['rules','ollama'].includes(planner)?'plannerLocal':'plannerDepends')
 };
}

export function liveKind(recipe){
 if(recipe?.blocks.some(b=>b.type==='color_finder'))return 'target';
 if(recipe?.blocks.some(b=>b.type==='line_counter'))return 'counter';
 return recipe?'privacy_guard':'unknown';
}

// Selection belongs to the runner session, never to the portable recipe or localStorage.
export function cameraChoice(status,previous={}){
 const session_id=status?.session_id,slots=status?.data.cameras||[];
 const camera_id=previous.session_id===session_id&&slots.includes(previous.camera_id)?previous.camera_id:slots[0]||null;
 return {session_id,slots,camera_id};
}
export function withCamera(input,status,selection){
 const {camera_id}=cameraChoice(status,selection);
 return camera_id?{...input,camera_id}:input;
}

// --- What the Live screen says, and the one thing to do next (UX pass, Oct 18) ---------------------
// Every state gets a title, why, what to do, and at most two actions (the first is the obvious one).
export const TEST_SECONDS = 3;   // the runner tries each round for 3 s (contract section 9)
const PRIVACY_STOPS = new Set(['PRIVATE_BATHROOM','PRIVATE_TOILET','PRIVATE_BEDROOM','PRIVATE_CHANGING_ROOM','LENS_COVERED','PRIVACY_UNCERTAIN','SCENE_CHANGED']);
const REFUSALS = new Set(['IDENTITY_FORBIDDEN','PROFILING_FORBIDDEN','VIEW_FORBIDDEN','AUDIO_FORBIDDEN','FRAMES_FORBIDDEN','SOLE_PROTECTION_FORBIDDEN','MOTOR_TARGET_FORBIDDEN','ACTUATOR_FORBIDDEN','SCHOOL_COUNTS_ONLY','SAFETY_LOCKED','RETENTION_LOCKED','UNSUPPORTED_CAPABILITY','INVALID_RECIPE']);
const TODO = {LENS_COVERED:'lensTodo',PRIVACY_UNCERTAIN:'uncertainTodo',MOTOR_NOT_ARMED:'motorTodo',MOTOR_SAFETY_STOP:'motorTodo',
 FRAME_STALE:'cameraTodo',OVERLOADED:'cameraTodo',CHECK_FAILED:'checkFailedTodo',ADJUSTMENT_LIMIT:'checkFailedTodo',
 OWNERSHIP_REQUIRED:'setupTodo',ALLOWED_AREA_REQUIRED:'setupTodo',PLANNER_UNAVAILABLE:'plannerTodo'};

// The stop reason in the runner window's words: the object it saw, else the room it thinks this is.
export function stopWhy(code,seen){
 if(seen&&['PRIVATE_BEDROOM','PRIVATE_BATHROOM'].includes(code))return {key:`seen_${seen}`};
 if(code?.startsWith('PRIVATE_'))return {key:`room_${code}`};
 if(code==='LENS_COVERED'||code==='PRIVACY_UNCERTAIN')return {key:`why_${code}`};
 return {code};
}
export function todoFor(code){
 if(REFUSALS.has(code))return 'refusedTodo';
 if(code?.startsWith('PRIVATE_')||code==='SCENE_CHANGED')return 'privacyTodo';
 return TODO[code]||'restartTodo';
}

// view: liveView(model). fault: the job's latest fault data ({code, effect, seen?}), kept after a
// later idle. stoppedBy: 'owner' when this page's Stop ended the job. canRetry: the same job can be
// started again. testing: {since, revision} of the current test round.
export function liveStep(view,{fault=null,stoppedBy=null,canRetry=false,hasJob=false,testing=null,kind='unknown',motors=false,trialUsed=false,now=Date.now()}={}){
 // In a trial whose one job already ran, "Try again" would be refused (one job per trial): the same
 // button finishes the trial first (recorded as unknown, interrupted), then starts the job again.
 const retry=trialUsed?'finishRetry':'retry';
 const actions=list=>list.map(a=>a==='retry'?retry:a).filter(a=>a===retry?canRetry:true);
 const withNote=step=>trialUsed&&step.actions.includes('finishRetry')?{...step,note:'trialRetryTodo'}:step;
 if(view.offline)return {step:'offline',tone:'unknown',title:'offlineTitle',why:{key:'offlineReason'},todo:'offlineTodo',actions:[]};
 const state=view.status.state;
 // A fault wins at once, whatever the status still says (a privacy stop shows before "held" arrives).
 if(fault&&state!=='planning'){
  const code=fault.code;
  if(PRIVACY_STOPS.has(code))return withNote({step:'privacyStop',tone:'bad',title:'privacyStopTitle',why:stopWhy(code,fault.seen),todo:todoFor(code),actions:actions(['retry','newJob'])});
  if(REFUSALS.has(code))return {step:'refused',tone:'bad',title:'refusedTitle',why:{code},todo:'refusedTodo',actions:['newJob']};
  return withNote({step:'problem',tone:'bad',title:'stopped',why:{code},todo:todoFor(code),actions:actions(['retry','newJob'])});
 }
 if(state==='planning')return {step:'planning',tone:'warn',title:'planningTitle',why:{key:'planningWhy'},actions:['stop']};
 if(state==='checking')return {step:'confirming',tone:'warn',title:'confirmingTitle',why:{key:'confirmingWhy'},actions:['stop']};
 if(state==='evaluating'){
  const elapsed=testing?Math.max(0,(now-testing.since)/1000):0,left=Math.ceil(TEST_SECONDS-elapsed);
  return {step:'testing',tone:'warn',title:left>0?'testingTitle':'testingJudging',why:{key:view.status&&testing?.revision>1?'testingAdjusted':'testingWhy'},
   actions:['stop'],test:{elapsed:Math.min(elapsed,TEST_SECONDS),left:Math.max(left,0),round:testing?.revision||1}};
 }
 if(state==='running'){
  // Any unknown output: amber, in the contract's own words (section 11), never green "Running".
  if(view.reason==='FRAME_STALE')return {step:'cameraLost',tone:'warn',title:'cameraLostTitle',why:{code:'FRAME_STALE'},todo:'cameraLostTodo',actions:['stop']};
  if(view.reason||view.state==='unknown')return {step:'unknownOutput',tone:'warn',title:'unknownTitle',why:view.reason?{code:view.reason}:{key:'waitingNumbersWhy'},
   todo:view.reason==='OVERLOADED'?'overloadedTodo':'unknownTodo',actions:['stop']};
  return {step:'running',tone:'good',title:'running',why:{key:motors?'runningCar':kind==='counter'?'runningReason':kind==='target'?'runningTarget':'runningGuard'},actions:['stop']};
 }
 if(state==='idle'&&stoppedBy==='owner')return withNote({step:'stoppedByYou',tone:'neutral',title:'stopped',why:{key:'youStopped'},todo:'stoppedTodo',actions:actions(['retry','newJob'])});
 if(hasJob||state!=='idle')return withNote({step:'stopped',tone:'neutral',title:'stopped',why:{key:'jobEnded'},todo:canRetry?'stoppedTodo':'idleTodo',actions:actions(['retry','newJob'])});
 return {step:'idle',tone:'neutral',title:'idleTitle',why:{key:'idleWhy'},todo:'idleTodo',actions:['newJob']};
}

// What "Try again" starts: the same job, on the SAME camera it ran on. lastStart is what this page
// started ({input, camera_id, job_id}); stored is {session_id, job_id, camera_id} kept by this tab
// (no prompt text) so the camera survives a page reload; recipe is the job's first checked recipe.
// Never the camera picked now: if the job's camera is unknown, the runner's default is used.
export function retryStart({lastStart=null,stored=null,status=null,recipe=null}={}){
 const job=status?.job_id;
 if(!job)return null;
 const same=lastStart?.job_id===job?lastStart:null;
 const input=same?.input||(recipe?{input:'recipe',recipe}:null);
 if(!input)return null;
 const camera=same?same.camera_id:(stored?.job_id===job&&stored?.session_id===status.session_id?stored.camera_id:undefined);
 return camera?{...input,camera_id:camera}:{...input};
}

// The short words under a closed eye.
export function eyeClosedReason(step){
 return {privacyStop:'eyeClosedPrivacy',confirming:'eyeChecking',cameraLost:'eyeLate',offline:'eyeOffline',
  testing:'eyeWaiting',running:'eyeWaiting',unknownOutput:'eyeWaiting',planning:'eyePlanning'}[step.step]||'eyeClosedStopped';
}

// The Connect device window (Oct 22). A new token disconnects the camera computer at once, so it is
// never one press away while that computer is connected: first "Replace…", then a warning to confirm.
// connected: the server has a live device. asking: the owner pressed Replace. token: just made (shown once).
export function deviceDialog({connected=false,asking=false,token=''}={}){
 const status=connected?'deviceConnectedNow':'deviceNotConnectedNow';
 if(token)return {status,actions:['copy-token'],note:'tokenPasteHint',showToken:true};
 if(connected&&asking)return {status,actions:['token','token-cancel'],warning:'tokenReplaceWarning'};
 if(connected)return {status,actions:['token-ask']};
 return {status,actions:['token'],note:'tokenFirstHint'};
}
