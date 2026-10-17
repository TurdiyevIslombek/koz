import {EYE_FRESH_MS, readEyeClosed, validEyeJPEG} from './eye-protocol.js';

// Separate from events and application persistence. A Blob URL lives for at most one second.
export function createEyeConnection({onChange, WebSocket=globalThis.WebSocket,
 url=()=>`${location.protocol==='https:'?'wss:':'ws:'}//${location.host}/api/eye`,
 objects=globalThis.URL, retryMs=1000}) {
 let socket=null, retry=null, expiry=null, enabled=false, allowed=false, generation=0, scope=null;
 let state={url:null,reason:'not_running'};
 function drop(reason) {
  clearTimeout(expiry);
  if (state.url) objects.revokeObjectURL(state.url);
  const changed=Boolean(state.url)||state.reason!==reason;
  state={url:null,reason};
  if (changed) onChange();
 }
 function disconnect(reason) {
  generation++; clearTimeout(retry); retry=null;
  const previous=socket; socket=null; previous?.close(); drop(reason);
 }
 function connect() {
  if (!enabled || socket) return;
  const attempt=++generation;
  const ws=socket=new WebSocket(url()); ws.binaryType='arraybuffer';
  ws.onmessage=event=>{
   if (attempt!==generation || !enabled) return;
   try {
    if (typeof event.data==='string') { drop(readEyeClosed(event.data).reason); return; }
    if (!(event.data instanceof ArrayBuffer) || !validEyeJPEG(new Uint8Array(event.data))) throw Error('Invalid preview');
    if (!allowed) return;
    const previous=state.url;
    state={url:objects.createObjectURL(new Blob([event.data],{type:'image/jpeg'})),reason:null};
    if (previous) objects.revokeObjectURL(previous);
    clearTimeout(expiry); expiry=setTimeout(()=>drop('not_fresh'),EYE_FRESH_MS);
    onChange();
   } catch { disconnect('not_fresh'); if(enabled)retry=setTimeout(connect,retryMs); }
  };
  ws.onerror=()=>{};
  ws.onclose=()=>{
   if(attempt!==generation)return;
   generation++; socket=null; drop('not_fresh');
   if(enabled)retry=setTimeout(connect,retryMs);
  };
 }
 return {
  get state(){return state;},
  sync({active,open,reason='not_running',scope:nextScope=null}) {
   if(scope!==nextScope){scope=nextScope;drop('not_running');}
   allowed=Boolean(open);
   if(!active){enabled=false;disconnect(reason);return;}
   enabled=true;
   if(!allowed)drop(reason);
   if(!retry)connect();
  },
  failedImage(){drop('not_fresh');},
  stop(){enabled=false;allowed=false;disconnect('not_running');}
 };
}
