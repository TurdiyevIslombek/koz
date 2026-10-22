// The Live screen's states (UX pass, Oct 18): every state says why, what to do, and offers one
// obvious next action; a privacy stop keeps its specific reason; texts exist in Uz/Ru/En.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createModel, ingest, liveView } from '../src/model.js';
import { sampleEvidence } from '../src/demo.js';
import { liveStep, stopWhy, todoFor, eyeClosedReason, TEST_SECONDS, deviceDialog, dockActions, diagramCover, macEyeWanted } from '../src/presentation.js';
import { validateEvent } from '../src/protocol.js';
import { t, languages } from '../src/i18n.js';

function counter(state = 'running') {
  const m = createModel(), events = sampleEvidence(), s = events[0];
  s.data.state = state; s.trial_id = null; s.minute = Math.floor(Date.now() / 60000);
  ingest(m, s);
  return { m, s };
}
const next = (s, seq, patch) => ({ ...s, seq, ...patch, data: { ...s.data, ...(patch.data || {}) } });
const view = state => ({ offline: false, reason: null, status: { state } });

test('every live state has a title, a reason and at most two actions, the first one obvious', () => {
  const cases = [
    [view('planning'), {}, 'planning', ['stop']],
    [view('checking'), {}, 'confirming', ['stop']],
    [view('evaluating'), {}, 'testing', ['stop']],
    [view('running'), {}, 'running', ['stop']],
    [{ ...view('running'), reason: 'FRAME_STALE' }, {}, 'cameraLost', ['stop']],
    [view('held'), { fault: { code: 'PRIVATE_BEDROOM', seen: 'bed' }, canRetry: true }, 'privacyStop', ['retry', 'newJob']],
    [view('refused'), { fault: { code: 'IDENTITY_FORBIDDEN' }, canRetry: true }, 'refused', ['newJob']],
    [view('idle'), { stoppedBy: 'owner', canRetry: true, hasJob: true }, 'stoppedByYou', ['retry', 'newJob']],
    [view('idle'), { hasJob: true, canRetry: true }, 'stopped', ['retry', 'newJob']],
    [view('idle'), {}, 'idle', ['newJob']],
    [{ offline: true }, {}, 'offline', []],
  ];
  for (const [v, context, step, actions] of cases) {
    const result = liveStep(v, context);
    assert.equal(result.step, step);
    assert.deepEqual(result.actions, actions, step);
    assert.ok(result.title && result.why, step);
  }
});

test('a privacy stop names what the guard saw, like the runner window, and says what to do', () => {
  assert.deepEqual(stopWhy('PRIVATE_BEDROOM', 'bed'), { key: 'seen_bed' });
  assert.deepEqual(stopWhy('PRIVATE_BEDROOM'), { key: 'room_PRIVATE_BEDROOM' });
  assert.deepEqual(stopWhy('PRIVATE_BATHROOM', 'toilet'), { key: 'seen_toilet' });
  assert.deepEqual(stopWhy('LENS_COVERED'), { key: 'why_LENS_COVERED' });
  assert.deepEqual(stopWhy('CHECK_FAILED'), { code: 'CHECK_FAILED' });
  assert.equal(todoFor('PRIVATE_TOILET'), 'privacyTodo');
  assert.equal(todoFor('LENS_COVERED'), 'lensTodo');
  assert.equal(todoFor('MOTOR_NOT_ARMED'), 'motorTodo');
  assert.equal(todoFor('IDENTITY_FORBIDDEN'), 'refusedTodo');
  assert.equal(eyeClosedReason({ step: 'privacyStop' }), 'eyeClosedPrivacy');
  assert.equal(t('en', 'seen_bed'), 'A bed is in view.');
  assert.equal(t('en', 'privacyTodo'), 'Point the camera away, then press Try again.');
});

test('without anything to retry, Try again is not offered', () => {
  const step = liveStep(view('held'), { fault: { code: 'PRIVATE_BATHROOM' }, canRetry: false });
  assert.deepEqual(step.actions, ['newJob']);
});

test('testing shows a 3-second countdown and its round, then "checking the result"', () => {
  const now = 10_000;
  const early = liveStep(view('evaluating'), { testing: { since: now - 1200, revision: 2 }, now });
  assert.equal(early.title, 'testingTitle');
  assert.equal(early.test.left, 2);
  assert.equal(early.test.round, 2);
  assert.equal(early.why.key, 'testingAdjusted');
  const late = liveStep(view('evaluating'), { testing: { since: now - (TEST_SECONDS + 1) * 1000, revision: 1 }, now });
  assert.equal(late.title, 'testingJudging');
  assert.equal(late.test.left, 0);
});

