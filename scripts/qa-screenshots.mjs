import { spawn } from 'node:child_process';
import { mkdir, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

const edge='C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const port=9337;
const profile=join(tmpdir(),'prahari-frontend-v2-qa-edge-profile');
const output=join(process.cwd(),'qa-screenshots');
await rm(profile,{recursive:true,force:true});await mkdir(output,{recursive:true});
const child=spawn(edge,['--headless=new','--disable-gpu',`--remote-debugging-port=${port}`,`--user-data-dir=${profile}`,'about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let page;
for(let i=0;i<30;i++){try{const list=await fetch(`http://127.0.0.1:${port}/json/list`).then(r=>r.json());page=list.find(x=>x.type==='page');if(page)break}catch{}await sleep(200)}
if(!page)throw new Error('Edge DevTools target unavailable');
const socket=new WebSocket(page.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject});
let seq=0;const pending=new Map();socket.onmessage=e=>{const msg=JSON.parse(e.data);if(msg.id&&pending.has(msg.id)){const {resolve,reject}=pending.get(msg.id);pending.delete(msg.id);msg.error?reject(new Error(msg.error.message)):resolve(msg.result)}};
const send=(method,params={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}))});
await send('Page.enable');await send('Runtime.enable');
await send('Page.navigate',{url:'http://127.0.0.1:4173/login'});await sleep(600);
await send('Runtime.evaluate',{expression:"localStorage.setItem('prahari-v2-demo-session','true')"});
await send('Page.navigate',{url:'http://127.0.0.1:4173/officer/projects'});await sleep(900);
for(const [width,height] of [[1366,768],[1440,900],[1920,1080]]){
 await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false});await sleep(250);
 const {data}=await send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});
 await writeFile(join(output,`projects-${width}x${height}.png`),Buffer.from(data,'base64'));
}
socket.close();child.kill();await Promise.race([new Promise(resolve=>child.once('exit',resolve)),sleep(1500)]);await rm(profile,{recursive:true,force:true}).catch(()=>{});
console.log(output);
