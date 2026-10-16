import test from 'node:test';
import assert from 'node:assert/strict';
import {plannerPresentation,liveKind} from '../src/presentation.js';
import {targetSVG} from '../src/scene.js';
import {t} from '../src/i18n.js';
import {recipeFor,sampleEvidence} from '../src/demo.js';
import {createModel,ingest,liveView,invalidateLive} from '../src/model.js';

test('planner copy distinguishes local, cloud, null, missing and stale reports in all languages',()=>{
 const cases=[['rules','planner_rules','plannerLocal'],['ollama','planner_ollama','plannerLocal'],['nebius','planner_nebius','crossBorder'],[null,'plannerUnset','plannerDepends'],[undefined,'plannerNotReported','plannerDepends']];
 for(const [planner,label,disclosure] of cases){
  assert.deepEqual(plannerPresentation(planner===undefined?{}:{planner}),{label,disclosure});
  for(const lang of ['uz','ru','en'])for(const key of [label,disclosure])assert.notEqual(t(lang,key),key);
  assert.deepEqual(plannerPresentation({planner},true),{label:'unknown',disclosure:'plannerDepends'});
 }
});

test('colour-only recipes use the target view; the counting view requires line_counter',()=>{
 const colour=recipeFor('red_ball');colour.brain={type:'none'};colour.actions=[{type:'dashboard'}];
 assert.equal(liveKind(colour),'target');
 assert.equal(liveKind(recipeFor('classroom')),'counter');
 const people=recipeFor('counter');people.blocks=people.blocks.filter(b=>b.type!=='line_counter');
 assert.notEqual(liveKind(people),'counter');
 assert.equal(liveKind(recipeFor('privacy_guard')),'privacy_guard');
 assert.equal(liveKind(null),'unknown');
 for(const [target,x] of [['left',80],['center',180],['right',280]]){
  const svg=targetSVG(target,'Target');assert.match(svg,new RegExp(`class="target-dot" cx="${x}"`));assert.doesNotMatch(svg,/counting-line|entry-arrow|silhouette/);
 }
 for(const target of ['lost','unknown',null])assert.doesNotMatch(targetSVG(target),/class="target-dot"/);
});

test('target locations cannot survive privacy stops or a dropped connection',()=>{
 const model=createModel(),events=sampleEvidence(),status=events[0],observation=events[2];
 status.data.state='running';status.data.planner='ollama';ingest(model,status);observation.data.target='left';ingest(model,observation);
 assert.equal(liveView(model).target,'left');
 const held=structuredClone(status);held.seq=observation.seq+1;held.data.state='held';held.data.privacy='blocked';ingest(model,held);
 assert.equal(liveView(model).target,'unknown');
 invalidateLive(model);assert.equal(liveView(model).target,'unknown');
});
