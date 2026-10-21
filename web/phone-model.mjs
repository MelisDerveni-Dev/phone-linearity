/**
 * Authored visual approximation of the Galaxy S25 Ultra, not manufacturer CAD.
 * The body has the published 77.6 × 162.8 × 8.2 mm proportions at 2 CSS px/mm.
 * Small features are illustrative. No texture downloads or rendering libraries.
 *
 * setQuaternion([x,y,z,w]) accepts a standard active, right-handed rotation in
 * phone coordinates: +x screen-right, +y toward the top, +z out of the screen.
 * CSS has +y down, so we use C R C, C = diag(1,-1,1). Parent stages may apply a
 * fixed viewing/camera transform. This module does not interpolate sensor poses.
 */
export const PHONE_DIMENSIONS = Object.freeze({
  widthMm: 77.6, heightMm: 162.8, depthMm: 8.2, pixelsPerMm: 2,
  width: 155.2, height: 325.6, depth: 16.4,
});

/** CSS column-major 4×4 matrix; pure so the frame convention is testable. */
export function quaternionToCssMatrix(quaternion) {
  if ((!Array.isArray(quaternion) && !ArrayBuffer.isView(quaternion))
      || quaternion.length !== 4 || !Array.from(quaternion).every(Number.isFinite)) {
    throw new TypeError('Phone orientation must be a finite [x, y, z, w] quaternion.');
  }
  // Scale first: a finite quaternion can have a norm larger than Number.MAX_VALUE.
  // The same normalization also accepts tiny nonzero representations accurately.
  const scale = Math.max(...Array.from(quaternion, Math.abs));
  if (scale === 0) throw new RangeError('Phone orientation quaternion has zero length.');
  const scaled = Array.from(quaternion, value => value / scale);
  const norm = Math.hypot(...scaled);
  const [x, y, z, w] = scaled.map(value => value / norm);
  const r00 = 1 - 2 * (y * y + z * z);
  const r01 = 2 * (x * y - z * w);
  const r02 = 2 * (x * z + y * w);
  const r10 = 2 * (x * y + z * w);
  const r11 = 1 - 2 * (x * x + z * z);
  const r12 = 2 * (y * z - x * w);
  const r20 = 2 * (x * z - y * w);
  const r21 = 2 * (y * z + x * w);
  const r22 = 1 - 2 * (x * x + y * y);
  return [r00, -r10, r20, 0, -r01, r11, -r21, 0,
    r02, -r12, r22, 0, 0, 0, 0, 1].map(value => Math.abs(value) < 1e-14 ? 0 : value);
}

let modelSequence = 0;

const element = (document, className, parent) => {
  const node = document.createElement('div');
  node.className = className;
  parent?.append(node);
  return node;
};

function addFrame(document, pivot) {
  const { width, height, depth } = PHONE_DIMENSIONS;
  const radius = 8;
  for (const [side, x, rotation] of [['right', width / 2, 90], ['left', -width / 2, -90]]) {
    const face = element(document, `pm-edge pm-edge-${side}`, pivot);
    face.style.width = `${depth}px`;
    face.style.height = `${height - 2 * radius}px`;
    face.style.transform = `translate3d(${x}px,0,0) rotateY(${rotation}deg)`;
  }
  for (const [side, y, rotation] of [['top', -height / 2, 90], ['bottom', height / 2, -90]]) {
    const face = element(document, `pm-edge pm-edge-${side}`, pivot);
    face.style.width = `${width - 2 * radius}px`;
    face.style.height = `${depth}px`;
    face.style.transform = `translate3d(0,${y}px,0) rotateX(${rotation}deg)`;
  }
  // Quarter cylinders close the real rounded outline rather than leaving gaps
  // between the front/back faces and a square six-face box.
  const segments = 8;
  for (let corner = 0; corner < 4; corner++) {
    const centerX = (corner === 0 || corner === 3 ? 1 : -1) * (width / 2 - radius);
    const centerY = (corner < 2 ? 1 : -1) * (height / 2 - radius);
    const delta = Math.PI / (2 * segments);
    for (let i = 0; i < segments; i++) {
      const angle = corner * Math.PI / 2 + (i + .5) * delta;
      const face = element(document, 'pm-corner', pivot);
      face.style.width = `${2 * radius * Math.sin(delta / 2) + .12}px`;
      face.style.height = `${depth}px`;
      face.style.transform = `translate3d(${centerX + radius * Math.cos(angle)}px,${centerY + radius * Math.sin(angle)}px,0) rotateZ(${angle * 180 / Math.PI + 90}deg) rotateX(90deg)`;
      const light = Math.round(157 + 41 * Math.cos(angle - 2.4));
      face.style.background = `linear-gradient(to bottom, rgb(${light + 22} ${light + 20} ${light + 14}),rgb(${light} ${light - 2} ${light - 6}) 38%,rgb(${light + 9} ${light + 7} ${light + 2}) 68%,rgb(${light - 12} ${light - 13} ${light - 16}))`;
    }
  }
}

function addCamera(document, back, { x, y, diameter, depth = 3.4, kind = 'main' }) {
  const camera = element(document, `pm-camera pm-camera-${kind}`, back);
  Object.assign(camera.style, {
    width: `${diameter}px`, height: `${diameter}px`, left: `${x}px`, top: `${y}px`,
  });
  const segments = 20;
  const radius = diameter / 2;
  for (let index = 0; index < segments; index++) {
    const angle = (index + .5) * 2 * Math.PI / segments;
    const wall = element(document, 'pm-camera-wall', camera);
    wall.style.width = `${2 * radius * Math.sin(Math.PI / segments) + .15}px`;
    wall.style.height = `${depth}px`;
    wall.style.transform = `translate3d(${radius + radius * Math.cos(angle)}px,${radius + radius * Math.sin(angle)}px,${depth / 2}px) rotateZ(${angle * 180 / Math.PI + 90}deg) rotateX(90deg)`;
    wall.style.backgroundColor = `hsl(45 3% ${14 + Math.round(11 * (.5 + .5 * Math.cos(angle - 2.2)))}%)`;
  }
  const cap = element(document, 'pm-camera-cap', camera);
  cap.style.transform = `translateZ(${depth}px)`;
  element(document, 'pm-camera-glass', cap);
  if (kind === 'main') element(document, 'pm-camera-reflection', cap);
}

