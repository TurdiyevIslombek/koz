// An offline implementation of the small low-level DynamoDB API used by our adapter.
// Requests still use the pinned AWS SDK command classes; no AWS credentials/network are used.
export class FakeDynamo {
 rows=new Map();requests=[];
 key(value){return `${value.pk.S}|${value.sk.S}`;}
 async send(command){
  const name=command.constructor.name,input=command.input;this.requests.push({name,input:structuredClone(input)});
  if(this.fail)throw Error('injected storage failure');
  if(name==='GetItemCommand')return {Item:structuredClone(this.rows.get(this.key(input.Key)))};
  if(name==='DeleteItemCommand'){this.rows.delete(this.key(input.Key));return {};}
  if(name==='PutItemCommand'){
   if(input.ConditionExpression&&this.rows.has(this.key(input.Item)))throw Object.assign(Error(),{name:'ConditionalCheckFailedException'});
   this.rows.set(this.key(input.Item),structuredClone(input.Item));return {};
  }
  if(name==='TransactWriteItemsCommand'){
   for(const [index,write]of input.TransactItems.entries())if(write.Put.ConditionExpression&&this.rows.has(this.key(write.Put.Item)))throw Object.assign(Error(),{name:'TransactionCanceledException',CancellationReasons:input.TransactItems.map((_,i)=>({Code:i===index?'ConditionalCheckFailed':'None'}))});
   for(const {Put}of input.TransactItems)this.rows.set(this.key(Put.Item),structuredClone(Put.Item));return {};
  }
  if(name==='QueryCommand'){
   const v=input.ExpressionAttributeValues;
   let rows=[...this.rows.values()].filter(r=>r.pk.S===v[':pk'].S&&r.sk.S.startsWith(v[':prefix'].S)).sort((a,b)=>b.sk.S.localeCompare(a.sk.S));
   if(input.ExclusiveStartKey)rows=rows.filter(r=>r.sk.S<input.ExclusiveStartKey.sk.S);
   const page=rows.slice(0,input.Limit),last=page.at(-1);
   return {Items:structuredClone(page.filter(r=>!r.expires_at||Number(r.expires_at.N)>Number(v[':now'].N))),...(rows.length>page.length?{LastEvaluatedKey:{pk:last.pk,sk:last.sk}}:{})};
  }
  throw Error(`Unexpected SDK command: ${name}`);
 }
 destroy(){}
}
