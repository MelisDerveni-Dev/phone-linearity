import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import {setTimeout as delay} from 'node:timers/promises';
import {createServer,correct,validateCalibration,normalizePhoneUrl,discoverBuffers} from '../scripts/live.mjs';

const config={title:'Acceleration with g',inputs:[{source:'accelerometer',outputs:[{x:'accX'},{y:'accY'},{z:'accZ'},{t:'acc_time'}]}],buffers:['accX','accY','accZ','acc_time'].map(name=>({name,size:0}))};
const listen=server=>new Promise(resolve=>server.listen(0,'127.0.0.1',()=>resolve(`http://127.0.0.1:${server.address().port}`)));
const close=server=>new Promise(resolve=>{server.closeAllConnections();server.close(resolve);});
const until=async(fn)=>{for(let i=0;i<100;i++){if(fn())return;await delay(15);}throw new Error('State did not settle.');};

test('recovers known vector with gains, bias and cross-axis terms',()=>{
  const c=validateCalibration({S:[[1.1,.02,-.01],[.04,.9,.03],[-.02,.01,1.05]],b:[.12,-.07,.2]});
  const truth=[2,-4,8];const measured=c.S.map((row,i)=>row.reduce((n,v,j)=>n+v*truth[j],c.b[i]));
  correct(measured,c).forEach((v,i)=>assert.ok(Math.abs(v-truth[i])<1e-11));
});

test('rejects singular, ill-conditioned, nonfinite and incorrectly sized calibration',()=>{
  const valid={S:[[1,0,0],[0,1,0],[0,0,1]],b:[0,0,0]};
  for(const input of [{...valid,S:[[1,0,0],[1,0,0],[0,0,1]]},{...valid,S:[[1e10,0,0],[0,1,0],[0,0,1]]},{...valid,b:[0,NaN,0]},{...valid,b:[0,0]},{...valid,units:'g'}]) assert.throws(()=>validateCalibration(input));
  assert.equal(validateCalibration({...valid,fitted:true}).fitted,false);
  assert.equal(validateCalibration({...valid,fitted:true,provenance:{session:'A'}}).fitted,true);
});

test('discovers official single-entry component outputs and custom names; refuses gravity-removed data',()=>{
  assert.deepEqual(discoverBuffers(config),{x:'accX',y:'accY',z:'accZ',t:'acc_time'});
  const c={...config,inputs:[{source:'accelerometer',outputs:[{x:'one'},{y:'two'},{z:'three'},{t:'clock'}]}],buffers:['one','two','three','clock'].map(name=>({name}))};
  assert.equal(discoverBuffers(c).t,'clock');
  assert.throws(()=>discoverBuffers({...config,title:'Acceleration (without g)',inputs:[{source:'linear_acceleration'}]}));
  assert.throws(()=>discoverBuffers(config,{t:'accX'}));
});

test('accepts local phone addresses and refuses public hosts, credentials and paths',()=>{
  assert.equal(normalizePhoneUrl('192.168.0.42:8080'),'http://192.168.0.42:8080');
  assert.equal(normalizePhoneUrl('http://10.0.0.1/'),'http://10.0.0.1');
  for(const address of ['https://example.com','http://8.8.8.8','http://user:secret@192.168.1.1','http://192.168.1.1/get','file:///etc/passwd'])assert.throws(()=>normalizePhoneUrl(address));
});

