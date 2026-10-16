import assert from 'node:assert/strict';
import {once} from 'node:events';
import {mkdir,writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const {chromium}=await import(process.env.KOZ_PLAYWRIGHT_MODULE||'playwright');
import {WebSocketServer} from 'ws';
import {createApplication} from '../../server/index.mjs';
import {recipeFor,sampleEvidence,known} from '../../src/demo.js';
import {t} from '../../src/i18n.js';
const out=fileURLToPath(new URL('.',import.meta.url));await mkdir(out,{recursive:true});
const events=sampleEvidence(),base=events[0];let seq=0,planner='ollama',target='left',kind='target',sendObservation=true;
const wss=new WebSocketServer({host:'127.0.0.1',port:0});await once(wss,'listening');
function event(type,data){return {...base,type,seq:++seq,trial_id:null,minute:Math.floor(Date.now()/60000),data};}
function status(){const data={...base.data,state:'running',motor:'not_present'};if(planner!==undefined)data.planner=planner;return event('status',data);}
function recipe(){const r=recipeFor(kind==='counter'?'counter':'red_ball');if(kind==='target'){r.brain={type:'none'};r.actions=[{type:'dashboard'}];}return event('recipe',{origin:'planner',caused_by:null,recipe:r});}
function observation(){const data={...events[2].data,round:null,target:kind==='target'?target:null,occupancy:kind==='counter'?known(0):null,entered:kind==='counter'?known(0):null,exited:kind==='counter'?known(0):null,unknown_reason:target==='unknown'&&kind==='target'?'FRAME_STALE':null};return event('observation',data);}
function send(e){for(const ws of wss.clients)if(ws.readyState===1)ws.send(JSON.stringify(e));}
function update(){send(status());send(recipe());if(sendObservation)send(observation());}
wss.on('connection',ws=>{ws.send(JSON.stringify(status()));ws.send(JSON.stringify(recipe()));if(sendObservation)ws.send(JSON.stringify(observation()));});
const beat=setInterval(()=>{send(status());if(sendObservation)send(observation());},500);
let app,browser;const errors=[],results=[];
async function start(port=0,password=''){app=await createApplication({persist:false,localAccess:true,localRunnerUrl:`ws://127.0.0.1:${wss.address().port}`,retryMs:80,password});app.server.listen(port,'127.0.0.1');await once(app.server,'listening');return app.server.address().port;}
try{
 const port=await start();browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:360,height:800},reducedMotion:'reduce'});page.on('pageerror',error=>errors.push(error.message));
 await page.goto(`http://127.0.0.1:${port}/#live`);await page.waitForSelector('.target-view[data-target="left"]');
 for(const lang of ['uz','ru','en']){
  await page.selectOption('#language',lang);
  for(const [value,label,privacy] of [['rules','planner_rules','plannerLocal'],['ollama','planner_ollama','plannerLocal'],['nebius','planner_nebius','crossBorder'],[null,'plannerUnset','plannerDepends'],[undefined,'plannerNotReported','plannerDepends']]){
   planner=value;update();await page.locator('.planner-report').filter({hasText:t(lang,label)}).waitFor();
   await page.locator('a[href="#setup"]').click();assert.equal(await page.locator('.planner-disclosure').textContent(),t(lang,privacy));
   assert.ok((await page.locator('.planner-report').textContent()).includes(t(lang,label)));
   await page.locator('a[href="#live"]').click();
  }
  results.push(`${lang}: all planner labels and disclosures`);
 }
 planner='ollama';update();await page.selectOption('#language','uz');
 for(const theme of ['dark','light']){
  if(await page.locator('html').getAttribute('data-theme')!==theme)await page.click('#theme');
  for(const state of ['left','center','right','lost','unknown']){
   target=state;update();await page.waitForSelector(`.target-view[data-target="${state}"]`);
   assert.equal(await page.locator('#main-value').textContent(),t('uz',state));
   assert.equal(await page.locator('.counting-line,.entry-arrow,.silhouettes,.crossings').count(),0);
   assert.equal((await page.locator('body').textContent()).includes('Odam sanaladi'),false);
   assert.equal(await page.locator('.target-dot').count(),['left','center','right'].includes(state)?1:0);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   if(state==='left')await page.screenshot({path:`${out}/target-${theme}-360.png`,fullPage:true});
  }
 }
 results.push('360px light/dark: left, center, right, lost, unknown; no counting diagram or overflow');
 target='center';update();await page.locator('a[href="#setup"]').click();await page.fill('#prompt','Eshikdan kirganlarni sana');await page.evaluate(()=>window.retainedTab=42);
 await page.screenshot({path:`${out}/setup-light-360.png`,fullPage:true});
 await app.close();app=null;await page.waitForSelector('[data-action="reload"]');
 sendObservation=false;kind='counter';await start(port);await page.waitForSelector('[data-action="reload"]',{state:'detached'});
 await page.locator('a[href="#live"]').click();await page.waitForSelector('.counting-line',{state:'attached'});assert.equal(await page.locator('#main-value').textContent(),'—');
 sendObservation=true;update();await page.waitForFunction(()=>document.querySelector('#main-value')?.textContent==='0');assert.equal(await page.evaluate(()=>window.retainedTab),42);
 await page.locator('a[href="#setup"]').click();assert.equal(await page.inputValue('#prompt'),'Eshikdan kirganlarni sana');
 results.push('same tab recovered after web restart, kept draft, waited for fresh count, then displayed measured zero');
 await app.close();app=null;await page.waitForSelector('[data-action="reload"]');await start(port,'browser-test-password');
 await page.locator('aside').filter({hasText:t('uz','sessionEnded')}).waitFor();
 await page.locator('aside [data-action="connect"]').click();await page.fill('#owner-password','browser-test-password');await page.locator('#login-form button').click();
 await page.locator('a[href="#live"]').click();await page.waitForFunction(()=>document.querySelector('#main-value')?.textContent==='0');
 results.push('restart with password required sign-in and resumed after login');
 assert.deepEqual(errors,[]);await writeFile(`${out}/browser.json`,JSON.stringify({results,jsErrors:errors},null,2)+'\n');console.log(JSON.stringify({results,jsErrors:errors}));
}finally{clearInterval(beat);await browser?.close();await app?.close();for(const ws of wss.clients)ws.terminate();await new Promise(resolve=>wss.close(resolve));}
