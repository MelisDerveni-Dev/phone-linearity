import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve, dirname } from 'node:path';
import { spawn } from 'node:child_process';
import { randomUUID } from 'node:crypto';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const identity = {name:'Identity — uncalibrated', fitted:false, units:'m/s^2', S:[[1,0,0],[0,1,0],[0,0,1]], b:[0,0,0]};
const finite = v => typeof v === 'number' && Number.isFinite(v);

export function inverse3(A) {
  const work = A.map((row,i) => [...row, ...[0,1,2].map(j => +(i === j))]);
  for (let col=0; col<3; col++) {
    let p=col;
    for(let i=col+1;i<3;i++) if(Math.abs(work[i][col])>Math.abs(work[p][col])) p=i;
    if(Math.abs(work[p][col])<1e-12) throw new Error('Calibration matrix S is singular or too close to singular.');
    [work[p],work[col]]=[work[col],work[p]];
    const pivot=work[col][col];
    for(let j=0;j<6;j++) work[col][j]/=pivot;
    for(let i=0;i<3;i++) if(i!==col) {const f=work[i][col];for(let j=0;j<6;j++) work[i][j]-=f*work[col][j];}
  }
  return work.map(r=>r.slice(3));
}

export function validateCalibration(input) {
  if(!input || !Array.isArray(input.S) || input.S.length!==3 || !input.S.every(r=>Array.isArray(r)&&r.length===3&&r.every(finite)) || !Array.isArray(input.b) || input.b.length!==3 || !input.b.every(finite)) throw new Error('Expected finite S (3×3) and b (3 values).');
  if(input.units && !['m/s^2','m/s²'].includes(input.units)) throw new Error('Calibration units must be m/s^2.');
  const inv=inverse3(input.S);
  const norm=A=>Math.max(...A.map(r=>r.reduce((n,v)=>n+Math.abs(v),0)));
  if(norm(input.S)*norm(inv)>1e8) throw new Error('Calibration is too ill-conditioned to apply reliably.');
  const provenance=typeof input.provenance==='object' && input.provenance!==null ? input.provenance : null;
  return {name: typeof input.name==='string' ? input.name.slice(0,100) : 'Imported calibration', fitted:input.fitted===true && provenance!==null, units:'m/s^2', S:input.S.map(r=>[...r]), b:[...input.b], provenance};
}

export function correct(raw, calibration) {
  const inv=inverse3(calibration.S);
  return inv.map(row=>row.reduce((sum,v,j)=>sum+v*(raw[j]-calibration.b[j]),0));
}

export function normalizePhoneUrl(value) {
  let url;
  try {url=new URL(String(value).includes('://') ? value : `http://${value}`);} catch {throw new Error('Enter the local URL shown in phyphox, such as http://192.168.1.42:8080.');}
  const h=url.hostname;
  const ip=h.split('.').map(Number);
  const local=ip.length===4 && ip.every(v=>Number.isInteger(v)&&v>=0&&v<=255) && (ip[0]===10 || ip[0]===127 || (ip[0]===192&&ip[1]===168) || (ip[0]===172&&ip[1]>=16&&ip[1]<=31) || (ip[0]===169&&ip[1]===254));
  if(!['http:','https:'].includes(url.protocol) || (!local && h!=='localhost') || url.username || url.password || !['','/'].includes(url.pathname) || url.search || url.hash) throw new Error('Use the private IPv4 URL shown by phyphox (same Wi-Fi), without a path or password.');
  return url.origin;
}

