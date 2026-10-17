import {WebSocket, WebSocketServer} from 'ws';
import {loopback, requestPolicy} from './security.mjs';
import {MAX_EYE_BYTES, EYE_FRESH_MS, eyeClosed, readEyeClosed, validEyeJPEG} from '../src/eye-protocol.js';

export function eyeRequestAllowed(req, authenticated) {
 return loopback(req.socket.remoteAddress) && requestPolicy(req, null).allowed &&
  req.headers.origin === `http://${req.headers.host}` &&
  req.headers['sec-fetch-site'] !== 'cross-site' && Boolean(authenticated(req));
}

// Constructed only by localAccess:true. One upstream, one newest frame in memory.
export function createEyeRelay({runnerUrl, authenticated, retryMs=1000}) {
 const url = new URL(runnerUrl);
 if (url.protocol !== 'ws:' || !['127.0.0.1','localhost','[::1]'].includes(url.hostname) || url.username || url.password) throw Error('Preview requires a local runner');
 url.pathname = '/v1/preview'; url.search = ''; url.hash = '';
 const viewers = new Map();
 const wss = new WebSocketServer({noServer:true,maxPayload:256,perMessageDeflate:false});
 wss.on('headers',headers=>headers.push('Cache-Control: no-store','X-Content-Type-Options: nosniff'));
 let upstream, retry, expiry, closed=false, allowed=false, scope=null;
 let frame=null, at=0, reason='not_running';
 const fresh = () => frame && performance.now()-at < EYE_FRESH_MS;
 function send(ws, value, binary=false) {
  if (!authenticated(viewers.get(ws)) || ws.bufferedAmount > 0) { ws.terminate(); return; }
  if (ws.readyState === WebSocket.OPEN) ws.send(value, {binary,compress:false});
 }
 function drop(why) {
  const changed = frame !== null || reason !== why;
  frame=null; at=0; reason=why; clearTimeout(expiry);
  if (changed) for (const ws of viewers.keys()) send(ws, JSON.stringify(eyeClosed(reason)));
 }
 function connect() {
  if (closed) return;
  const ws = upstream = new WebSocket(url, {maxPayload:MAX_EYE_BYTES,perMessageDeflate:false,handshakeTimeout:2500});
  ws.on('message', (data, binary) => {
   if (upstream !== ws || closed) return;
   try {
    if (!binary) { drop(readEyeClosed(new TextDecoder('utf-8',{fatal:true}).decode(data)).reason); return; }
    if (!validEyeJPEG(data)) throw Error('Invalid preview');
    if (!allowed) return;
    frame=data; at=performance.now();
    clearTimeout(expiry); expiry=setTimeout(()=>drop('not_fresh'), EYE_FRESH_MS); expiry.unref();
    for (const viewer of viewers.keys()) send(viewer, frame, true);
   } catch { drop('not_fresh'); ws.terminate(); }
  });
  ws.on('error', ()=>{});
  ws.on('close', ()=>{
   if (upstream !== ws || closed) return;
   drop('not_fresh'); retry=setTimeout(connect,retryMs); retry.unref();
  });
 }
 connect();
 const maintenance=setInterval(()=>{
  for (const [ws,req] of viewers) if (!authenticated(req)) ws.terminate();
 },250); maintenance.unref();
 return {
  gate({open,reason:why,scope:nextScope}) {
   if (scope !== nextScope) { scope=nextScope; drop('not_running'); }
   allowed=open;
   if (!open) drop(why);
  },
  upgrade(req,socket,head) {
   if (!eyeRequestAllowed(req,authenticated)) { socket.end('HTTP/1.1 403 Forbidden\r\nConnection: close\r\nCache-Control: no-store\r\n\r\n'); return; }
   if (viewers.size >= 4) { socket.end('HTTP/1.1 503 Service Unavailable\r\nConnection: close\r\n\r\n'); return; }
   wss.handleUpgrade(req,socket,head,ws=>{
    viewers.set(ws,req);
    // Never reuse a frame's full lifetime for a newly opened tab. Wait for the next JPEG.
    send(ws,JSON.stringify(eyeClosed(fresh()?'checking':reason)));
    ws.on('message',()=>ws.terminate()); // receive only
    ws.on('error',()=>{});
    ws.on('close',()=>viewers.delete(ws));
   });
  },
  closeViewers() { for (const ws of viewers.keys()) ws.terminate(); },
  close() { closed=true; allowed=false; drop('not_running'); clearTimeout(retry); clearTimeout(expiry); clearInterval(maintenance); upstream?.terminate(); for (const ws of viewers.keys()) ws.terminate(); wss.close(); }
 };
}