test('the stop reason survives the idle status that follows it, until a new job starts', () => {
  const { m, s } = counter('running');
  ingest(m, { ...s, type: 'fault', seq: 50, revision: null, data: { code: 'PRIVATE_BEDROOM', effect: 'held', seen: 'bed' } });
  ingest(m, next(s, 51, { data: { state: 'held', privacy: 'blocked' } }));
  ingest(m, next(s, 52, { data: { state: 'idle', privacy: 'blocked' } }));   // e.g. q pressed after the stop
  assert.equal(m.fault, null);
  assert.equal(m.lastStop.data.seen, 'bed');
  const step = liveStep(liveView(m), { fault: m.lastStop.data, canRetry: true, hasJob: true });
  assert.equal(step.step, 'privacyStop');
  assert.equal(step.why.key, 'seen_bed');
  ingest(m, next(s, 53, { job_id: 'b'.repeat(32), data: { state: 'planning' } }));   // a new job
  assert.equal(m.lastStop, null);
});

test('this page\'s Stop is remembered as "stopped by you"; the test round start is kept across heartbeats', () => {
  const { m, s } = counter('evaluating');
  const since = m.testing.since;
  ingest(m, next(s, 60, { data: { state: 'evaluating' } }), since + 1000);   // a heartbeat
  assert.equal(m.testing.since, since);
  m.pending = { command_id: 'c'.repeat(32), command: 'stop_job', session_id: s.session_id, job_id: s.job_id };
  ingest(m, next(s, 61, { data: { state: 'idle' } }));
  assert.equal(m.stoppedBy, 'owner');
  assert.equal(m.testing, null);
});

test('fault.seen is accepted only with the listed objects', () => {
  const { s } = counter();
  const fault = data => ({ ...s, type: 'fault', seq: 70, revision: null, data });
  validateEvent(fault({ code: 'PRIVATE_BEDROOM', effect: 'held', seen: 'bed' }));
  assert.throws(() => validateEvent(fault({ code: 'PRIVATE_BEDROOM', effect: 'held', seen: 'cat' })));
});

test('every text the Live states use exists in Uzbek, Russian and English', () => {
  const keys = ['idleTitle', 'idleWhy', 'idleTodo', 'planningTitle', 'planningWhy', 'testingTitle', 'testingWhy', 'testingAdjusted',
    'testingTry', 'testingJudging', 'secondsLeft', 'runningTarget', 'runningGuard', 'runningCar', 'confirmingTitle', 'confirmingWhy',
    'privacyStopTitle', 'seen_bed', 'seen_toilet', 'seen_sink', 'room_PRIVATE_BEDROOM', 'room_PRIVATE_BATHROOM', 'room_PRIVATE_TOILET',
    'room_PRIVATE_CHANGING_ROOM', 'why_LENS_COVERED', 'why_PRIVACY_UNCERTAIN', 'privacyTodo', 'lensTodo', 'uncertainTodo', 'youStopped',
    'jobEnded', 'stoppedTodo', 'refusedTitle', 'refusedTodo', 'cameraLostTitle', 'cameraLostWhy', 'cameraLostTodo', 'cameraTodo',
    'offlineTitle', 'offlineTodo', 'checkFailedTodo', 'motorTodo', 'setupTodo', 'plannerTodo', 'restartTodo', 'retry', 'newJob',
    'waitingCamera', 'notCounting', 'targetWhere', 'armHint', 'eyeClosedPrivacy', 'eyeClosedStopped', 'eyeWaiting', 'eyeOffline'];
  for (const key of keys) {
    const texts = languages.map(language => t(language, key));
    assert.ok(texts.every(text => text && text !== key), key);
    assert.equal(new Set(texts.slice(0, 2)).size, 2, `${key}: Uzbek and Russian differ`);
  }
  const english = ['sinceEvaluation', 'accepted', 'sinceStart', 'now', 'fresh'].map(key => t('en', key));
  for (const jargon of ['Evaluation measurement', 'Request accepted', 'Since job start · crossings', 'In the area now', 'Fresh data'])
    assert.ok(!english.includes(jargon), jargon);
});

// --- Codex's findings on the UX pass (Oct 19) ----------------------------------------------------------
import { retryStart } from '../src/presentation.js';

test('a fault wins at once, even before the status says held: never green Running', () => {
  const step = liveStep({ offline: false, reason: 'PRIVATE_BEDROOM', state: 'blocked', status: { state: 'running' } },
    { fault: { code: 'PRIVATE_BEDROOM', seen: 'bed' }, canRetry: true });
  assert.equal(step.step, 'privacyStop');
  assert.equal(step.why.key, 'seen_bed');
  const other = liveStep({ offline: false, reason: 'BLUR_UNAVAILABLE', state: 'stopped', status: { state: 'running' } },
    { fault: { code: 'BLUR_UNAVAILABLE' }, canRetry: true });
  assert.equal(other.tone, 'bad');
});