export function discoverBuffers(config, override) {
  const inputs=config.inputs || [];
  const input=inputs.find(i=>i.sensor==='accelerometer' || i.type==='accelerometer' || (i.source==='accelerometer'));
  // Explicitly refuse gravity-removed experiments even when their buffers use accX names.
  if(!input && (inputs.some(i=>[i.sensor,i.type,i.source].includes('linear_acceleration')) || /without\s*g|linear\s*acceleration/i.test(config.title||''))) throw new Error('Select Acceleration with g in phyphox; the gravity-removed experiment cannot be used here.');
  const available=new Set((config.buffers||[]).map(b=>typeof b==='string'?b:b.name));
  let detected={};
  const outputs=input?.outputs || input?.output || [];
  if(Array.isArray(outputs)) for(const o of outputs) {
    if(['t','x','y','z'].includes(o.component)) detected[o.component]=o.buffer;
    for(const k of ['t','x','y','z']) if(typeof o[k]==='string')detected[k]=o[k];
  }
  else if(outputs && typeof outputs==='object') for(const k of ['t','x','y','z']) detected[k]=outputs[k];
  const defaults={t:['acc_time','accT','time','t'],x:['accX','accx'],y:['accY','accy'],z:['accZ','accz']};
  for(const k of ['t','x','y','z']) if(!detected[k]) detected[k]=defaults[k].find(n=>available.has(n));
  if(override) detected={...detected,...override};
  if(!['t','x','y','z'].every(k=>typeof detected[k]==='string'&&available.has(detected[k])) || new Set(Object.values(detected)).size!==4) throw new Error('Could not identify four acceleration buffers. Select Acceleration with g, or provide --buffers time,x,y,z.');
  return detected;
}

export function discoverAttitudeBuffers(config) {
  const input=(config.inputs||[]).find(i=>[i.source,i.sensor,i.type].includes('attitude'));
  if(!input)return null;
  const names=new Set((config.buffers||[]).map(b=>typeof b==='string'?b:b.name));
  const map={},outputs=input.outputs||input.output||[];
  if(Array.isArray(outputs))for(const o of outputs){
    if(typeof o.component==='string')map[o.component]=o.buffer;
    for(const k of ['t','x','y','z','abs','w'])if(typeof o[k]==='string')map[k]=o[k];
  }
  else if(outputs&&typeof outputs==='object')Object.assign(map,outputs);
  const result={t:map.t,x:map.x,y:map.y,z:map.z,w:map.abs||map.w};
  return Object.values(result).every(n=>typeof n==='string'&&names.has(n))&&new Set(Object.values(result)).size===5?result:null;
}

