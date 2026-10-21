import test from 'node:test';
import assert from 'node:assert/strict';
import { PHONE_DIMENSIONS, quaternionToCssMatrix } from '../web/phone-model.mjs';

function near(actual, expected, tolerance = 1e-12) {
  assert.equal(actual.length, expected.length);
  actual.forEach((value, index) => assert.ok(
    Math.abs(value - expected[index]) < tolerance,
    `coordinate ${index}: expected ${expected[index]}, received ${value}`,
  ));
}

// CSS matrix3d is column-major. These are the rendered screen-right, screen-down
// and screen-front vectors, before the stage's fixed viewing transform.
function apply(matrix, vector) {
  return [0, 1, 2].map(row => matrix[row] * vector[0]
    + matrix[4 + row] * vector[1] + matrix[8 + row] * vector[2]);
}

test('phone model preserves the published body proportions and millimetre scale', () => {
  assert.deepEqual([PHONE_DIMENSIONS.widthMm, PHONE_DIMENSIONS.heightMm, PHONE_DIMENSIONS.depthMm], [77.6, 162.8, 8.2]);
  assert.equal(PHONE_DIMENSIONS.width, PHONE_DIMENSIONS.widthMm * PHONE_DIMENSIONS.pixelsPerMm);
  assert.equal(PHONE_DIMENSIONS.height, PHONE_DIMENSIONS.heightMm * PHONE_DIMENSIONS.pixelsPerMm);
  assert.equal(PHONE_DIMENSIONS.depth, PHONE_DIMENSIONS.depthMm * PHONE_DIMENSIONS.pixelsPerMm);
  assert.ok(Object.isFrozen(PHONE_DIMENSIONS));
});

test('identity quaternion has no translation or perspective and leaves the phone basis unchanged', () => {
  near(quaternionToCssMatrix([0, 0, 0, 1]), [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);
});

test('positive yaw rotates screen-right toward phone top after the CSS Y reflection', () => {
  const matrix = quaternionToCssMatrix([0, 0, Math.SQRT1_2, Math.SQRT1_2]);
  near(apply(matrix, [1, 0, 0]), [0, -1, 0]);
  near(apply(matrix, [0, -1, 0]), [-1, 0, 0]);
  near(apply(matrix, [0, 0, 1]), [0, 0, 1]);
});

test('phone X and Y rotations put the front and top in the correct directions', () => {
  const s = Math.SQRT1_2;
  const aroundX = quaternionToCssMatrix([s, 0, 0, s]);
  near(apply(aroundX, [0, -1, 0]), [0, 0, 1]);
  near(apply(aroundX, [0, 0, 1]), [0, 1, 0]);
  const aroundY = quaternionToCssMatrix([0, s, 0, s]);
  near(apply(aroundY, [0, 0, 1]), [1, 0, 0]);
  near(apply(aroundY, [1, 0, 0]), [0, 0, -1]);
});

test('combined rotation preserves lengths, orthogonality and handedness', () => {
  const matrix = quaternionToCssMatrix([.5, .5, .5, .5]);
  const right = apply(matrix, [1, 0, 0]);
  const down = apply(matrix, [0, 1, 0]);
  const front = apply(matrix, [0, 0, 1]);
  near(right, [0, -1, 0]);
  near(down, [0, 0, -1]);
  near(front, [1, 0, 0]);
  assert.ok(Math.abs(Math.hypot(...right) - 1) < 1e-12);
  assert.ok(Math.abs(right.reduce((sum, value, index) => sum + value * down[index], 0)) < 1e-12);
  near([
    right[1] * down[2] - right[2] * down[1],
    right[2] * down[0] - right[0] * down[2],
    right[0] * down[1] - right[1] * down[0],
  ], front);
});

test('normalization accepts equivalent scaled, huge, tiny, typed and sign-reversed quaternions', () => {
  const expected = quaternionToCssMatrix([.5, .5, .5, .5]);
  for (const q of [[5, 5, 5, 5], [-.5, -.5, -.5, -.5],
    [Number.MAX_VALUE, Number.MAX_VALUE, Number.MAX_VALUE, Number.MAX_VALUE],
    [Number.MIN_VALUE, Number.MIN_VALUE, Number.MIN_VALUE, Number.MIN_VALUE],
    new Float64Array([.5, .5, .5, .5])]) {
    near(quaternionToCssMatrix(q), expected);
    assert.ok(quaternionToCssMatrix(q).every(Number.isFinite));
  }
});

test('invalid and zero quaternions are rejected instead of producing a plausible pose', () => {
  for (const value of [null, {}, '0001', [0, 0, 1], [0, 0, 0, 1, 2],
    [0, NaN, 0, 1], [0, 0, Infinity, 1], [0, 0, 0, '1']]) {
    assert.throws(() => quaternionToCssMatrix(value), TypeError);
  }
  assert.throws(() => quaternionToCssMatrix([0, 0, 0, 0]), RangeError);
});