test('an unknown output while running is amber with the fixed contract message, never green', () => {
  for (const reason of ['OVERLOADED', 'PRIVACY_UNCERTAIN', 'FRAME_STALE']) {
    const step = liveStep({ offline: false, reason, state: 'unknown', status: { state: 'running' } }, {});
    assert.notEqual(step.tone, 'good', reason);
    assert.deepEqual(step.why, { code: reason }, reason);   // the contract's own words (section 11)
    assert.deepEqual(step.actions, ['stop']);
  }
  const noNumbersYet = liveStep({ offline: false, reason: null, state: 'unknown', status: { state: 'running' } }, {});
  assert.equal(noNumbersYet.tone, 'warn');
  const fine = liveStep({ offline: false, reason: null, state: 'running', status: { state: 'running' } }, {});
  assert.equal(fine.tone, 'good');
});

test('Try again keeps the camera the job ran on, also after a page reload', () => {
  const status = { session_id: 's'.repeat(32), job_id: 'j'.repeat(32) };
  const recipe = { version: 1 };
  const fromPage = retryStart({ lastStart: { job_id: status.job_id, input: { input: 'prompt', language: 'uz', text: 'x' }, camera_id: 'esp32_cam' }, status, recipe });
  assert.deepEqual(fromPage, { input: 'prompt', language: 'uz', text: 'x', camera_id: 'esp32_cam' });
  const afterReload = retryStart({ lastStart: null, stored: { session_id: status.session_id, job_id: status.job_id, camera_id: 'esp32_cam' }, status, recipe });
  assert.deepEqual(afterReload, { input: 'recipe', recipe, camera_id: 'esp32_cam' });
  const otherJob = retryStart({ lastStart: null, stored: { session_id: status.session_id, job_id: 'k'.repeat(32), camera_id: 'esp32_cam' }, status, recipe });
  assert.deepEqual(otherJob, { input: 'recipe', recipe });           // no camera known: the runner's default
  assert.equal(retryStart({ lastStart: null, status: { job_id: null }, recipe }), null);
});

test('inside a trial whose job already ran, the one button is "Finish trial and try again"', () => {
  const held = { offline: false, reason: null, state: 'stopped', status: { state: 'held' } };
  const step = liveStep(held, { fault: { code: 'PRIVATE_BEDROOM' }, canRetry: true, trialUsed: true });
  assert.deepEqual(step.actions, ['finishRetry', 'newJob']);
  assert.equal(step.todo, 'privacyTodo');             // what to do about the stop stays
  assert.equal(step.note, 'trialRetryTodo');         // plus what the button does to the trial
  const idle = liveStep({ offline: false, reason: null, state: 'stopped', status: { state: 'idle' } }, { stoppedBy: 'owner', canRetry: true, hasJob: true, trialUsed: true });
  assert.deepEqual(idle.actions, ['finishRetry', 'newJob']);
  for (const key of ['finishRetry', 'trialRetryTodo', 'unknownTitle'])
    assert.ok(languages.every(language => t(language, key) !== key), key);
});

test('Connect device never replaces the token by itself (Oct 22: each open-and-press disconnected the Mac)',()=>{
 const live=deviceDialog({connected:true});
 assert.equal(live.status,'deviceConnectedNow');assert.deepEqual(live.actions,['token-ask']);   // no one-press new token
 const asking=deviceDialog({connected:true,asking:true});
 assert.deepEqual(asking.actions,['token','token-cancel']);assert.equal(asking.warning,'tokenReplaceWarning');
 const none=deviceDialog({connected:false});
 assert.equal(none.status,'deviceNotConnectedNow');assert.deepEqual(none.actions,['token']);assert.equal(none.note,'tokenFirstHint');
 const made=deviceDialog({connected:false,token:'a'.repeat(64)});
 assert.deepEqual(made.actions,['copy-token']);assert.equal(made.note,'tokenPasteHint');assert.equal(made.showToken,true);
 for(const d of [live,asking,none,made])for(const key of [d.status,d.warning,d.note].filter(Boolean))
  for(const lang of ['uz','ru','en'])assert.notEqual(t(lang,key),key,`${key} in ${lang}`);
});

