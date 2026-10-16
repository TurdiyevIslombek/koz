// Re-check the owner session before reconnecting: a web restart loses its cookies' sessions.
// Requests and streams from an earlier attempt cannot overwrite a newer snapshot or demo.
export function createOwnerConnection({api,onSession,onSnapshot,onPacket,onDisconnect,onSignedOut,onInvalidPacket,EventSource=globalThis.EventSource,retryMs=1000}) {
 let generation=0,stream=null,timer=null;
 function stop(){generation++;clearTimeout(timer);timer=null;stream?.close();stream=null;}
 function retry(attempt){
  if(attempt!==generation)return;
  stop();onDisconnect();timer=setTimeout(connect,retryMs);
 }
 async function connect(){
  stop();const attempt=generation;
  try{
   const session=await api('session');if(attempt!==generation)return;
   onSession(session);
   if(!session.authenticated){onSignedOut();return;}
   const snapshot=await api('snapshot');if(attempt!==generation)return;
   onSnapshot(snapshot);
   stream=new EventSource('/api/events');
   stream.onmessage=e=>{
    if(attempt!==generation)return;
    let packet;try{packet=JSON.parse(e.data);if(!packet||typeof packet!=='object'||Array.isArray(packet))throw Error();}catch{onInvalidPacket();return;}
    if(packet.reset){connect();return;}
    onPacket(packet);
   };
   stream.onerror=()=>retry(attempt);
  }catch{retry(attempt);}
 }
 return {start:connect,stop};
}