test('mock-phone integration: incremental alignment, correction, start/stop and experiment change',async()=>{
  let session='A',measuring=false,requests=[];
  let samples=[[0,1,2,9.81],[.02,2,3,9.8],[.04,3,4,9.79]];
  const phone=http.createServer((req,res)=>{
    const url=new URL(req.url,'http://localhost');requests.push(url);
    res.setHeader('content-type','application/json');
    if(url.pathname==='/config')return res.end(JSON.stringify(config));
    if(url.pathname==='/control'){measuring=url.searchParams.get('cmd')==='start';return res.end('{"result":true}');}
    const threshold=url.searchParams.get('acc_time');const selected=threshold==='full'?samples:samples.filter(s=>s[0]>Number(threshold));
    const buffer=Object.fromEntries(['acc_time','accX','accY','accZ'].map((name,i)=>[name,{size:0,updateMode:threshold==='full'?'full':'partial',buffer:selected.map(s=>s[i])}]));
    res.end(JSON.stringify({buffer,status:{session,measuring}}));
  });
  const phoneUrl=await listen(phone);const app=createServer({pollMs:20});const appUrl=await listen(app.server);
  const post=async(path,body)=>{const r=await fetch(appUrl+path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});const data=await r.json();assert.equal(r.status,200,JSON.stringify(data));return data;};
  try {
    let s=await post('/api/connect',{url:phoneUrl});assert.equal(s.count,3);assert.equal(s.measuring,false);assert.deepEqual(s.points[0].raw,s.points[0].corrected);
    const baseline=app.observatory.updates();
    assert.equal(baseline.append,false);assert.equal(baseline.cursor,3);
    samples.push([.06,null,5,9.8],[.08,4,5,9.8]);
    await until(()=>app.observatory.snapshot().count===4);
    const delta=app.observatory.updates({epoch:baseline.epoch,since:baseline.cursor});
    assert.equal(delta.append,true);assert.equal(delta.points.length,1);assert.equal(delta.points[0].t,.08);
    assert.equal(app.observatory.snapshot().points.at(-1).t,.08);
    await delay(70);assert.equal(app.observatory.snapshot().count,4,'duplicate times must not accumulate');
    assert.ok(requests.some(u=>u.searchParams.get('accX')?.includes('|acc_time')),'incremental x uses time reference');
    s=await post('/api/calibration',{S:[[2,0,0],[0,1,0],[0,0,1]],b:[0,0,0]});assert.equal(s.points.at(-1).corrected[0],2);assert.equal(s.points.at(-1).raw[0],4);
    const reprojected=app.observatory.updates({epoch:delta.epoch,since:delta.cursor});
    assert.equal(reprojected.append,false);assert.notEqual(reprojected.epoch,delta.epoch);assert.equal(reprojected.points.at(-1).corrected[0],2);
    await post('/api/control',{cmd:'start'});await until(()=>app.observatory.snapshot().measuring);
    await post('/api/control',{cmd:'stop'});await until(()=>!app.observatory.snapshot().measuring);
    session='B';await until(()=>!app.observatory.snapshot().connected);s=app.observatory.snapshot();assert.equal(s.points.length,0);assert.match(s.error,/experiment changed/);
    s=await post('/api/connect',{url:phoneUrl});assert.equal(s.count,4);assert.equal(s.session,'B');
    s=await post('/api/preview',{enabled:true});assert.equal(s.source,'synthetic');assert.ok(s.count>0);
    s=await post('/api/preview',{enabled:false});assert.equal(s.source,'none');assert.equal(s.points.length,0);
  } finally {app.observatory.close();await close(app.server);await close(phone);}
});

test('SSE delivers compact incremental samples independently to both windows',async()=>{
  const app=createServer();const url=await listen(app.server);
  const controllers=[];
  async function open(){
    const controller=new AbortController();controllers.push(controller);
    const response=await fetch(url+'/api/events',{signal:controller.signal});
    assert.match(response.headers.get('content-type'),/text\/event-stream/);
    const reader=response.body.getReader();let buffer='';
    return async()=>{
      while(true){
        const end=buffer.indexOf('\n\n');
        if(end>=0){const frame=buffer.slice(0,end);buffer=buffer.slice(end+2);const line=frame.split('\n').find(l=>l.startsWith('data: '));if(line)return JSON.parse(line.slice(6));continue;}
        const next=await reader.read();if(next.done)throw new Error('Stream ended');buffer+=new TextDecoder().decode(next.value);
      }
    };
  }
  try{
    const nextA=await open(),nextB=await open();
    assert.equal((await nextA()).source,'none');assert.equal((await nextB()).source,'none');
    app.observatory.setPreview(true);
    await nextA();await nextB(); // Disconnect/reset metadata before preview starts.
    const a=await nextA(),b=await nextB();
    assert.equal(a.source,'synthetic');assert.equal(a.append,true);assert.deepEqual(a.points,b.points);
    const next=await nextA();assert.equal(next.append,true);assert.equal(next.points.length,3);assert.ok(next.cursor>a.cursor);
    const compact=await fetch(url+'/api/preview?compact=1',{method:'POST',headers:{'content-type':'application/json'},body:'{"enabled":false}'});
    assert.deepEqual(await compact.json(),{ok:true});
  }finally{controllers.forEach(c=>c.abort());app.observatory.close();await close(app.server);}
});

test('HTTP surface serves local UI, rejects foreign origins and malformed JSON',async()=>{
  const app=createServer();const url=await listen(app.server);
  try{
    assert.equal((await fetch(url)).status,200);
    const r=await fetch(url+'/api/state');assert.equal((await r.json()).source,'none');
    assert.equal((await fetch(url+'/api/preview',{method:'POST',headers:{'content-type':'application/json',origin:'https://unrelated.example'},body:'{"enabled":true}'})).status,403);
    assert.equal((await fetch(url+'/api/preview',{method:'POST',headers:{'content-type':'application/json'},body:'bad json'})).status,400);
    assert.equal((await fetch(url+'/missing')).status,404);
  }finally{app.observatory.close();await close(app.server);}
});
