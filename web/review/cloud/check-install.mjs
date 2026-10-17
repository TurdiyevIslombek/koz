import assert from 'node:assert/strict';
import {mkdtemp,cp,mkdir,readFile,rm,access,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const source=fileURLToPath(new URL('../../',import.meta.url)),out=fileURLToPath(new URL('.',import.meta.url));
const dir=await mkdtemp(join(tmpdir(),'koz-install-check-')),web=join(dir,'web'),linux=join(dir,'linux');
const run=(cmd,args,cwd)=>execFileSync(cmd,args,{cwd,stdio:'pipe',timeout:120000});
try{
 await mkdir(web);for(const name of ['package.json','package-lock.json','index.html','scripts','src','server'])await cp(join(source,name),join(web,name),{recursive:true});
 await cp(join(source,'design/assets'),join(web,'design/assets'),{recursive:true});await cp(join(source,'../contracts'),join(dir,'contracts'),{recursive:true});
 run('npm',['ci','--no-audit','--no-fund'],web);run('node',['scripts/build.mjs'],web);run('npm',['prune','--omit=dev','--no-audit','--no-fund'],web);
 await assert.rejects(access(join(web,'node_modules/esbuild')));
 run('node',['--input-type=module','-e',"await import('./server/cloud.mjs'); await import('./src/protocol.js'); console.log('production imports OK')"],web);
 await mkdir(linux);for(const name of ['package.json','package-lock.json'])await cp(join(source,name),join(linux,name));
 run('npm',['ci','--os=linux','--cpu=x64','--ignore-scripts','--no-audit','--no-fund'],linux);
 const elf=await readFile(join(linux,'node_modules/@esbuild/linux-x64/bin/esbuild'));assert.deepEqual([...elf.subarray(0,4)],[127,69,76,70]);
 const result={nativePlatform:process.platform,node:process.version,passed:['clean npm ci -> build -> prune --omit=dev','cloud and protocol imports after removing dev dependencies','Linux x64 optional esbuild package resolves from lockfile and contains an ELF executable'],limit:'Linux execution and an AWS deployment were not performed on this macOS host.'};
 await writeFile(join(out,'install.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{await rm(dir,{recursive:true,force:true});}
