// The Live screen's states (UX pass, Oct 18): every state says why, what to do, and offers one
// obvious next action; a privacy stop keeps its specific reason; texts exist in Uz/Ru/En.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createModel, ingest, liveView } from '../src/model.js';
import { sampleEvidence } from '../src/demo.js';
import { liveStep, stopWhy, todoFor, eyeClosedReason, TEST_SECONDS } from '../src/presentation.js';
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
