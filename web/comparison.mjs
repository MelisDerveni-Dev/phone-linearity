export function tiltDegrees(vector, axis = 'x') {
  if (!Array.isArray(vector) || vector.length !== 3 || !vector.every(Number.isFinite) || Math.hypot(...vector) < 1e-9) return null;
  const k = axis === 'y' ? 1 : 0;
  return Math.atan2(vector[k], Math.hypot(...vector.filter((_, i) => i !== k))) * 180 / Math.PI;
}

export function component(vector, focus = 'tilt', tiltAxis = 'x') {
  if (focus === 'tilt') return tiltDegrees(vector, tiltAxis);
  const index = ['x', 'y', 'z'].indexOf(focus);
  return index >= 0 && Number.isFinite(vector?.[index]) ? vector[index] : null;
}

export function compareSample(point, focus, tiltAxis, reference = null) {
  const raw = component(point?.raw, focus, tiltAxis);
  const corrected = component(point?.corrected, focus, tiltAxis);
  if (raw === null || corrected === null) return null;
  const validReference = Number.isFinite(reference);
  return { raw, corrected, delta: corrected - raw,
    rawError: validReference ? raw - reference : null,
    correctedError: validReference ? corrected - reference : null,
    errorReduction: validReference ? Math.abs(raw - reference) - Math.abs(corrected - reference) : null };
}
