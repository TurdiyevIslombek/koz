import {scryptSync,timingSafeEqual,randomBytes} from 'node:crypto';

export const loopback=address=>['127.0.0.1','::1','::ffff:127.0.0.1'].includes(address);
export function normalizeOrigin(value){
 const url=new URL(value);
 if(url.protocol!=='https:'||url.origin!==value||url.username||url.password)throw Error('KOZ_PUBLIC_ORIGIN must be an HTTPS origin');
 return url;
}
export function passwordVerifier(password){
 const salt=randomBytes(16),digest=password?scryptSync(password,salt,32):null;
 // The returned closure retains the digest and salt, not the original password.
 password=undefined;
 return {configured:Boolean(digest),verify:value=>Boolean(digest)&&typeof value==='string'&&value.length<=256&&timingSafeEqual(digest,scryptSync(value,salt,32))};
}
export function requestPolicy(req,publicOrigin){
 const host=req.headers.host||'';
 const cloud=Boolean(publicOrigin);
 const origin=cloud?publicOrigin:`http://${host}`;
 const hostOK=cloud?host===new URL(publicOrigin).host:['localhost','127.0.0.1','[::1]'].includes(host.replace(/:\d+$/,''));
 const secure=cloud&&loopback(req.socket.remoteAddress)&&req.headers['x-forwarded-proto']==='https';
 const health=req.url==='/api/health'&&req.method==='GET'&&loopback(req.socket.remoteAddress)&&['localhost','127.0.0.1','[::1]'].includes(host.replace(/:\d+$/,''));
 const mutation=!['GET','HEAD'].includes(req.method);
 const originOK=req.headers['sec-fetch-site']!=='cross-site'&&(!mutation||
   (cloud?req.headers.origin===origin:!req.headers.origin||req.headers.origin===origin));
 return {allowed:health||(hostOK&&(!cloud||secure)),originOK,secure};
}