export function createObservatory({pollMs=50, defaultBuffers}={}) {
  const state={connected:false,source:'none',phoneUrl:'',measuring:false,session:null,error:null,latencyMs:null,lastReceivedAt:null,calibration:structuredClone(identity),buffers:null,points:[],count:0,revision:0,attitudeAvailable:false,orientation:null,orientationSamples:[],orientationReceivedAt:null,orientationError:null};
  let generation=0, timer=null, lastT=null, queue=Promise.resolve(), previewT=0;
  let attitudeBuffers=null,lastAttitudeT=null;
  let epoch=randomUUID(), inverse=inverse3(state.calibration.S);
  const listeners=new Set();
  const snapshot=()=>({...state,points:state.points});
  const reset=()=>{epoch=randomUUID();state.points=[];state.count=0;lastT=null;state.lastReceivedAt=null;lastAttitudeT=null;state.orientation=null;state.orientationSamples=[];state.orientationReceivedAt=null;state.orientationError=null;};
  const updates=({since=-1,epoch:previousEpoch}={})=>{
    const {points,...metadata}=state;
    const oldest=state.count-points.length;
    const append=previousEpoch===epoch && Number.isInteger(since) && since>=oldest && since<=state.count;
    let first=append?since-oldest:0;
    // New viewers need only the longest selectable plot window, not all history.
    if(!append && points.length) {const cutoff=points.at(-1).t-32;while(first<points.length && points[first].t<cutoff)first++;}
    return {...metadata,epoch,cursor:state.count,append,points:points.slice(first)};
  };
  const touch=()=>{state.revision++;for(const listener of listeners)listener();};
  const stop=()=>{generation++;clearTimeout(timer);timer=null;};
  const phoneRequest=(url,path)=>{
    const run=async()=>{
      const response=await fetch(`${url}${path}`,{signal:AbortSignal.timeout(5000),redirect:'error'});
      if(!response.ok) throw new Error(`phyphox returned HTTP ${response.status}.`);
      const content=await response.text();
      if(content.length>16_000_000) throw new Error('Phone response too large; restart with a shorter recording.');
      try {return JSON.parse(content);} catch {throw new Error('Phone did not return phyphox JSON. Check the URL and enable remote access.');}
    };
    const job=queue.then(run,run);queue=job.catch(()=>{});return job;
  };
  const apply=raw=>inverse.map(row=>row.reduce((sum,v,j)=>sum+v*(raw[j]-state.calibration.b[j]),0));
  const append=(t,raw)=>{state.points.push({t,raw,corrected:apply(raw)});state.count++;lastT=t;state.lastReceivedAt=Date.now();};
  const trim=()=>{if(!state.points.length)return;const min=state.points.at(-1).t-120;let n=0;while(n<state.points.length&&state.points[n].t<min)n++;if(n)state.points.splice(0,n);if(state.points.length>30000)state.points.splice(0,state.points.length-30000);};
  const poll=async(token)=>{
    if(token!==generation)return;
    const start=Date.now();
    try {
      // Bootstrap from single latest timestamps. Fetch only the last 32 seconds
      // of acceleration / 0.5 seconds of attitude, even on long phone recordings.
      if(lastT===null||(attitudeBuffers&&lastAttitudeT===null)){
        const clocks=[state.buffers.t,...(attitudeBuffers?[attitudeBuffers.t]:[])];
        const latest=await phoneRequest(state.phoneUrl,`/get?${clocks.map(encodeURIComponent).join('&')}`);
        if(token!==generation)return;
        const acc=latest.buffer?.[state.buffers.t]?.buffer?.at(-1);
        const att=attitudeBuffers?latest.buffer?.[attitudeBuffers.t]?.buffer?.at(-1):null;
        if(lastT===null&&finite(acc))lastT=Math.max(-1,acc-32);
        if(lastAttitudeT===null&&finite(att))lastAttitudeT=Math.max(-1,att-.5);
      }
      const query=new URLSearchParams();
      for(const k of ['t','x','y','z']) query.set(state.buffers[k],lastT===null?'full':k==='t'?String(lastT):`${lastT}|${state.buffers.t}`);
      if(attitudeBuffers)for(const k of ['t','x','y','z','w'])query.set(attitudeBuffers[k],lastAttitudeT===null?'full':k==='t'?String(lastAttitudeT):`${lastAttitudeT}|${attitudeBuffers.t}`);
      const data=await phoneRequest(state.phoneUrl,`/get?${query}`);
      if(token!==generation)return;
      const session=data.status?.session;
      if(state.session!==null && session!==undefined && session!==state.session) {
        reset();state.connected=false;state.measuring=false;state.error='The phyphox experiment changed. Reconnect to your selected acceleration experiment.';stop();touch();return;
      }
      state.session=session??state.session;state.measuring=data.status?.measuring===true;state.latencyMs=Date.now()-start;
      const arrays=['t','x','y','z'].map(k=>data.buffer?.[state.buffers[k]]?.buffer);
      if(!arrays.every(Array.isArray))throw new Error('Acceleration buffers are missing. Reconnect to Acceleration with g.');
      if(!arrays.every(a=>a.length===arrays[0].length))throw new Error('Phone returned unaligned time/axis buffers; skipping this batch.');
      // A full time update is sent by phyphox after clearing the experiment.
      if(lastT!==null && data.buffer[state.buffers.t].updateMode==='full' && arrays[0].length && arrays[0].at(-1)<lastT) reset();
      for(let i=0;i<arrays[0].length;i++) {
        const t=arrays[0][i],raw=[arrays[1][i],arrays[2][i],arrays[3][i]];
        if(finite(t)&&raw.every(finite)&&(lastT===null||t>lastT))append(t,raw);
      }
      if(attitudeBuffers){
        const att=['t','x','y','z','w'].map(k=>data.buffer?.[attitudeBuffers[k]]?.buffer);
        if(att.every(Array.isArray)&&att.every(a=>a.length===att[0].length)){
          if(att[0].length&&lastAttitudeT!==null&&data.buffer[attitudeBuffers.t].updateMode==='full'&&att[0].at(-1)<lastAttitudeT){lastAttitudeT=null;state.orientation=null;state.orientationSamples=[];state.orientationReceivedAt=null;}
          for(let i=0;i<att[0].length;i++){
            const t=att[0][i],q=[att[1][i],att[2][i],att[3][i],att[4][i]],norm=Math.hypot(...q);
            if(finite(t)&&q.every(finite)&&Number.isFinite(norm)&&norm>1e-6&&(lastAttitudeT===null||t>lastAttitudeT)){state.orientation={t,q:q.map(v=>v/norm),source:'attitude'};state.orientationSamples.push(state.orientation);lastAttitudeT=t;state.orientationReceivedAt=Date.now();}
          }
          if(state.orientation)state.orientationSamples=state.orientationSamples.filter(p=>p.t>=state.orientation.t-.5).slice(-250);
          state.orientationError=null;
        }else{state.orientation=null;state.orientationSamples=[];state.orientationReceivedAt=null;state.orientationError='Attitude buffers are unavailable or not aligned.';}
      }
      trim();state.error=null;
    } catch(error) {if(token!==generation)return;state.error=`${error.message} Keep phyphox open, enable remote access, and check that both devices share Wi-Fi.`;}
    touch();
    if(token===generation)timer=setTimeout(()=>poll(token),Math.max(10,pollMs-(Date.now()-start)));
  };
  const preview=token=>{
    if(token!==generation)return;
    for(let i=0;i<3;i++) {previewT+=0.02;const t=previewT;const angle=0.3*Math.sin(t*.7);append(t,[9.81*Math.sin(angle)+.08, .12*Math.sin(t*1.2)-.03,9.81*Math.cos(angle)+.05]);}
    trim();touch();timer=setTimeout(()=>preview(token),60);
  };
  const connect=async({url,buffers})=>{
    stop();reset();attitudeBuffers=null;state.attitudeAvailable=false;state.source='none';state.connected=false;state.measuring=false;state.error=null;state.session=null;state.latencyMs=null;
    const token=generation;
    try {
      state.phoneUrl=normalizePhoneUrl(url);
      const config=await phoneRequest(state.phoneUrl,'/config');
      if(token!==generation)return snapshot();
      state.buffers=discoverBuffers(config,buffers||defaultBuffers);attitudeBuffers=discoverAttitudeBuffers(config);state.attitudeAvailable=Boolean(attitudeBuffers);
    } catch(error) {
      // The previous stream was already stopped and cleared: tell every window, then report the failure.
      if(token===generation){state.error=`Connection failed: ${error.message}`;touch();}
      throw error;
    }
    state.connected=true;state.source='phone';touch();
    await poll(token);return snapshot();
  };
  const disconnect=()=>{stop();attitudeBuffers=null;state.attitudeAvailable=false;state.connected=false;state.measuring=false;state.source='none';state.error=null;reset();touch();return snapshot();};
  const setPreview=enabled=>{
    disconnect();if(enabled){state.source='synthetic';state.measuring=true;state.session='synthetic-preview';state.latencyMs=null;previewT=0;preview(generation);}return snapshot();
  };
  const calibrate=input=>{const c=validateCalibration(input);state.calibration=c;inverse=inverse3(c.S);epoch=randomUUID();state.points=state.points.map(p=>({...p,corrected:apply(p.raw)}));touch();return snapshot();};
  const control=async cmd=>{
    if(state.source!=='phone'||!state.connected)throw new Error('Connect a phone before starting or stopping its measurement.');
    if(!['start','stop'].includes(cmd))throw new Error('Only start and stop are supported.');
    const token=generation;const response=await phoneRequest(state.phoneUrl,`/control?cmd=${cmd}`);
    if(token!==generation)throw new Error('Connection changed while the command was running.');
    if(response.result!==true)throw new Error('phyphox rejected the command. Check the phone.');
    // Actual measuring state comes from /get, including timed-run delays.
    touch();return snapshot();
  };
  return {snapshot,updates,subscribe:listener=>{listeners.add(listener);return()=>listeners.delete(listener);},connect,disconnect,setPreview,calibrate,control,close:stop};
}

