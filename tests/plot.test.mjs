import test from 'node:test';
import assert from 'node:assert/strict';
import {lowerBound,mergeUpdate,traceForPixels} from '../web/plot.mjs';

const point=(t,x=0)=>({t,raw:[x,1,9.81],corrected:[x,1,9.81]});

test('incremental updates retain measured samples and replace them on a new epoch',()=>{
  const initial=mergeUpdate({points:[]},{epoch:'A',append:false,cursor:2,points:[point(0),point(1)]});
  const next=mergeUpdate(initial,{epoch:'A',append:true,cursor:3,points:[point(2,7)]});
  assert.deepEqual(next.points.map(p=>p.t),[0,1,2]);
  assert.equal(next.points[2].raw[0],7);
  assert.equal(mergeUpdate(next,{...next,points:[],append:true}).points,next.points,'metadata-only events reuse history');
  assert.throws(()=>mergeUpdate(next,{epoch:'B',append:true,points:[]}));
  assert.equal(mergeUpdate(next,{epoch:'B',append:false,points:[]}).points.length,0);
});

test('client history stays bounded and time lookup includes a boundary sample',()=>{
  const state=mergeUpdate({points:[]},{epoch:'A',append:false,points:Array.from({length:101},(_,i)=>point(i))});
  assert.equal(state.points[0].t,68);
  assert.equal(lowerBound(state.points,90.5),23);
  assert.equal(lowerBound([],1),0);
});

test('pixel reduction preserves narrow positive and negative spikes and their time order',()=>{
  const points=Array.from({length:10000},(_,i)=>point(i/1000,Math.sin(i/100)));
  points[5001].raw[0]=97;points[5002].raw[0]=-83;
  const trace=traceForPixels(points,'raw',0,400,0,10);
  assert.doesNotThrow(()=>traceForPixels(points,'raw',0,400,.001,10),'a boundary sample before the viewport must render');
  assert.ok(trace.length<=4*401);
  assert.ok(trace.some(([t,v])=>t===5.001&&v===97));
  assert.ok(trace.some(([t,v])=>t===5.002&&v===-83));
  for(let i=1;i<trace.length;i++)assert.ok(trace[i][0]>trace[i-1][0]);
  const original=new Map(points.map(p=>[p.t,p.raw[0]]));
  for(const [t,v] of trace)assert.equal(v,original.get(t),'drawn values must be actual measured values');
});
