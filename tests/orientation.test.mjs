import test from 'node:test';
import assert from 'node:assert/strict';
import {gravityQuaternion,normalizeQuaternion,slerpQuaternion,quaternionDistance,motionEvidence} from '../web/orientation.mjs';

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
