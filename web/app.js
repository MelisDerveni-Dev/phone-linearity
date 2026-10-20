/* Both windows read the same local bridge. No phone data leaves this machine. */
const $ = (id) => document.getElementById(id);
const AXES = [
  { key: 'x', label: 'X', color: '#347e75' },
  { key: 'y', label: 'Y', color: '#b46147' },
  { key: 'z', label: 'Z', color: '#8e743c' },
];
const IDENTITY = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
let state = { source: 'none', connected: false, points: [], calibration: {} };
let requestPending = false;
let pollPending = false;
let bridgeUnavailable = false;
let hoverTime = null;
const chartGeometry = new WeakMap();
let drawRequested = false;
let lastRevision = null;

if (new URLSearchParams(location.search).get('display') === '1') {
  document.body.classList.add('display-mode');
  document.title = 'Live observatory · Is your phone linear?';
}

function setText(id, value) {
  const element = $(id);
  if (element && element.textContent !== value) element.textContent = value;
}

function setButtonLabel(id, value) {
  const button = $(id);
  const label = button?.querySelector('span:last-child') || button;
  if (label && label.textContent !== value) label.textContent = value;
}

function showError(message) {
  if (!$('error-banner')) return;
  $('error-banner').textContent = message || '';
  $('error-banner').hidden = !message;
}

