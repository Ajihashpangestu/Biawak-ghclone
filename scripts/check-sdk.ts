// In-process SDK transport for sandboxes that prohibit TCP listening.
// This verifies handlers and protocol bytes, not network behavior or real transport timings.
import {createApp} from '../app.ts';
import {Readable} from 'node:stream';
const app=createApp();
globalThis.fetch=async(input,init={})=>{const url=typeof input==='string'?input:input.url||String(input);const headers=Object.fromEntries(new Headers(init.headers||{}));headers.host='localhost';const req=Readable.from(init.body?[Buffer.from(init.body)]:[]);req.url=new URL(url).pathname+new URL(url).search;req.method=init.method||'GET';req.headers=headers;
return await new Promise((resolve,reject)=>{let status=200,h={},chunks=[];const res={headersSent:false,writeHead(s,hs){status=s;h=hs;this.headersSent=true;return this;},setHeader(k,v){h[k]=v;},write(b){chunks.push(Buffer.from(b));},end(b){if(b)chunks.push(Buffer.from(b));resolve(new Response(status===204||status===202?null:Buffer.concat(chunks),{status,headers:h}));}};app.emit('request',req,res);});};
const sdk=process.env.FORGE_SDK_PATH;
if(!sdk)throw new Error('Set FORGE_SDK_PATH to the kit sdk/run.ts file');
const perf=process.argv.includes('--perf');
process.argv=['node','sdk/run.ts','--url','http://localhost','--token',process.env.MAKEFUN_SHOP_TOKEN||'test','--json',...(perf?['--perf']:[])];
await import(sdk);