test('the bottom bar shows Live actions only on the Live tab; Stop stays reachable everywhere (design review, Oct 22)',()=>{
 const stopped={step:'privacyStop',actions:['retry','newJob']},running={step:'running',actions:['stop']},idle={step:'idle',actions:['newJob']};
 assert.deepEqual(dockActions(stopped,'live',{hasJob:true}),['retry','newJob']);
 assert.deepEqual(dockActions(stopped,'trials',{hasJob:true}),['openLive']);   // no "Try again" out of context
 assert.deepEqual(dockActions(stopped,'setup',{hasJob:true}),['openLive']);
 assert.deepEqual(dockActions(running,'setup',{hasJob:true}),['stop']);        // a running job (or a car) can always be stopped
 assert.deepEqual(dockActions(running,'trials',{hasJob:true}),['stop']);
 assert.deepEqual(dockActions(idle,'setup',{hasJob:false}),[]);                // no second "New job" under "Test it"
 assert.deepEqual(dockActions(idle,'live',{hasJob:false}),['newJob']);
});
test('the AWS diagram never claims to be a view: it says the job state (design review, Oct 22)',()=>{
 assert.equal(diagramCover({step:'running'}),null);
 assert.equal(diagramCover({step:'testing'}),'coverTesting');
 assert.equal(diagramCover({step:'privacyStop'}),'coverPrivacy');
 assert.equal(diagramCover({step:'cameraLost'}),'coverWaiting');assert.equal(diagramCover({step:'unknownOutput'}),'coverWaiting');
 assert.equal(diagramCover({step:'offline'}),'coverOffline');
 for(const step of ['stopped','stoppedByYou','refused','problem','idle'])assert.equal(diagramCover({step}),'coverStopped');
 for(const key of ['diagramHeading','targetHeading','coverTesting','coverPrivacy','coverWaiting','coverOffline','coverStopped','openLive','cameraComputer','shareTitle','ownerLogin','moreNotRun'])
  for(const lang of ['uz','ru','en'])assert.notEqual(t(lang,key),key,`${key} in ${lang}`);
 assert.doesNotMatch(t('en','diagramHeading'),/sees/);
});
test('plain words: no bare "rules" planner, no first person in the plan box, short Russian tab (design review, Oct 22)',()=>{
 for(const lang of ['uz','ru','en'])assert.ok(t(lang,'planner_rules').length>8,lang);
 assert.doesNotMatch(t('en','planPromise'),/\bI\b/);assert.doesNotMatch(t('uz','planPromise'),/raman\b/);assert.doesNotMatch(t('ru','planPromise'),/проверю|скрою/);
 assert.ok(t('ru','live').split(' ').length===1,'one Russian word fits the tab');
 assert.notEqual(t('en','held'),'on hold');
});

test('judges before anything is shared: "Not shared yet" with a sample run, never "not connected" (Oct 22)',()=>{
 const offline={offline:true,status:null,counts:[null,null,null]};
 const step=liveStep(offline,{notShared:true});
 assert.equal(step.step,'notShared');assert.equal(step.tone,'neutral');assert.equal(step.cta,'demo');assert.deepEqual(step.actions,[]);
 assert.equal(liveStep(offline,{}).step,'offline');   // the owner's own page still says offline
 for(const key of ['notSharedTitle','notSharedWhy','notSharedPill','capabilityHint','targetNotFoundTodo','trialsScope','picturePrivacy'])
  for(const lang of ['uz','ru','en'])assert.notEqual(t(lang,key),key,`${key} in ${lang}`);
});
test('a colour job that found nothing says what Koʻz can find (Oct 22: "three attempts failed")',()=>{
 assert.equal(todoFor('ADJUSTMENT_LIMIT','target'),'targetNotFoundTodo');
 assert.equal(todoFor('ADJUSTMENT_LIMIT','counter'),'checkFailedTodo');
 assert.equal(todoFor('UNSUPPORTED_CAPABILITY'),'capabilityHint');   // a refusal lists what Koʻz can do
 assert.match(t('en','targetNotFoundTodo'),/round/);assert.match(t('en','capabilityHint'),/ball/);
});

test('the eye picture is asked of this computer only for the owner, on the AWS page, while a job runs or tests (Oct 22)',()=>{
 const owner={cloud:true,owner:true,demo:false};
 assert.equal(macEyeWanted({...owner,step:'running'}),true);assert.equal(macEyeWanted({...owner,step:'testing'}),true);
 for(const step of ['privacyStop','confirming','cameraLost','offline','stopped','stoppedByYou','idle','planning','refused','problem','unknownOutput'])
  assert.equal(macEyeWanted({...owner,step}),false,step);
 assert.equal(macEyeWanted({cloud:true,owner:false,demo:false,step:'running'}),false);   // judges: never
 assert.equal(macEyeWanted({cloud:true,owner:true,demo:true,step:'running'}),false);    // the sample run: no camera
 assert.equal(macEyeWanted({cloud:false,owner:true,demo:false,step:'running'}),false);   // the local app has its own eye
});