async function api(path, body) {
  const response = await fetch(path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: 'no-store',
    signal: AbortSignal.timeout(12000),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status}).`);
  return payload;
}

function receive(payload) {
  const next = payload.state || payload;
  if (!Array.isArray(next.points)) return;
  if (bridgeUnavailable || (state.error && !next.error && $('error-banner')?.textContent === state.error)) showError('');
  state = next;
  if (!Array.isArray(state.points)) state.points = [];
  bridgeUnavailable = false;
  updateReadouts();
  requestDraw();
}

async function action(path, body) {
  if (requestPending) return;
  requestPending = true;
  showError('');
  updateReadouts();
  try {
    receive(await api(path, body));
    await poll();
  } catch (error) {
    showError(error.message);
  } finally {
    requestPending = false;
    updateReadouts();
  }
}

async function poll() {
  if (pollPending) return;
  pollPending = true;
  try {
    receive(await api('/api/state'));
  } catch (error) {
    bridgeUnavailable = true;
    updateReadouts();
    showError(`The local bridge is unavailable. Keep the launcher running. ${error.message}`);
  } finally {
    pollPending = false;
  }
}

function isIdentity(calibration) {
  return Array.isArray(calibration.S) && calibration.S.length === 3
    && calibration.S.every((row, i) => Array.isArray(row) && row.length === 3
      && row.every((value, j) => value === IDENTITY[i][j]))
    && Array.isArray(calibration.b) && calibration.b.length === 3
    && calibration.b.every((value) => value === 0);
}

function number(value, decimals = 3) {
  return Number.isFinite(value) ? value.toFixed(decimals) : '—';
}

function rate() {
  const points = state.points;
  if (points.length < 2) return null;
  const last = points.length - 1;
  const first = Math.max(0, last - 200);
  const duration = points[last].t - points[first].t;
  return duration > 0 ? (last - first) / duration : null;
}

function updateReadouts() {
  const points = state.points;
  const latest = points.at(-1);
  const synthetic = state.source === 'synthetic';
  const phone = state.connected && state.source === 'phone';
  const age = state.lastReceivedAt ? Math.max(0, Date.now() - state.lastReceivedAt) : null;
  let status = 'idle';
  let label = 'Ready for your experiment';
  if (bridgeUnavailable) { status = 'error'; label = 'Local bridge offline'; }
  else if (state.error && phone) { status = 'error'; label = 'Phone connection interrupted'; }
  else if (synthetic) { status = 'preview'; label = 'Synthetic preview running'; }
  else if (phone && state.measuring === false) { status = 'paused'; label = 'Phone connected · paused'; }
  else if (phone && !latest) { status = 'waiting'; label = 'Connected · waiting for samples'; }
  else if (phone && (age === null || age > 2500)) { status = 'stale'; label = 'Phone connected · stream stale'; }
  else if (phone) { status = 'live'; label = 'Live from your phone'; }
  else if (latest) { status = 'paused'; label = 'Disconnected · retained samples'; }

  if ($('connection-status')) $('connection-status').dataset.state = status;
  document.body.dataset.streamState = status;
  setText('connection-label', label);
  setText('source-label', synthetic ? 'SYNTHETIC PREVIEW · generated data'
    : state.source === 'phone' ? 'PHONE · acceleration including g' : 'No source connected');
  setText('sample-count', Number(state.count ?? points.length).toLocaleString());
  setText('sample-rate', latest ? number(rate(), 1) : '—');
  setText('latency-value', phone && Number.isFinite(state.latencyMs) ? String(Math.round(state.latencyMs)) : '—');
  setText('last-value', age === null ? 'Awaiting data' : age < 1000 ? 'Just now'
    : `${Math.floor(age / 1000)} s ago`);

  AXES.forEach(({ key }, index) => {
    setText(`raw-${key}`, number(latest?.raw?.[index]));
    setText(`corrected-${key}`, number(latest?.corrected?.[index]));
  });
  const norm = (values) => Array.isArray(values) ? Math.hypot(...values) : null;
  setText('raw-norm', number(norm(latest?.raw)));
  setText('corrected-norm', number(norm(latest?.corrected)));

  const calibration = state.calibration || {};
  const identity = isIdentity(calibration);
  setText('calibration-name', calibration.name || 'Identity transform');
  setText('calibration-status', identity || !calibration.S ? 'Identity · uncalibrated'
    : calibration.fitted === true && calibration.provenance ? 'Fitted calibration · verify on held-out data'
      : 'Imported transform · unverified');
  document.body.dataset.calibrated = String(!identity && !!calibration.S);
  if ($('preview-button')) {
    $('preview-button').setAttribute('aria-pressed', String(synthetic));
    setButtonLabel('preview-button', synthetic ? 'Stop synthetic preview' : 'Synthetic preview');
  }
  ['connect-button', 'disconnect-button', 'phone-start', 'phone-stop', 'preview-button', 'calibration-reset', 'calibration-file'].forEach((id) => {
    if ($(id)) $(id).disabled = requestPending;
  });
  if ($('disconnect-button')) $('disconnect-button').disabled = requestPending || !state.connected;
  if ($('phone-start')) $('phone-start').disabled = requestPending || !phone;
  if ($('phone-stop')) $('phone-stop').disabled = requestPending || !phone;
  if ($('calibration-reset')) $('calibration-reset').disabled = requestPending || identity || !calibration.S;
  ['raw-empty', 'calibrated-empty'].forEach((id) => { if ($(id)) $(id).hidden = !!latest; });
  if (state.error && !requestPending) showError(state.error);
  if (lastRevision !== state.revision) {
    lastRevision = state.revision;
    requestDraw();
  }
}

function selectedAxes() {
  return AXES.map((axis, index) => ({ ...axis, index })).filter(({ key }) => !$(`axis-${key}`) || $(`axis-${key}`).checked);
}

function viewport() {
  const duration = Number($('time-window')?.value || 10);
  const points = state.points;
  const latest = points.at(-1)?.t || 0;
  const end = Math.max(duration, latest);
  const start = end - duration;
  const axes = selectedAxes();
  const visible = points.filter((point) => point.t >= start && point.t <= end);
  let extent = 12;
  if ($('scale-mode')?.value === 'fixed') extent = 20;
  else {
    let maximum = 0;
    for (const point of visible) {
      for (const { index } of axes) {
        maximum = Math.max(maximum, Math.abs(point.raw?.[index] || 0), Math.abs(point.corrected?.[index] || 0));
      }
    }
    if (maximum > 0) {
      const target = Math.max(1, maximum * 1.15);
      const magnitude = 10 ** Math.floor(Math.log10(target));
      extent = Math.ceil(target / magnitude * 2) / 2 * magnitude;
    }
  }
  return { start, end, duration, extent, axes, visible };
}

function requestDraw() {
  if (drawRequested) return;
  drawRequested = true;
  requestAnimationFrame(() => {
    drawRequested = false;
    const view = viewport();
    drawChart($('raw-chart'), 'raw', view);
    drawChart($('calibrated-chart'), 'corrected', view);
  });
}

function drawChart(canvas, field, view) {
  if (!canvas) return;
  const bounds = canvas.getBoundingClientRect();
  if (bounds.width < 1 || bounds.height < 1) return;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  if (canvas.width !== Math.round(bounds.width * dpr) || canvas.height !== Math.round(bounds.height * dpr)) {
    canvas.width = Math.round(bounds.width * dpr);
    canvas.height = Math.round(bounds.height * dpr);
  }
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const w = bounds.width;
  const h = bounds.height;
  const pad = { left: 49, right: 17, top: 28, bottom: 34 };
  const pw = Math.max(1, w - pad.left - pad.right);
  const ph = Math.max(1, h - pad.top - pad.bottom);
  chartGeometry.set(canvas, { pad, pw, width: w, ...view });
  const px = (t) => pad.left + ((t - view.start) / view.duration) * pw;
  const py = (v) => pad.top + (1 - (v + view.extent) / (2 * view.extent)) * ph;
  ctx.clearRect(0, 0, w, h);
  ctx.font = '10px ui-monospace, SFMono-Regular, Consolas, monospace';
  ctx.textBaseline = 'middle';
  ctx.lineWidth = 1;
  for (let step = 0; step <= 4; step++) {
    const value = view.extent * (1 - step / 2);
    const y = py(value);
    ctx.strokeStyle = step === 2 ? 'rgba(38,62,57,.23)' : 'rgba(38,62,57,.09)';
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
    ctx.fillStyle = '#6e7971';
    ctx.textAlign = 'right';
    ctx.fillText(number(value, view.extent >= 10 ? 0 : 1), pad.left - 10, y);
  }
  const divisions = w < 420 ? 4 : 5;
  for (let step = 0; step <= divisions; step++) {
    const t = view.start + view.duration * step / divisions;
    const x = px(t);
    ctx.strokeStyle = 'rgba(38,62,57,.07)';
    ctx.beginPath(); ctx.moveTo(x, pad.top); ctx.lineTo(x, h - pad.bottom); ctx.stroke();
    ctx.fillStyle = '#6e7971';
    ctx.textAlign = 'center';
    ctx.fillText(`${t.toFixed(view.duration < 10 ? 1 : 0)}s`, x, h - 15);
  }
  ctx.save();
  ctx.beginPath(); ctx.rect(pad.left, pad.top, pw, ph); ctx.clip();
  for (const axis of view.axes) {
    ctx.beginPath();
    let previous = null;
    let count = 0;
    for (const point of view.visible) {
      const value = point[field]?.[axis.index];
      if (!Number.isFinite(value)) { previous = null; continue; }
      const x = px(point.t);
      const y = py(value);
      if (previous === null || point.t - previous > 1) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
      previous = point.t;
      count++;
    }
    ctx.strokeStyle = axis.color;
    ctx.lineWidth = 1.65;
    ctx.lineJoin = 'round';
    ctx.stroke();
    const latest = view.visible.at(-1);
    if (latest && count && Number.isFinite(latest[field]?.[axis.index])) {
      ctx.fillStyle = axis.color;
      ctx.beginPath(); ctx.arc(px(latest.t), py(latest[field][axis.index]), 2.7, 0, 2 * Math.PI); ctx.fill();
    }
  }
  ctx.restore();

  if (hoverTime !== null && view.visible.length) {
    let nearest = view.visible[0];
    for (const point of view.visible) if (Math.abs(point.t - hoverTime) < Math.abs(nearest.t - hoverTime)) nearest = point;
    const cursorX = px(nearest.t);
    ctx.strokeStyle = 'rgba(38,62,57,.4)';
    ctx.setLineDash([3, 4]);
    ctx.beginPath(); ctx.moveTo(cursorX, pad.top); ctx.lineTo(cursorX, h - pad.bottom); ctx.stroke();
    ctx.setLineDash([]);
    const tooltipWidth = Math.min(174, pw);
    const tooltipX = Math.min(w - pad.right - tooltipWidth, Math.max(pad.left, cursorX + 10));
    const tooltipHeight = 27 + view.axes.length * 17;
    ctx.fillStyle = 'rgba(255,253,247,.97)';
    ctx.fillRect(tooltipX, pad.top + 6, tooltipWidth, tooltipHeight);
    ctx.strokeStyle = 'rgba(38,62,57,.25)';
    ctx.strokeRect(tooltipX, pad.top + 6, tooltipWidth, tooltipHeight);
    ctx.textAlign = 'left'; ctx.fillStyle = '#263e39';
    ctx.fillText(`t = ${number(nearest.t)} s`, tooltipX + 9, pad.top + 21);
    view.axes.forEach((axis, index) => {
      ctx.fillStyle = axis.color;
      ctx.fillText(`${axis.label}  ${number(nearest[field]?.[axis.index])} m/s²`, tooltipX + 9, pad.top + 39 + index * 17);
    });
  }
}

$('connect-form')?.addEventListener('submit', (event) => {
  event.preventDefault();
  const url = $('phone-url')?.value.trim();
  if (!url) { showError('Enter the remote access address displayed by phyphox.'); return; }
  action('/api/connect', { url });
});
$('disconnect-button')?.addEventListener('click', () => action('/api/disconnect', {}));
$('phone-start')?.addEventListener('click', () => action('/api/control', { cmd: 'start' }));
$('phone-stop')?.addEventListener('click', () => action('/api/control', { cmd: 'stop' }));
$('preview-button')?.addEventListener('click', () => action('/api/preview', { enabled: state.source !== 'synthetic' }));
$('calibration-reset')?.addEventListener('click', () => action('/api/calibration', {
  name: 'Identity transform', fitted: false, S: IDENTITY, b: [0, 0, 0], units: 'm/s^2',
}));
$('calibration-file')?.addEventListener('change', async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    if (file.size > 1024 * 1024) throw new Error('Calibration JSON must be smaller than 1 MB.');
    const calibration = JSON.parse(await file.text());
    await action('/api/calibration', { ...calibration, name: calibration.name || file.name });
  } catch (error) { showError(`Cannot load calibration: ${error.message}`); }
  finally { event.target.value = ''; }
});
$('popout-button')?.addEventListener('click', () => {
  const display = window.open('/?display=1', 'accelerometer-observatory', 'popup,width=1500,height=900');
  if (display) display.focus();
  else showError('Allow pop-up windows for localhost to open the separate graph display.');
});
$('fullscreen-button')?.addEventListener('click', async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch (error) { showError(`Fullscreen is unavailable: ${error.message}`); }
});
document.addEventListener('fullscreenchange', () => {
  setButtonLabel('fullscreen-button', document.fullscreenElement ? 'Exit full screen' : 'Full screen');
  requestDraw();
});
['time-window', 'scale-mode', 'axis-x', 'axis-y', 'axis-z'].forEach((id) => $(id)?.addEventListener('change', requestDraw));
['raw-chart', 'calibrated-chart'].forEach((id) => {
  const canvas = $(id);
  if (!canvas) return;
  canvas.addEventListener('pointermove', (event) => {
    const geometry = chartGeometry.get(canvas);
    if (!geometry) return;
    const rect = canvas.getBoundingClientRect();
    const { pad, pw, start, duration } = geometry;
    hoverTime = start + Math.max(0, Math.min(1, (event.clientX - rect.left - pad.left) / pw)) * duration;
    requestDraw();
  });
  canvas.addEventListener('pointerleave', () => { hoverTime = null; requestDraw(); });
  if ('ResizeObserver' in window) new ResizeObserver(requestDraw).observe(canvas);
});
window.addEventListener('resize', requestDraw);
document.addEventListener('visibilitychange', () => { if (!document.hidden) poll(); });
updateReadouts();
requestDraw();
poll();
setInterval(() => { if (!document.hidden) poll(); }, 250);
setInterval(updateReadouts, 1000);
