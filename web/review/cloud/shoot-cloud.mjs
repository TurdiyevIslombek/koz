// Every screen of the cloud web app, for design review (Oct 22): the owner's screens (login, Connect
// device in each state, Set up a job, Live job states, Trials) and the judges' view, in Uzbek, Russian
// and English, at 360 px and 1280 px, dark theme (plus light for the main screens). Local only: the real
// cloud server code with a fake DynamoDB, a local HTTPS proxy and a fake device that sends contract
// events (numbers only; no camera exists here). Also records horizontal overflow and clipped text.
//   KOZ_PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node web/review/cloud/shoot-cloud.mjs OUT_DIR
import http from 'node:http';
import https from 'node:https';
import {once} from 'node:events';
import {mkdir,mkdtemp,readFile,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import {randomBytes} from 'node:crypto';
import {WebSocket} from 'ws';
import {createCloudApplication} from '../../server/cloud.mjs';
import {createDynamoStore} from '../../server/dynamo.mjs';
import {FakeDynamo} from '../../test/fake-dynamo.mjs';
import {sampleEvidence,recipeFor,known,unknown} from '../../src/demo.js';
const {chromium}=await import(process.env.KOZ_PLAYWRIGHT_MODULE||'playwright');
const out=process.argv[2];if(!out)throw Error('usage: shoot-cloud.mjs OUT_DIR');await mkdir(out,{recursive:true});
const temporary=await mkdtemp(join(tmpdir(),'koz-shoot-cloud-'));
execFileSync('openssl',['req','-x509','-newkey','rsa:2048','-nodes','-keyout',join(temporary,'key.pem'),'-out',join(temporary,'cert.pem'),'-days','1','-subj','/CN=localhost'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let session=randomBytes(16).toString('hex'),app,browser,ws,seq=0,job=null,trial=null,state='idle',privacy='approved',revision=null,beat;const client=new FakeDynamo(),shots=[],problems=[],errors=[];
const proxy=https.createServer({key:await readFile(join(temporary,'key.pem')),cert:await readFile(join(temporary,'cert.pem'))},(req,res)=>{
 const forward=http.request({host:'127.0.0.1',port:app.server.address().port,path:req.url,method:req.method,headers:{...req.headers,'x-forwarded-proto':'https'}},response=>{res.writeHead(response.statusCode,response.headers);response.pipe(res);});
 forward.on('error',()=>res.destroy());req.pipe(forward);res.on('close',()=>forward.destroy());
});
await new Promise(resolve=>proxy.listen(0,'127.0.0.1',resolve));const origin=`https://127.0.0.1:${proxy.address().port}`,password='offline-shoot-password';
app=await createCloudApplication({KOZ_OWNER_PASSWORD:password,KOZ_PUBLIC_ORIGIN:origin,KOZ_TABLE:'koz-web',AWS_REGION:'ap-southeast-2'},{storage:createDynamoStore({table:'koz-web',region:'ap-southeast-2',client})});app.server.listen(0,'127.0.0.1');await once(app.server,'listening');
const base=sampleEvidence()[0],observation=sampleEvidence().find(e=>e.type==='observation').data;
const emit=(type,data,extra={})=>ws?.readyState===1&&ws.send(JSON.stringify({...base,session_id:session,seq:++seq,type,job_id:job,trial_id:trial,revision,minute:Math.floor(Date.now()/60000),data,...extra}));
const status=()=>emit('status',{...base.data,state,privacy,camera_on:['running','evaluating','checking'].includes(state),planner:'rules',cameras:['mac_camera']});
async function shoot(page,name,{langs=['uz','ru','en'],themes=['dark'],full=true,prepare=null}={}){
 for(const theme of themes){if(await page.locator('html').getAttribute('data-theme')!==theme)await page.evaluate(()=>document.querySelector('#theme').click());   // works under an open dialog
  for(const lang of langs){await page.evaluate(l=>{const s=document.querySelector('#language');s.value=l;s.dispatchEvent(new Event('change',{bubbles:true}));},lang);await sleep(350);if(prepare){await page.evaluate(()=>document.querySelector('#connection')?.close());await prepare();await sleep(300);}
   const width=page.viewportSize().width,file=`${name}-${lang}-${theme}-${width}.png`;await page.screenshot({path:join(out,file),fullPage:full});shots.push({name,lang,theme,width,file});
   const found=await page.evaluate(()=>{const issues=[];if(document.documentElement.scrollWidth>innerWidth+1)issues.push(`page scrolls sideways (${document.documentElement.scrollWidth} > ${innerWidth})`);
    for(const el of document.querySelectorAll('button,a,h1,h2,h3,p,span,small,strong,label,code,summary,li,dt,dd')){const s=getComputedStyle(el);if(!el.offsetParent&&s.position!=='fixed')continue;
     if(el.scrollWidth>el.clientWidth+2&&['hidden','clip'].includes(s.overflowX))issues.push(`clipped: <${el.tagName.toLowerCase()}> "${el.textContent.trim().slice(0,50)}"`);
     const r=el.getBoundingClientRect();if(r.right>innerWidth+1&&r.width>0)issues.push(`past the edge: <${el.tagName.toLowerCase()}> "${el.textContent.trim().slice(0,50)}"`);}
    const dock=document.querySelector('.dock');if(dock){const top=dock.getBoundingClientRect().top;for(const el of document.querySelectorAll('main p, main small')){const r=el.getBoundingClientRect();if(r.bottom>top&&r.top<top&&window.scrollY+innerHeight>=document.documentElement.scrollHeight-2)issues.push(`under the bottom bar at the end of the page: "${el.textContent.trim().slice(0,50)}"`);}}
    return [...new Set(issues)];});
   for(const issue of found)problems.push({screen:name,lang,width,issue});}}
}
try{
 browser=await chromium.launch({headless:true});
 for(const [width,height] of [[360,800],[1280,800]]){
  session=randomBytes(16).toString('hex');seq=0;job=null;trial=null;state='idle';   // a new device session per pass
 privacy='approved';revision=null;
  const owner=await browser.newContext({viewport:{width,height},ignoreHTTPSErrors:true}),judge=await browser.newContext({viewport:{width,height},ignoreHTTPSErrors:true});
  const page=await owner.newPage(),viewer=await judge.newPage();for(const p of [page,viewer])p.on('pageerror',e=>errors.push(e.message));
  const open=(...then)=>async()=>{await page.click('[data-action="connect"]');for(const action of then)await page.click(`[data-action="${action}"]`);};   // a window opens after the language is set, as for a person
  await page.goto(origin+'/#setup');await shoot(page,'01-login',{full:false,prepare:open()});
  await page.fill('#owner-password',password);await page.locator('#login-form button').click();await page.locator('#connection').waitFor({state:'hidden'});
  await shoot(page,'02-device-not-connected',{full:false,prepare:open()});
  await shoot(page,'03-device-token-shown',{full:false,prepare:open('token')});const token=await page.locator('.token-value').innerText();await page.click('[data-action="close-dialog"]');
  ws=new WebSocket(`ws://127.0.0.1:${app.server.address().port}/v1/runner`,{headers:{Host:new URL(origin).host,'X-Forwarded-Proto':'https',Authorization:`Bearer ${token}`}});await once(ws,'open');status();beat=setInterval(status,500);
  ws.on('message',data=>{const m=JSON.parse(data);if(m.type==='command'){emit('command_result',{command_id:m.command_id,result:'accepted',code:null});if(m.command==='start_job'){job=m.job_id;trial=m.trial_id;revision=1;state='running';status();}}});
  await sleep(1200);await shoot(page,'04-device-connected',{full:false,prepare:open()});
  await shoot(page,'05-device-replace-warning',{full:false,prepare:open('token-ask')});await page.click('[data-action="token-cancel"]');await page.click('[data-action="close-dialog"]');
  await page.locator('.tabs a[href="#setup"]').click();await sleep(800);await shoot(page,'06-setup-empty',{themes:['dark','light']});
  await page.fill('#prompt',"Do'konga kirgan odamlarni sana");await sleep(200);await shoot(page,'07-setup-typed');
  await page.click('#test');for(let i=0;i<40&&!job;i++)await sleep(100);
  emit('recipe',{origin:'planner',caused_by:null,recipe:recipeFor('classroom')});state='evaluating';status();await sleep(900);await shoot(page,'08-live-testing');
  state='running';status();emit('observation',{...observation,round:null,target:null,occupancy:known(1),entered:known(2),exited:known(3)});await sleep(900);await shoot(page,'09-live-running-counter',{themes:['dark','light']});
  emit('observation',{...observation,round:null,target:null,occupancy:unknown('OVERLOADED'),entered:unknown('OVERLOADED'),exited:unknown('OVERLOADED'),unknown_reason:'OVERLOADED'});await sleep(900);await shoot(page,'10-live-unknown');
  state='held';privacy='blocked';status();emit('fault',{code:'PRIVATE_BEDROOM',effect:'held',seen:'bed'});await sleep(900);await shoot(page,'11-live-privacy-stop');
  await page.locator('.tabs a[href="#trials"]').click();await sleep(900);await shoot(page,'12-trials');
  await viewer.goto(origin+'/#live');await sleep(1200);await shoot(viewer,'13-judges-not-shared');
  state='idle';privacy='approved';job=null;revision=null;status();await page.locator('.tabs a[href="#setup"]').click();await sleep(600);await page.fill('#prompt','Find the red ball');await page.click('#test');for(let i=0;i<40&&!job;i++)await sleep(100);
  emit('recipe',{origin:'planner',caused_by:null,recipe:recipeFor('red_ball')});state='running';status();emit('observation',{...observation,round:null,target:'left'});
  await page.click('[data-action="connect"]');await page.click('[data-action="publish"]');await page.locator('[data-action="unpublish"]').waitFor();await page.click('[data-action="close-dialog"]');
  await viewer.goto(origin+'/#live');await sleep(1500);await shoot(viewer,'14-judges-live-target');
  clearInterval(beat);ws.close();await once(ws,'close');await sleep(4200);await page.locator('.tabs a[href="#live"]').click();await sleep(1200);await shoot(page,'15-live-offline');
  await page.click('[data-action="connect"]');await page.click('[data-action="unpublish"]').catch(()=>{});await owner.close();await judge.close();
 }
 await writeFile(join(out,'shots.json'),JSON.stringify(shots,null,1));await writeFile(join(out,'problems.json'),JSON.stringify(problems,null,1));
 console.log(JSON.stringify({shots:shots.length,problems:problems.length,jsErrors:errors},null,1));
 for(const p of problems)console.log(`${p.screen} ${p.lang} ${p.width}: ${p.issue}`);
}finally{clearInterval(beat);ws?.terminate();await browser?.close();if(app?.server.listening)await app.close();await new Promise(resolve=>proxy.close(resolve));await rm(temporary,{recursive:true,force:true});}
