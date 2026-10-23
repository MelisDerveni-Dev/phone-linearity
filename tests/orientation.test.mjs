import test from 'node:test';
import assert from 'node:assert/strict';
import {gravityQuaternion,normalizeQuaternion,slerpQuaternion,quaternionDistance,motionEvidence,createPoseTimeline,angularSpeedDegrees,createMotionGuard} from '../web/orientation.mjs';

function rotate(q,v){const [x,y,z,w]=q;const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];const t=cross([x,y,z],v).map(a=>2*a),c=cross([x,y,z],t);return v.map((a,i)=>a+w*t[i]+c[i]);}

test('gravity pose maps all six signed faces to world up, including upside down',()=>{
  for(const v of [[0,0,1],[0,0,-1],[1,0,0],[-1,0,0],[0,1,0],[0,-1,0]]){
    const q=gravityQuaternion(v);assert.ok(q.every(Number.isFinite));const up=rotate(q,v);
    up.forEach((value,i)=>assert.ok(Math.abs(value-(i===2?1:0))<1e-9));
  }
  assert.equal(gravityQuaternion([0,0,0]),null);assert.equal(gravityQuaternion([NaN,0,1]),null);
});

test('quaternion interpolation takes the shortest arc without flips or manufactured overshoot',()=>{
  const q=normalizeQuaternion([.3,.5,.1,.7]);
  assert.ok(quaternionDistance(q,slerpQuaternion(q,q.map(v=>-v),.5))<1e-6);
  const a=[0,0,0,1],b=[1,0,0,0],half=slerpQuaternion(a,b,.5);
  assert.ok(Math.abs(quaternionDistance(a,half)-Math.PI/2)<1e-8);
  assert.ok(Math.abs(Math.hypot(...half)-1)<1e-10);
  assert.equal(normalizeQuaternion([0,0,0,0]),null);
});

test('motion indicators distinguish quiet readings, strong motion and zero specific force without claiming sensor nonlinearity',()=>{
  const make=(vector,i)=>({t:i/100,corrected:vector});
  const quiet=Array.from({length:30},(_,i)=>make([0,0,9.81],i));
  assert.equal(motionEvidence(quiet).level,'steady');assert.ok(motionEvidence(quiet).variation<1e-10);
  const shaking=Array.from({length:30},(_,i)=>make([i%2?8:-8,0,9.81],i));
  assert.equal(motionEvidence(shaking).level,'uncertain');
  assert.equal(motionEvidence([make([0,0,0],0)]).level,'uncertain');
  assert.equal(motionEvidence([]).level,'unavailable');
});

test('gravity continuation stays stable around screen-down without inventing a heading measurement',()=>{
  let prior=gravityQuaternion([0,0,-1]);
  for(let i=0;i<=360;i++){
    const angle=i*Math.PI/180,epsilon=.0002;
    const v=[epsilon*Math.cos(angle),epsilon*Math.sin(angle),-Math.sqrt(1-epsilon**2)];
    const next=gravityQuaternion(v,prior);
    assert.ok(quaternionDistance(prior,next)<.001,'small sensor changes must not spin the displayed phone');
    rotate(next,v).forEach((value,axis)=>assert.ok(Math.abs(value-(axis===2?1:0))<1e-8));
    prior=next;
  }
  // The held display convention cannot detect a real rotation around gravity.
  assert.ok(quaternionDistance(prior,gravityQuaternion([0,0,-1],prior))<.001);
});

test('gravity continuation follows complete turns about both observable axes',()=>{
  for(const axis of [0,1]){
    let previous=[0,0,0,1];
    for(let i=0;i<=720;i++){
      const angle=i*Math.PI/360,vector=axis===0?[0,Math.sin(angle),Math.cos(angle)]:[Math.sin(angle),0,Math.cos(angle)];
      const q=gravityQuaternion(vector,previous);
      assert.ok(quaternionDistance(previous,q)<.009);
      rotate(q,vector).forEach((v,k)=>assert.ok(Math.abs(v-(k===2?1:0))<1e-8));
      previous=q;
    }
  }
});

