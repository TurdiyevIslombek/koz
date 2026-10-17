import assert from 'node:assert/strict';
import http from 'node:http';
import https from 'node:https';
import {once} from 'node:events';
import {mkdtemp,readFile,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {WebSocket} from 'ws';
import {createCloudApplication} from '../../server/cloud.mjs';
import {createDynamoStore} from '../../server/dynamo.mjs';
import {FakeDynamo} from '../../test/fake-dynamo.mjs';
import {sampleEvidence,recipeFor} from '../../src/demo.js';
const {chromium}=await import(process.env.KOZ_PLAYWRIGHT_MODULE||'playwright');
const out=fileURLToPath(new URL('.',import.meta.url)),temporary=await mkdtemp(join(tmpdir(),'koz-cloud-browser-'));
execFileSync('openssl',['req','-x509','-newkey','rsa:2048','-nodes','-keyout',join(temporary,'key.pem'),'-out',join(temporary,'cert.pem'),'-days','1','-subj','/CN=localhost'],{stdio:'ignore'});
let app,browser,ws,seq=0,job=null,privacy='approved',state='idle';const client=new FakeDynamo(),errors=[];
const proxy=https.createServer({key:await readFile(join(temporary,'key.pem')),cert:await readFile(join(temporary,'cert.pem'))},(req,res)=>{
 const forward=http.request({host:'127.0.0.1',port:app.server.address().port,path:req.url,method:req.method,headers:{...req.headers,'x-forwarded-proto':'https'}},response=>{res.writeHead(response.statusCode,response.headers);response.pipe(res);});
 forward.on('error',()=>res.destroy());req.pipe(forward);res.on('close',()=>forward.destroy());
});
await new Promise(resolve=>proxy.listen(0,'127.0.0.1',resolve));const origin=`https://127.0.0.1:${proxy.address().port}`,password='offline-browser-test-password';
async function start(){app=await createCloudApplication({KOZ_OWNER_PASSWORD:password,KOZ_PUBLIC_ORIGIN:origin,KOZ_TABLE:'koz-web',AWS_REGION:'eu-central-1'},{storage:createDynamoStore({table:'koz-web',region:'eu-central-1',client})});app.server.listen(0,'127.0.0.1');await once(app.server,'listening');}
const base=sampleEvidence()[0],emit=(type,data)=>ws?.readyState===1&&ws.send(JSON.stringify({...base,seq:++seq,type,job_id:job,trial_id:null,revision:job?1:null,minute:Math.floor(Date.now()/60000),data}));
const status=()=>emit('status',{...base.data,state,privacy,planner:'bedrock',cameras:['mac_camera','esp32_cam']});
let beat;
try{
 await start();browser=await chromium.launch({headless:true});const owner=await browser.newContext({viewport:{width:360,height:800},ignoreHTTPSErrors:true});const judge=await browser.newContext({viewport:{width:360,height:800},ignoreHTTPSErrors:true});const page=await owner.newPage(),viewer=await judge.newPage();for(const p of [page,viewer])p.on('pageerror',e=>errors.push(e.message));
 await page.goto(origin);await page.selectOption('#language','en');await page.click('[data-action="connect"]');await page.fill('#owner-password',password);await page.locator('#login-form button').click();await page.locator('#connection').waitFor({state:'hidden'});
 await page.click('[data-action="connect"]');await page.click('[data-action="token"]');const token=await page.locator('.token-value').innerText();await page.click('[data-action="close-dialog"]');
 ws=new WebSocket(`ws://127.0.0.1:${app.server.address().port}/v1/runner`,{headers:{Host:new URL(origin).host,'X-Forwarded-Proto':'https',Authorization:`Bearer ${token}`}});await once(ws,'open');status();beat=setInterval(status,500);
 await page.locator('a[href="#setup"]').click();await page.locator('#camera-choice').waitFor();
 for(const lang of ['uz','ru','en']){await page.selectOption('#language',lang);assert.match(await page.locator('.planner-disclosure').innerText(),/AWS/);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
 assert.equal(await page.locator('.planner-disclosure').innerText(),'The text passes through AWS Frankfurt; with the Bedrock planner it is processed in AWS EU Regions; it is not stored.');
 for(const theme of ['light','dark']){if(await page.locator('html').getAttribute('data-theme')!==theme)await page.click('#theme');await page.screenshot({path:join(out,`setup-${theme}-360.png`),fullPage:true});}
 await viewer.goto(origin);await viewer.selectOption('#language','en');await viewer.getByText('The owner has not shared a demonstration yet.').waitFor();assert.equal(await viewer.locator('a[href="#setup"], [data-action="stop"]').count(),0);
 await page.selectOption('#camera-choice','esp32_cam');await page.fill('#prompt','Find the red ball');const command=once(ws,'message');await page.click('#test');const received=JSON.parse((await command)[0]);assert.equal(received.data.camera_id,'esp32_cam');job=received.job_id;state='running';status();emit('recipe',{origin:'planner',caused_by:null,recipe:recipeFor('red_ball')});const observation=sampleEvidence().find(e=>e.type==='observation').data;emit('observation',{...observation,round:null,target:'left'});
 await page.click('[data-action="connect"]');await page.click('[data-action="publish"]');await page.locator('[data-action="unpublish"]').waitFor();await page.click('[data-action="close-dialog"]');
 await viewer.locator('#main-value').filter({hasText:'Left'}).waitFor();await viewer.screenshot({path:join(out,'judges-live-360.png'),fullPage:true});assert.equal(await viewer.locator('[data-action="stop"]').count(),0);
 await viewer.locator('a[href="#trials"]').click();assert.equal(await viewer.locator('[data-action="begin-trial"], [data-action^="save:"], [data-action^="delete:"]').count(),0);
 await viewer.locator('a[href="#live"]').click();state='held';privacy='blocked';status();emit('fault',{code:'PRIVATE_BATHROOM',effect:'held'});await viewer.locator('#status-reason').filter({hasText:'bathroom'}).waitFor();assert.notEqual(await viewer.locator('#main-value').innerText(),'Left');
 clearInterval(beat);ws.close();await once(ws,'close');await viewer.locator('#status-reason').filter({hasText:'Offline'}).waitFor();await app.close();await start();await viewer.locator('#main-value').filter({hasText:'Unknown'}).waitFor();
 // Both tabs reconnect anonymously after a restart; owner controls require a fresh login.
 await page.getByText('Judges · read only').first().waitFor();assert.equal(await page.locator('[data-action="stop"]').count(),0);
 assert.deepEqual(errors,[]);const result={passed:['cloud Setup disclosure in Uz/Ru/En at 360px','light/dark themes','Secure owner login through HTTPS proxy','Bedrock and camera selection on the wire','unpublished default','public job selection','judge controls absent','privacy stop and disconnect clear target','same tabs recover after web restart'],jsErrors:errors};await writeFile(join(out,'browser.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{clearInterval(beat);ws?.terminate();await browser?.close();if(app?.server.listening)await app.close();await new Promise(resolve=>proxy.close(resolve));await rm(temporary,{recursive:true,force:true});}
