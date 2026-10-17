import {isAbsolute,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createApplication} from './index.mjs';
import {createDynamoStore} from './dynamo.mjs';
import {normalizeOrigin} from './security.mjs';

export async function createCloudApplication(env=process.env,{storage}={}){
 let password=env.KOZ_OWNER_PASSWORD;
 delete env.KOZ_OWNER_PASSWORD;
 try{
  if(typeof password!=='string'||password.length<16||password.length>256)throw Error('Cloud owner password must contain 16–256 characters');
  const publicOrigin=normalizeOrigin(env.KOZ_PUBLIC_ORIGIN).origin;
  const port=Number(env.PORT||4173);
  if(!Number.isInteger(port)||port<1||port>65535)throw Error('Invalid PORT');
  const dataDir=env.KOZ_DATA_DIR||'/var/lib/koz';if(!isAbsolute(dataDir))throw Error('KOZ_DATA_DIR must be absolute');
  if(env.AWS_REGION!=='eu-central-1'||!/^[-A-Za-z0-9_.]{3,255}$/.test(env.KOZ_TABLE||''))throw Error('KOZ_TABLE and AWS_REGION=eu-central-1 are required');
  const store=storage||createDynamoStore({table:env.KOZ_TABLE,region:env.AWS_REGION});
  try{return {...await createApplication({password,dataDir,storage:store,publicOrigin,localAccess:false,localRunnerUrl:null}),port};}
  catch(error){store.close?.();throw error;}
 }finally{password=undefined;}
}

if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href){
 try{
  const app=await createCloudApplication();
  app.server.listen(app.port,'127.0.0.1',()=>console.log('Koʻz cloud web ready (DynamoDB).'));
  app.server.on('error',()=>{console.error('Koʻz cloud web could not listen.');process.exit(1);});
  let closing=false;
  for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{if(closing)return;closing=true;app.close().then(()=>process.exit(0),()=>process.exit(1));});
 }catch{console.error('Koʻz cloud startup failed. Check configuration and table access.');process.exitCode=1;}
}
