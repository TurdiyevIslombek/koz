import assert from 'node:assert/strict';
import {once} from 'node:events';
import {writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {WebSocketServer} from 'ws';
import {createApplication} from '../../server/index.mjs';
import {sampleEvidence,recipeFor} from '../../src/demo.js';
import {t} from '../../src/i18n.js';
import {codeMessage} from '../../src/protocol.js';
const {chromium}=await import(process.env.KOZ_PLAYWRIGHT_MODULE||'playwright');
const out=fileURLToPath(new URL('.',import.meta.url));
const base=sampleEvidence()[0],commands=[],errors=[];let seq=0,cameras=['mac_camera','esp32_cam','phone_ip_camera'];
const wss=new WebSocketServer({port:0,host:'127.0.0.1'});await once(wss,'listening');
const emit=(type,data)=>{const e={...base,job_id:null,trial_id:null,revision:null,type,seq:++seq,data};for(const ws of wss.clients)if(ws.readyState===1)ws.send(JSON.stringify(e));};
const status=()=>emit('status',{...base.data,state:'idle',...(cameras===undefined?{}:{cameras})});
wss.on('connection',ws=>{status();ws.on('message',raw=>{const c=JSON.parse(raw);if(c.type!=='command'){errors.push(`Unexpected runner message: ${c.type}`);return;}commands.push(c);setTimeout(()=>emit('command_result',{command_id:c.command_id,result:'rejected',code:'UNSUPPORTED_CAPABILITY'}),50);});});
const beat=setInterval(status,500);
let browser;const app=await createApplication({persist:false,localAccess:true,localRunnerUrl:`ws://127.0.0.1:${wss.address().port}`});
try{
 app.server.listen(0,'127.0.0.1');await once(app.server,'listening');browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:360,height:800}});page.on('pageerror',error=>errors.push(error.message));
 await page.goto(`http://127.0.0.1:${app.server.address().port}/#setup`);await page.waitForSelector('#camera-choice');assert.equal(await page.inputValue('#camera-choice'),'mac_camera');
 for(const lang of ['uz','ru','en']){await page.selectOption('#language',lang);assert.deepEqual(await page.locator('#camera-choice option').allTextContents(),cameras.map(slot=>t(lang,slot)));assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);}
 await page.selectOption('#language','uz');await page.selectOption('#camera-choice','esp32_cam');
 for(const theme of ['light','dark']){if(await page.locator('html').getAttribute('data-theme')!==theme)await page.click('#theme');await page.screenshot({path:`${out}/setup-${theme}-360.png`,fullPage:true});}
 await page.fill('#prompt','Qizil koptokni kuzat');await page.click('#test');await page.locator('[role="alert"]').filter({hasText:codeMessage('UNSUPPORTED_CAPABILITY','uz')}).waitFor();assert.equal(commands.at(-1).data.camera_id,'esp32_cam');assert.equal(commands.at(-1).data.input,'prompt');
 await page.locator('a[href="#setup"]').click();assert.equal(await page.inputValue('#camera-choice'),'esp32_cam');
 await page.locator('#recipe-file').setInputFiles({name:'recipe.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(recipeFor('red_ball')))});await page.click('#test');await page.locator('[role="alert"]').filter({hasText:codeMessage('UNSUPPORTED_CAPABILITY','uz')}).waitFor();assert.equal(commands.at(-1).data.camera_id,'esp32_cam');assert.equal(commands.at(-1).data.input,'recipe');assert.equal('camera_id' in commands.at(-1).data.recipe.camera,false);
 await page.locator('a[href="#setup"]').click();base.session_id='f'.repeat(32);for(const ws of wss.clients)ws.terminate();await page.waitForFunction(()=>document.querySelector('#camera-choice')?.value==='mac_camera');
 cameras=['phone_ip_camera'];status();await page.waitForSelector('#camera-choice',{state:'detached'});await page.fill('#prompt','Sana');await page.click('#test');await page.locator('[role="alert"]').filter({hasText:codeMessage('UNSUPPORTED_CAPABILITY','uz')}).waitFor();assert.equal(commands.at(-1).data.camera_id,'phone_ip_camera');
 for(const value of [[],undefined]){await page.locator('a[href="#setup"]').click();cameras=value;status();await page.waitForTimeout(100);assert.equal(await page.locator('#camera-choice').count(),0);await page.fill('#prompt','Sana');await page.click('#test');await page.locator('[role="alert"]').filter({hasText:codeMessage('UNSUPPORTED_CAPABILITY','uz')}).waitFor();assert.equal('camera_id' in commands.at(-1).data,false);}
 assert.deepEqual(errors,[]);const result={passed:['three-language fixed labels at 360px','light and dark themes','prompt and imported recipe preserve selected camera_id','new session resets to first slot','one slot is sent without a selector','empty and legacy status omit camera_id','runner rejection uses fixed message'],commands:commands.map(c=>({input:c.data.input,camera_id:c.data.camera_id??null})),jsErrors:errors};await writeFile(`${out}/browser.json`,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{clearInterval(beat);await browser?.close();await app.close();for(const ws of wss.clients)ws.terminate();await new Promise(resolve=>wss.close(resolve));}