test('timestamped playback interpolates measured poses, clamps endpoints and ignores duplicate arrivals',()=>{
  const timeline=createPoseTimeline();
  const yaw=t=>[0,0,Math.sin(t/2),Math.cos(t/2)];
  assert.equal(timeline.read(1000),null);
  timeline.push(Array.from({length:6},(_,i)=>({t:i*.02,q:yaw(i*.02)})),1000);
  for(const now of [1000,1005,1010,1020]){
    const expected=yaw(.1+(now-1000)/1000-.07);
    assert.ok(quaternionDistance(timeline.read(now),expected)<1e-7);
  }
  assert.equal(timeline.push([{t:.1,q:yaw(.1)}],9999),false);
  assert.ok(quaternionDistance(timeline.read(1010),yaw(.04))<1e-7,'duplicates cannot reset playback timing');
  assert.ok(quaternionDistance(timeline.read(999999),yaw(.1))<1e-7,'no extrapolation beyond last measured pose');
  assert.ok(quaternionDistance(timeline.read(0),yaw(0))<1e-7,'clamp before first measurement');
  assert.ok(quaternionDistance(timeline.read(1000,{immediate:true}),yaw(.1))<1e-7);
  timeline.clear();assert.equal(timeline.latest(),null);assert.equal(timeline.read(1000),null);
});

test('angular speed uses measured shortest quaternion arcs and rejects missing or stale pairs',()=>{
  const spin=Array.from({length:21},(_,i)=>{const t=i*.01;return {t,q:[0,0,Math.sin(Math.PI*t),Math.cos(Math.PI*t)]};});
  assert.ok(Math.abs(angularSpeedDegrees(spin)-360)<1e-6);
  spin.forEach((p,i)=>{if(i%2)p.q=p.q.map(v=>-v);});
  assert.ok(Math.abs(angularSpeedDegrees(spin)-360)<1e-6,'quaternion sign changes are not motion');
  assert.equal(angularSpeedDegrees([]),null);
  assert.equal(angularSpeedDegrees([{t:0,q:[0,0,0,1]},{t:1,q:[0,0,0,1]}]),null);
});

test('motion policy holds on strong acceleration or fast rotation and requires measured quiet time to resume',()=>{
  const guard=createMotionGuard(),steady={level:'steady',norm:9.81},strong={level:'uncertain',norm:61};
  const read=(time,evidence=steady,speed=0)=>guard.update({time,evidence,angularSpeedDegS:speed,rotationAvailable:true});
  assert.equal(read(0).paused,false);
  assert.equal(read(.05,{level:'uncertain',norm:50},500).paused,false,'movement between the previous and new limits does not freeze the model');
  assert.equal(read(.06,{level:'uncertain',norm:60},720).paused,false,'pause limits are strictly above 60 m/s² and 720°/s');
  assert.equal(read(.1,steady,800).paused,true,'very fast yaw is detected even with a quiet accelerometer');
  assert.equal(read(.2).settling,true);
  for(let i=0;i<20;i++)assert.equal(read(.2).paused,true,'repeated UI updates cannot invent quiet sensor time');
  assert.equal(read(.3).paused,true);
  assert.equal(read(.36).paused,false);
  assert.equal(read(1,strong,0).paused,true);
  assert.equal(read(1.1).settling,true);
  assert.equal(read(1.2,{level:'uncertain',norm:35}).settling,false,'hysteresis prevents resuming too close to the acceleration limit');
  assert.equal(read(2,{level:'uncertain',norm:25},150).paused,true);
  assert.equal(read(2.16,{level:'uncertain',norm:25},150).paused,false,'tracking resumes promptly even with some remaining movement');
  assert.equal(read(3,strong).paused,true);
  assert.equal(read(3.1,steady,null).settling,false,'missing fused data cannot certify quiet rotation');
  assert.equal(read(0).paused,false,'a new sensor clock resets previous holds');
});

test('gravity-only motion policy resumes without requiring an unavailable attitude stream',()=>{
  const guard=createMotionGuard();
  assert.equal(guard.update({time:0,evidence:{level:'uncertain',norm:60.01}}).paused,true);
  assert.equal(guard.update({time:1,evidence:{level:'steady',norm:9.81}}).paused,true);
  assert.equal(guard.update({time:1.16,evidence:{level:'steady',norm:9.81}}).paused,false);
  guard.reset();assert.equal(guard.update({time:2,evidence:{level:'steady',norm:9.81}}).paused,false);
});

test('motion hold needs continuously observed quiet time; a data gap restarts recovery',()=>{
  const guard=createMotionGuard(),quiet={level:'steady',norm:9.81};
  assert.equal(guard.update({time:0,evidence:{level:'uncertain',norm:61}}).paused,true);
  assert.equal(guard.update({time:.05,evidence:quiet}).settling,true);
  const afterGap=guard.update({time:10,evidence:quiet});
  assert.equal(afterGap.paused,true,'ten seconds without samples are not ten seconds of quiet');
  assert.equal(afterGap.settling,true);
  assert.equal(guard.update({time:10.1,evidence:quiet}).paused,true);
  assert.equal(guard.update({time:10.16,evidence:quiet}).paused,false,'resumes after 0.15 s of fresh quiet samples');
});
