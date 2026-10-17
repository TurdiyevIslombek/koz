import {DynamoDBClient,GetItemCommand,PutItemCommand,DeleteItemCommand,QueryCommand,TransactWriteItemsCommand} from '@aws-sdk/client-dynamodb';
import {ContractError,validateEvent} from '../src/protocol.js';
import {expiry} from '../src/model.js';

// One installed owner and one paired runner. A client can never choose this scope.
const OWNER='OWNER#primary',SOURCE=`${OWNER}#RUNNER#primary`,DAY=86400;
const key=(pk,sk)=>({pk:{S:pk},sk:{S:sk}});
const item=(pk,sk,value,expires)=>({...key(pk,sk),value:{S:JSON.stringify(value)},...(expires?{expires_at:{N:String(expires)}}:{})});
const decode=(row,now)=>row&&(!row.expires_at||Number(row.expires_at.N)>now)?JSON.parse(row.value.S):null;
const validID=v=>typeof v==='string'&&/^[a-f0-9]{32}$/.test(v);
const eventPK=session=>`${SOURCE}#SESSION#${session}`;
const eventSK=seq=>`EVENT#${String(seq).padStart(16,'0')}`;
const seconds=()=>Math.floor(Date.now()/1000);

export function createDynamoStore({table,region,client=new DynamoDBClient({region,maxAttempts:2,requestHandler:{connectionTimeout:1500,requestTimeout:3000}}),now=seconds}={}){
 if(!table||!region)throw Error('KOZ_TABLE and AWS_REGION are required');
 const send=command=>client.send(command),get=async(pk,sk)=>decode((await send(new GetItemCommand({TableName:table,Key:key(pk,sk),ConsistentRead:true}))).Item,now());
 const put=(pk,sk,value,expires)=>({TableName:table,Item:item(pk,sk,value,expires)});
 const query=async(pk,prefix,{limit=100,cursor=null}={})=>{
  if(!Number.isInteger(limit)||limit<1||limit>200)throw new ContractError('INVALID_COMMAND');
  let start;
  if(cursor){try{if(cursor.length>1024)throw Error();start=JSON.parse(Buffer.from(cursor,'base64url'));if(start.pk?.S!==pk||!start.sk?.S?.startsWith(prefix)||Object.keys(start).sort().join(',')!=='pk,sk')throw Error();}catch{throw new ContractError('INVALID_COMMAND');}}
  const result=await send(new QueryCommand({TableName:table,KeyConditionExpression:'pk = :pk AND begins_with(sk, :prefix)',
   FilterExpression:'attribute_not_exists(expires_at) OR expires_at > :now',ExpressionAttributeValues:{':pk':{S:pk},':prefix':{S:prefix},':now':{N:String(now())}},
   ScanIndexForward:false,ConsistentRead:true,Limit:limit,...(start?{ExclusiveStartKey:start}:{})}));
  return {rows:(result.Items||[]).map(row=>decode(row,now())).filter(Boolean),nextCursor:result.LastEvaluatedKey?Buffer.from(JSON.stringify(result.LastEvaluatedKey)).toString('base64url'):null};
 };
 let latestStatus=null;
 const history=async({session=latestStatus?.event.session_id,limit=100,cursor=null}={})=>{
  if(!session)return {rows:[],nextCursor:null};if(!validID(session))throw new ContractError('INVALID_COMMAND');
  return {...await query(eventPK(session),'EVENT#',{limit,cursor}),session};
 };
 const totals=async({date=new Date(now()*1000).toISOString().slice(0,10),limit=100,cursor=null}={})=>{
  if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||new Date(date).toISOString().slice(0,10)!==date)throw new ContractError('INVALID_COMMAND');
  return query(SOURCE,`TOTAL#${date}#`,{limit,cursor});
 };
 async function load(){
  const [meta,status,recipe,fault,summaries]=await Promise.all([get(OWNER,'META'),get(SOURCE,'STATE#status'),get(SOURCE,'STATE#recipe'),get(SOURCE,'STATE#fault'),query(OWNER,'SUMMARY#')]);
  latestStatus=status;
  const selectedSummaries=await Promise.all((meta?.publication?.summary_ids||[]).filter(id=>!summaries.rows.some(s=>s.trial_id===id)).slice(0,100).map(id=>get(OWNER,`SUMMARY#${id}`)));
  const page=await history({limit:200});
  const rows=new Map([...page.rows,status,recipe,fault].filter(Boolean).map(row=>[`${row.event.session_id}:${row.event.seq}`,row]));
  return {meta:{...meta,saved:[...summaries.rows,...selectedSummaries.filter(Boolean)]},events:[...rows.values()].sort((a,b)=>a.receivedAt-b.receivedAt||a.event.seq-b.event.seq),historyCursor:page.nextCursor,summariesCursor:summaries.nextCursor};
 }
 async function append(input){
  const event=input.event;validateEvent(event,input.receivedAt);
  const expires=Math.floor(expiry(event,input.receivedAt)/1000);if(expires<=now())return false;
  const row={event,receivedAt:Math.floor(input.receivedAt/60000)*60000,expiresAt:expires*1000};
  const writes=[{Put:{...put(eventPK(event.session_id),eventSK(event.seq),row,expires),ConditionExpression:'attribute_not_exists(pk)'}}];
  const freshStatus=event.type==='status'&&(!latestStatus||latestStatus.event.session_id!==event.session_id||event.seq>latestStatus.event.seq);
  if(freshStatus||['recipe','fault'].includes(event.type)){
   const previous=event.type==='status'?latestStatus:await get(SOURCE,`STATE#${event.type}`);
   if(!previous||previous.event.session_id!==event.session_id||event.seq>previous.event.seq)writes.push({Put:put(SOURCE,`STATE#${event.type}`,row,expires)});
  }
  // A transaction makes retrying an event unable to add its crossings twice.
  if(event.job_id&&!event.trial_id&&(event.type==='observation'&&event.data.round===null||freshStatus&&['idle','held','refused'].includes(event.data.state))){
   const counterKey=`COUNTER#${event.session_id}#${event.job_id}`,previous=await get(SOURCE,counterKey);
   const observation=event.type==='observation',data=event.data;
   if((previous||observation&&(data.entered||data.exited))&&(!previous||event.seq>previous.seq)){
    const day=Math.floor(Math.min(event.minute,Math.floor(input.receivedAt/60000))/1440),date=new Date(day*DAY*1000).toISOString().slice(0,10),totalKey=`TOTAL#${date}#${event.session_id}#${event.job_id}`;
    const total=await get(SOURCE,totalKey)||{date,entered:0,exited:0,incomplete:false,open:true};
    const counter=previous||{entered:0,exited:0,known:false,incomplete:false};
    let known=true;
    if(observation){
     for(const field of ['entered','exited']){const count=data[field];if(count?.state==='known'){const high=Math.max(counter[field],count.value);total[field]+=high-counter[field];counter[field]=high;}else if(count!==null)known=false;}
     counter.known=known;counter.incomplete ||= data.coverage==='gapped'||!known;
    }
    counter.incomplete ||= Boolean(input.incomplete);
    // A terminal status alone is not proof of a final count. Require an adjacent known observation.
    total.incomplete ||= counter.incomplete||(!observation&&(!counter.known||event.seq!==counter.seq+1));
    total.open=observation;counter.seq=event.seq;counter.date=date;counter.totalKey=totalKey;
    const totalExpiry=(day+1)*DAY+30*DAY;
    writes.push({Put:put(SOURCE,counterKey,counter,totalExpiry)},{Put:put(SOURCE,totalKey,total,totalExpiry)});
   }
  }
  try{await send(new TransactWriteItemsCommand({TransactItems:writes}));}
  catch(error){if(error.name==='TransactionCanceledException'&&error.CancellationReasons?.[0]?.Code==='ConditionalCheckFailed')return false;throw error;}
  if(freshStatus)latestStatus=row;
  return true;
 }
 async function disconnected(){
  const event=latestStatus?.event;if(!event?.job_id||event.trial_id)return;
  const sk=`COUNTER#${event.session_id}#${event.job_id}`,counter=await get(SOURCE,sk);if(!counter)return;
  const total=await get(SOURCE,counter.totalKey);if(!total||!total.open)return;
  counter.incomplete=true;total.incomplete=true;
  const expires=(Math.floor(Date.parse(counter.date)/1000/DAY)+1)*DAY+30*DAY;
  await send(new TransactWriteItemsCommand({TransactItems:[{Put:put(SOURCE,sk,counter,expires)},{Put:put(SOURCE,counter.totalKey,total,expires)}]}));
 }
 return {kind:'dynamodb',load,append,history,totals,disconnected,
  saveMeta:meta=>send(new PutItemCommand(put(OWNER,'META',meta))),
  summaries:options=>query(OWNER,'SUMMARY#',options),
  saveSummary:async summary=>{try{await send(new PutItemCommand({...put(OWNER,`SUMMARY#${summary.trial_id}`,summary),ConditionExpression:'attribute_not_exists(pk)'}));}catch(error){if(error.name!=='ConditionalCheckFailedException')throw error;}},
  deleteSummary:trial=>send(new DeleteItemCommand({TableName:table,Key:key(OWNER,`SUMMARY#${trial}`)})),
  close:()=>client.destroy?.()
 };
}
