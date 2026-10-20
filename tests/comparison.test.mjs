import test from 'node:test';
import assert from 'node:assert/strict';
import {tiltDegrees,component,compareSample} from '../web/comparison.mjs';

test('signed inclination uses the selected phone direction and rejects an undefined direction',()=>{
  assert.equal(tiltDegrees([0,0,9.81]),0);
  assert.equal(tiltDegrees([9.81,0,0]),90);
  assert.ok(Math.abs(tiltDegrees([-1,0,1])+45)<1e-12);
  assert.ok(Math.abs(tiltDegrees([0,1,1],'y')-45)<1e-12);
  assert.equal(tiltDegrees([0,0,0]),null);
  assert.equal(tiltDegrees([NaN,0,1]),null);
  assert.equal(component([1,2,3],'z'),3);
});

test('a correction is not an error reduction without an independent reference',()=>{
  const p={raw:[1,0,9.81],corrected:[.5,0,9.81]};
  const result=compareSample(p,'x','x');
  assert.equal(result.delta,-.5);assert.equal(result.rawError,null);assert.equal(result.errorReduction,null);
  const good=compareSample(p,'x','x',0);
  assert.equal(good.rawError,1);assert.equal(good.correctedError,.5);assert.equal(good.errorReduction,.5);
  const worse=compareSample(p,'x','x',2);
  assert.equal(worse.errorReduction,-.5);
});

test('identity calibration has zero applied correction and zero error reduction',()=>{
  const p={raw:[2,3,9.5],corrected:[2,3,9.5]};
  const r=compareSample(p,'tilt','x',7);
  assert.equal(r.delta,0);assert.equal(r.errorReduction,0);
  assert.equal(compareSample({raw:[0,0,0],corrected:[0,0,0]},'tilt','x'),null);
});
