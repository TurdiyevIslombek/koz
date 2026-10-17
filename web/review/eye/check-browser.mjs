// No screenshots, traces, recordings, frame files or frame-containing result data.
import assert from 'node:assert/strict';
import http from 'node:http';
import {once} from 'node:events';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {writeFile} from 'node:fs/promises';
import {WebSocketServer} from 'ws';
import {createApplication} from '../../server/index.mjs';
import {sampleEvidence,recipeFor} from '../../src/demo.js';
import {eyeClosed} from '../../src/eye-protocol.js';
import {t} from '../../src/i18n.js';
import {codeMessage} from '../../src/protocol.js';

const {chromium}=await import(process.env.KOZ_PLAYWRIGHT_MODULE||'playwright');
const python=fileURLToPath(new URL('../../../.venv/bin/python',import.meta.url));
const frame=execFileSync(python,['-c',"import cv2,numpy as np,sys; image=np.full((180,320,3),110,np.uint8); cv2.circle(image,(160,90),30,(0,0,220),-1); sys.stdout.buffer.write(cv2.imencode('.jpg',image)[1].tobytes())"]);
const upstream=http.createServer(),wss=new WebSocketServer({server:upstream,perMessageDeflate:false});
let eventSocket,previewSocket,seq=0,job='a'.repeat(32),state='running',privacy='approved',sending=true,app,browser,beat,pump;
let reason='checking';const base=sampleEvidence()[0],errors=[],requests=[];
const emit=(type,data)=>eventSocket?.readyState===1&&eventSocket.send(JSON.stringify({...base,seq:++seq,type,job_id:job,trial_id:null,revision:1,minute:Math.floor(Date.now()/60000),data}));
const status=()=>emit('status',{...base.data,state,privacy,camera_on:['running','checking'].includes(state),planner:'rules'});
function initialise(){status();emit('recipe',{origin:'import',caused_by:null,recipe:recipeFor('red_ball')});emit('observation',{...sampleEvidence().find(e=>e.type==='observation').data,round:null,target:'left'});}
wss.on('connection',(ws,req)=>{if(req.url==='/v1/preview'){previewSocket=ws;if(!sending)ws.send(JSON.stringify(eyeClosed(reason)));}else{eventSocket=ws;initialise();}});
await new Promise(resolve=>upstream.listen(0,'127.0.0.1',resolve));
async function start(port=0){app=await createApplication({localAccess:true,persist:false,localRunnerUrl:`ws://127.0.0.1:${upstream.address().port}`,retryMs:30});app.server.listen(port,'127.0.0.1');await once(app.server,'listening');}
async function closed(page,text){await page.waitForFunction(()=>document.querySelector('#eye-picture')?.getAttribute('src')===null);await page.locator('#eye-reason').filter({hasText:text}).waitFor();assert.equal(await page.locator('#live-eye').getAttribute('class'),'scene-frame live-eye is-closed');}
async function opened(page){await page.waitForFunction(()=>{const img=document.querySelector('#eye-picture');return img&&!img.hidden&&img.complete&&img.naturalWidth===320;});}
try{
 await start();const port=app.server.address().port,origin=`http://127.0.0.1:${port}`;
 beat=setInterval(status,450);pump=setInterval(()=>{if(sending&&previewSocket?.readyState===1)previewSocket.send(frame);},220);
 browser=await chromium.launch({headless:true});const context=await browser.newContext({viewport:{width:360,height:800}}),page=await context.newPage();
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(new URL(r.url()).pathname));
 await page.goto(origin+'/#live');await opened(page);
 for(const language of ['uz','ru','en']){
  await page.selectOption('#language',language);await opened(page);
  assert.equal(await page.locator('.eye-label').innerText(),t(language,'eyeLocal'));
  for(const theme of ['light','dark']){
   if(await page.locator('html').getAttribute('data-theme')!==theme)await page.click('#theme');
   await opened(page);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
   const geometry=await page.locator('#eye-picture').evaluate(img=>{const a=img.getBoundingClientRect(),b=img.parentElement.getBoundingClientRect();return {fits:a.left>=b.left&&a.right<=b.right&&a.top>=b.top&&a.bottom<=b.bottom};});assert.ok(geometry.fits);
  }
  sending=false;reason='checking';previewSocket.send(JSON.stringify(eyeClosed(reason)));await closed(page,t(language,'eyeChecking'));
  sending=true;await opened(page);sending=false;await closed(page,t(language,'eyeLate'));
  sending=true;await opened(page);sending=false;reason='not_running';previewSocket.send(JSON.stringify(eyeClosed(reason)));state='held';privacy='blocked';status();emit('fault',{code:'PRIVATE_BATHROOM',effect:'held'});
  await closed(page,codeMessage('PRIVATE_BATHROOM',language));assert.equal(await page.locator('#main-value').innerText(),t(language,'unknown'));
  job=(Number.parseInt(job[0],16)+1).toString(16).repeat(32);state='running';privacy='approved';initialise();sending=true;await opened(page);
 }
 await page.emulateMedia({reducedMotion:'reduce'});assert.equal(await page.locator('.eye-lid').evaluate(el=>getComputedStyle(el).transitionDuration),'0s');
 sending=false;reason='not_fresh';previewSocket.terminate();await closed(page,t('en','eyeLate'));sending=true;await opened(page);
 // Event transport loss closes the image even if preview JPEGs still arrive.
 clearInterval(beat);eventSocket.terminate();sending=false;reason='not_fresh';await closed(page,t('en','offlineReason'));
 beat=setInterval(status,450);sending=true;await opened(page);
 // Same tab: the web restart revokes its session, discards the image, then renews locally.
 await app.close();await closed(page,t('en','offlineReason'));await start(port);await opened(page);
 await page.locator('a[href="#setup"]').click();assert.equal(await page.locator('#eye-picture').count(),0);await page.locator('a[href="#live"]').click();await opened(page);
 assert.deepEqual(errors,[]);assert.ok(!requests.some(p=>/\.jpe?g$|snapshot-image|recording/.test(p)));
 const result={passed:['360px Uzbek/Russian/English and both themes','in-memory JPEG decoded inside eye without cropping','checking and one-second stale reason clear image','fixed bathroom refusal closes eye and keeps Unknown','reduced motion','preview/event disconnect recovery','same-tab local web restart','navigation releases preview'],jsErrors:errors,mediaArtifactsSaved:false,hardwareUsed:false};
 await writeFile(new URL('browser.json',import.meta.url),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{clearInterval(beat);clearInterval(pump);await browser?.close();if(app?.server.listening)await app.close();for(const ws of wss.clients)ws.terminate();await new Promise(r=>wss.close(r));await new Promise(r=>upstream.close(r));}