export function createServer(options={}) {
  const observatory=createObservatory(options);
  const json=(res,status,value)=>{res.writeHead(status,{'content-type':'application/json; charset=utf-8','cache-control':'no-store'});res.end(JSON.stringify(value));};
  const server=http.createServer(async(req,res)=>{
    try {
      // Bind and browser-origin checks keep a LAN instrument behind the local app.
      const host=req.headers.host||'';
      if(!/^localhost(?::\d+)?$|^127\.0\.0\.1(?::\d+)?$/.test(host))return json(res,403,{error:'Use the localhost dashboard URL.'});
      if(req.headers.origin && req.headers.origin!==`http://${host}`)return json(res,403,{error:'Cross-origin requests are not accepted.'});
      const url=new URL(req.url,`http://${host}`);
      if(req.method==='GET'&&url.pathname==='/experiments/observatory-motion.phyphox'){
        const content=await readFile(resolve(root,'experiments','observatory-motion.phyphox'));
        res.writeHead(200,{'content-type':'application/octet-stream','content-disposition':'attachment; filename="observatory-motion.phyphox"','x-content-type-options':'nosniff'});res.end(content);return;
      }
      if(req.method==='GET'&&url.pathname==='/api/state')return json(res,200,observatory.snapshot());
      if(req.method==='GET'&&url.pathname==='/api/events') {
        res.writeHead(200,{'content-type':'text/event-stream','cache-control':'no-cache, no-transform','connection':'keep-alive','x-accel-buffering':'no'});
        req.socket.setNoDelay(true);
        res.flushHeaders();
        res.write('retry: 1000\n\n');
        let cursor=-1,epoch=null,blocked=false;
        const send=()=>{
          if(blocked||res.destroyed)return;
          const update=observatory.updates({since:cursor,epoch});
          blocked=!res.write(`event: state\ndata: ${JSON.stringify(update)}\n\n`);
          cursor=update.cursor;epoch=update.epoch;
        };
        const unsubscribe=observatory.subscribe(send);
        res.on('drain',()=>{blocked=false;send();});
        const heartbeat=setInterval(()=>{if(!blocked&&!res.destroyed)blocked=!res.write(': heartbeat\n\n');},10000);
        res.on('close',()=>{unsubscribe();clearInterval(heartbeat);});
        send();return;
      }
      if(req.method==='POST'&&url.pathname.startsWith('/api/')) {
        if(!req.headers['content-type']?.startsWith('application/json'))return json(res,415,{error:'Send application/json.'});
        let body='';for await(const chunk of req){body+=chunk;if(body.length>65536)return json(res,413,{error:'Request exceeds 64 KB.'});}
        let input;try{input=JSON.parse(body||'{}');}catch{return json(res,400,{error:'Malformed JSON.'});}
        let result;
        switch(url.pathname) {
          case '/api/connect':result=await observatory.connect(input);break;
          case '/api/disconnect':result=observatory.disconnect();break;
          case '/api/control':result=await observatory.control(input.cmd);break;
          case '/api/calibration':result=observatory.calibrate(input);break;
          case '/api/preview':if(typeof input.enabled!=='boolean')throw new Error('enabled must be boolean.');result=observatory.setPreview(input.enabled);break;
          default:return json(res,404,{error:'Unknown endpoint.'});
        }
        return json(res,200,url.searchParams.has('compact')?{ok:true}:result);
      }
      const assets={'/':['index.html','text/html'],'/app.js':['app.js','text/javascript'],'/plot.mjs':['plot.mjs','text/javascript'],'/comparison.mjs':['comparison.mjs','text/javascript'],'/presentation.mjs':['presentation.mjs','text/javascript'],'/presentation.css':['presentation.css','text/css'],'/styles.css':['styles.css','text/css'],'/motion.mjs':['motion.mjs','text/javascript'],'/orientation.mjs':['orientation.mjs','text/javascript'],'/phone-model.mjs':['phone-model.mjs','text/javascript'],'/phone-model.css':['phone-model.css','text/css'],'/motion-stage.css':['motion-stage.css','text/css'],'/motion-setup-qr.svg':['motion-setup-qr.svg','image/svg+xml']};
      if(req.method!=='GET'||!assets[url.pathname])return json(res,404,{error:'Not found.'});
      const [file,type]=assets[url.pathname];const content=await readFile(resolve(root,'web',file));
      res.writeHead(200,{'content-type':`${type}; charset=utf-8`,'cache-control':'no-cache','x-content-type-options':'nosniff','content-security-policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"});res.end(content);
    } catch(error) {json(res,400,{error:error.message});}
  });
  server.on('close',()=>observatory.close());
  return {server,observatory};
}

async function main() {
  const args=process.argv.slice(2);
  const option=(name,fallback)=>{const i=args.indexOf(name);return i<0?fallback:args[i+1];};
  if(args.includes('--help')) {console.log('Usage: npm start -- [--phone http://192.168.1.42:8080] [--port 5173] [--no-open] [--calibration calibration/params.json] [--buffers time,x,y,z]\nPhone stays untouched until you press Start. No measurements are saved by this viewer.');return;}
  const port=Number(option('--port','5173'));
  if(!Number.isInteger(port)||port<1||port>65535)throw new Error('Port must be between 1 and 65535.');
  const names=option('--buffers',null)?.split(',');
  if(names&&names.length!==4)throw new Error('--buffers requires four comma-separated names: time,x,y,z.');
  const {server,observatory}=createServer({defaultBuffers:names?Object.fromEntries(['t','x','y','z'].map((k,i)=>[k,names[i]])):undefined});
  if(option('--calibration',null))observatory.calibrate(JSON.parse(await readFile(resolve(option('--calibration')),'utf8')));
  server.on('error',error=>{console.error(`Unable to launch: ${error.message}`);process.exitCode=1;observatory.close();});
  server.listen(port,'127.0.0.1',async()=>{
    const local=`http://127.0.0.1:${port}`;
    console.log(`\nThe Affine Observatory\n${local}\nOpen the graph window with “Display window”. Ctrl+C stops the viewer.\n`);
    if(option('--phone',null))try{await observatory.connect({url:option('--phone')});}catch(error){console.error(`Phone connection: ${error.message}`);}
    if(!args.includes('--no-open')) {
      const child=process.platform==='win32'?spawn('rundll32',['url.dll,FileProtocolHandler',local],{detached:true,stdio:'ignore',windowsHide:true}):spawn(process.platform==='darwin'?'open':'xdg-open',[local],{detached:true,stdio:'ignore'});
      child.on('error',()=>console.log(`Open ${local} in your browser.`));child.unref();
    }
  });
  for(const signal of ['SIGINT','SIGTERM'])process.once(signal,()=>{observatory.close();server.close();server.closeAllConnections();});
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))main().catch(error=>{console.error(error.message);process.exitCode=1;});