function addDetails(document, pivot) {
  for (const [kind, y, height] of [['volume', -81, 36], ['power', -37, 19]]) {
    const button = element(document, `pm-side-button pm-${kind}`, pivot);
    Object.assign(button.style, { height: `${height}px`, transform: `translate3d(78.15px,${y}px,0) rotateY(90deg)` });
  }
  const bottom = element(document, 'pm-bottom-details', pivot);
  bottom.style.transform = 'translate3d(0,162.93px,0) rotateX(-90deg)';
  element(document, 'pm-usbc', bottom);
  element(document, 'pm-spen', bottom);
  for (let index = 0; index < 5; index++) {
    const hole = element(document, 'pm-speaker-hole', bottom);
    hole.style.left = `${27 + index * 4.5}px`;
  }
  const mic = element(document, 'pm-top-mic', pivot);
  mic.style.transform = 'translate3d(38px,-162.93px,0) rotateX(90deg)';
  for (const [x, y, z] of [[77.72, -139, 0], [77.72, 135, 0], [-77.72, -139, 0], [-77.72, 135, 0]]) {
    const antenna = element(document, 'pm-antenna', pivot);
    antenna.style.transform = `translate3d(${x}px,${y}px,${z}px) rotateY(${x > 0 ? 90 : -90}deg)`;
  }
}

/** Host remains owned by the caller; its own transforms are never replaced. */
export function createPhoneModel(host) {
  if (!host?.ownerDocument || typeof host.append !== 'function') throw new TypeError('A phone model host element is required.');
  const document = host.ownerDocument;
  if (!document.querySelector('link[data-affine-phone-model]')) {
    const stylesheet = document.createElement('link');
    stylesheet.rel = 'stylesheet';
    stylesheet.href = new URL('./phone-model.css', import.meta.url).href;
    stylesheet.dataset.affinePhoneModel = '';
    document.head.append(stylesheet);
  }
  const root = element(document, 'phone-model-root', host);
  root.setAttribute('role', 'img');
  root.setAttribute('aria-label', 'Illustrative Samsung Galaxy S25 Ultra model. Phone pose is supplied by the orientation viewer.');
  const pivot = element(document, 'pm-pivot', root);
  pivot.setAttribute('aria-hidden', 'true');
  addFrame(document, pivot);
  const back = element(document, 'pm-face pm-back', pivot);
  element(document, 'pm-back-sheen', back);
  const wordmark = element(document, 'pm-samsung', back);
  wordmark.textContent = 'SAMSUNG';
  const model = element(document, 'pm-back-inscription', back);
  model.textContent = 'GALAXY S25 ULTRA';
  // Four rear cameras: three large left lenses and the smaller right telephoto.
  // The fifth dark circle is a laser-autofocus sensor, not a fifth camera.
  for (const camera of [
    { x: 16, y: 24, diameter: 27 }, { x: 16, y: 66, diameter: 27 }, { x: 16, y: 108, diameter: 27 },
    { x: 54, y: 30, diameter: 15, depth: 1.8, kind: 'sensor' },
    { x: 51, y: 69, diameter: 21, depth: 3.1, kind: 'telephoto' },
  ]) addCamera(document, back, camera);
  element(document, 'pm-flash', back);
  const front = element(document, 'pm-face pm-front', pivot);
  const screen = element(document, 'pm-screen', front);
  const wallpaper = element(document, 'pm-wallpaper', screen);
  const gradientId = `pm-arc-${++modelSequence}`;
  wallpaper.innerHTML = `<svg viewBox="0 0 150 320" aria-hidden="true"><defs><linearGradient id="${gradientId}" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#bba47a" stop-opacity=".44"/><stop offset="1" stop-color="#6b9582" stop-opacity=".09"/></linearGradient></defs><g fill="none" stroke="url(#${gradientId})" stroke-width=".6"><circle cx="130" cy="215" r="113"/><circle cx="130" cy="215" r="101"/><circle cx="130" cy="215" r="82"/><circle cx="130" cy="215" r="58"/><path d="M17 215h226M130 102v226M50 135l160 160M50 295l160-160"/><circle cx="16" cy="91" r="54"/><circle cx="16" cy="91" r="42"/></g></svg>`;
  const screenLabel = element(document, 'pm-screen-label', screen);
  screenLabel.textContent = 'THE AFFINE OBSERVATORY';
  const screenMark = element(document, 'pm-screen-mark', screen);
  screenMark.textContent = 'Observe.';
  element(document, 'pm-home-indicator', screen);
  element(document, 'pm-front-camera', front);
  element(document, 'pm-earpiece', front);
  addDetails(document, pivot);
  let disposed = false;
  const setQuaternion = quaternion => {
    const matrix = quaternionToCssMatrix(quaternion);
    if (!disposed) pivot.style.transform = `translate(-50%,-50%) matrix3d(${matrix.join(',')})`;
  };
  const reset = () => setQuaternion([0, 0, 0, 1]);
  reset();
  return { setQuaternion, reset, dispose() { disposed = true; root.remove(); } };
}
