import { tiltDegrees, compareSample } from './comparison.mjs';
import { traceForPixels } from './plot.mjs';

const $ = id => document.getElementById(id);
const STORAGE = 'affine-observatory.presentation.v1';
const defaults = () => ({focus:'tilt',tiltAxis:'x',mode:'correction',duration:10,references:{tilt:null,x:null,y:null,z:null},active:null});
const fmt = (value, digits=3) => Number.isFinite(value) ? value.toFixed(digits) : '—';
function text(id,value){const el=$(id);if(el&&el.textContent!==value)el.textContent=value;}

function readSettings() {
  const cfg=defaults();
  try {
    const saved=JSON.parse(localStorage.getItem(STORAGE));
    if(!saved)return cfg;
    if(['tilt','x','y','z'].includes(saved.focus))cfg.focus=saved.focus;
    if(['x','y'].includes(saved.tiltAxis))cfg.tiltAxis=saved.tiltAxis;
    if(['signal','correction','error'].includes(saved.mode))cfg.mode=saved.mode;
    if([5,10,20,30].includes(saved.duration))cfg.duration=saved.duration;
    for(const key of ['tilt','x','y','z'])if(Number.isFinite(saved.references?.[key])&&(key!=='tilt'||Math.abs(saved.references[key])<=90))cfg.references[key]=saved.references[key];
    if(typeof saved.active?.epoch==='string'&&Number.isFinite(saved.active.since))cfg.active={epoch:saved.active.epoch,since:saved.active.since};
  }catch{/* Storage is optional; private browsing still works. */}
  return cfg;
}

function dialMarkup(id) {
  let ticks='';
  for(let a=-90;a<=90;a+=15){const r=a*Math.PI/180;const x=180+Math.sin(r)*125,y=164-Math.cos(r)*125;const length=a%30===0?11:6;
    ticks+=`<line class="dial-tick ${a%30===0?'major':''}" x1="${x}" y1="${y}" x2="${180+Math.sin(r)*(125-length)}" y2="${164-Math.cos(r)*(125-length)}"/>`;
  }
  return `<svg viewBox="0 0 360 190"><path class="dial-ring" d="M40 164 A140 140 0 0 1 320 164"/><path class="dial-arc" d="M55 164 A125 125 0 0 1 305 164"/>${ticks}<text class="dial-label" x="29" y="181">−90°</text><text class="dial-label" x="173" y="14">0°</text><text class="dial-label" x="305" y="181">+90°</text><line class="dial-arc" x1="65" y1="164" x2="295" y2="164"/><g id="${id}-target" hidden><line class="dial-target" x1="180" y1="19" x2="180" y2="151"/><path fill="#9a783a" d="M174 22 L180 30 L186 22Z"/></g><g id="${id}-needle" class="dial-needle" hidden><path d="M177 160 L180 50 L183 160Z"/><circle class="dial-center" cx="180" cy="164" r="9"/><circle cx="180" cy="164" r="3"/></g></svg>`;
}

export function createPresentation({ getState, requestDraw }) {
  if(!$('presentation'))return {update(){},draw(){}};
  let cfg=readSettings(),cached=null;
  $('raw-dial').innerHTML=dialMarkup('raw');$('corrected-dial').innerHTML=dialMarkup('corrected');
  const reference=()=>cfg.references[cfg.focus];
  const hasReference=state=>Boolean(cfg.active&&typeof state.epoch==='string'&&cfg.active.epoch===state.epoch&&Number.isFinite(reference()));
  const invalidate=()=>{cfg.active=null;if(cfg.mode==='error')cfg.mode='correction';};
  function persist(){try{localStorage.setItem(STORAGE,JSON.stringify(cfg));}catch{}cached=null;syncControls();update(getState());requestDraw();}
  function syncControls(){
    for(const el of document.querySelectorAll('input[name="focus"]'))el.checked=el.value===cfg.focus;
    $('tilt-direction').value=cfg.tiltAxis;
    $('focus-mode').value=cfg.mode;
    $('focus-window').value=String(cfg.duration);
    $('time-window').value=String(cfg.duration);
    const input=$('reference-value');
    if(document.activeElement!==input)input.value=reference()===null?'':String(reference());
    if(cfg.focus==='tilt'){input.min='-90';input.max='90';}else{input.removeAttribute('min');input.removeAttribute('max');}
    text('reference-unit',cfg.focus==='tilt'?'°':'m/s²');
    text('reference-label',cfg.focus==='tilt'?'RULER REFERENCE ANGLE':`INDEPENDENT ${cfg.focus.toUpperCase()} REFERENCE`);
  }
  function update(state){
    if(cfg.active&&state.epoch&&cfg.active.epoch!==state.epoch){invalidate();try{localStorage.setItem(STORAGE,JSON.stringify(cfg));}catch{}syncControls();cached=null;}
    const latest=state.points.at(-1),rawTilt=tiltDegrees(latest?.raw,cfg.tiltAxis),correctedTilt=tiltDegrees(latest?.corrected,cfg.tiltAxis);
    const valid=hasReference(state),fresh=valid&&latest&&latest.t>cfg.active.since;
    const unit=cfg.focus==='tilt'?'°':' m/s²';
    const result=latest?compareSample(latest,cfg.focus,cfg.tiltAxis,fresh?reference():null):null;
    const calibration=state.calibration||{};
    const identity=calibration.S?.every((row,i)=>row.every((v,j)=>v===+(i===j)))&&calibration.b?.every(v=>v===0);
    const calibrationLabel=identity?'Identity · uncalibrated':calibration.fitted&&calibration.provenance?'Fitted · validate independently':'Imported · unverified';
    text('presentation-calibration',`${state.source==='synthetic'?'SYNTHETIC · ':''}${calibrationLabel}`);
    for(const [id,angle] of [['raw',rawTilt],['corrected',correctedTilt]]){
      text(`${id}-tilt`,fmt(angle,2));
      const needle=$(`${id}-needle`);needle.toggleAttribute('hidden',angle===null);
      if(angle!==null)needle.setAttribute('transform',`rotate(${angle} 180 164)`);
      const target=$(`${id}-target`);target.toggleAttribute('hidden',!valid||cfg.focus!=='tilt');
      if(valid&&cfg.focus==='tilt')target.setAttribute('transform',`rotate(${reference()} 180 164)`);
      text(`${id}-target-note`,valid&&cfg.focus==='tilt'?`Ruler target ${fmt(reference(),2)}° · slope along ${cfg.tiltAxis.toUpperCase()}`:`Inclination along phone ${cfg.tiltAxis.toUpperCase()}`);
    }
    $('reference-confirm').checked=valid;
    $('reference-confirm').disabled=!Number.isFinite(reference())||!latest||!state.epoch;
    $('reference-clear').disabled=reference()===null&&!cfg.active;
    $('focus-mode').querySelector('[value="error"]').disabled=!valid;
    const mode=cfg.mode==='error'&&!valid?'correction':cfg.mode;
    text('focus-title',mode==='error'?'Distance from the reference':mode==='signal'?`${cfg.focus==='tilt'?'Inclination':`${cfg.focus.toUpperCase()} acceleration`}, before & after`:'The correction applied');
    text('focus-subtitle',mode==='error'?'Two error curves. One scale. The zero line is your independent reference.':mode==='signal'?'One component at a time. Raw and corrected share the same scale.':'Corrected minus raw. A change in reading is not proof of improved accuracy.');
    text('focus-scale-note',`Shared auto scale · ${cfg.focus==='tilt'?'degrees':'m/s²'}`);
    $('legend-raw').hidden=mode==='correction';$('legend-corrected').hidden=mode==='correction';$('legend-delta').hidden=mode!=='correction';
    text('metric-raw',fresh&&result?`${fmt(Math.abs(result.rawError))}${unit}`:'—');
    text('metric-corrected',fresh&&result?`${fmt(Math.abs(result.correctedError))}${unit}`:'—');
    text('metric-change-label',fresh?'REDUCTION IN ABSOLUTE ERROR':'CORRECTION APPLIED');
    text('metric-change',result?`${fmt(fresh?result.errorReduction:result.delta)}${unit}`:'—');
    $('metric-change').dataset.direction=fresh&&result?(result.errorReduction>1e-9?'better':result.errorReduction< -1e-9?'worse':'same'):'same';
    const prefix=state.source==='synthetic'?'SYNTHETIC PREVIEW. ':'';
    text('comparison-caption',prefix+(valid?(fresh?'Current sample at your stated reference; not a held-out accuracy score. Positive reduction means less absolute error; negative means more.':'Reference armed. Start or resume the phone and hold it still; waiting for new samples.'):identity?'Identity calibration: both instruments agree by design. Add real coefficients and an independent reference to evaluate accuracy.':'No independent reference supplied. The correction shows a change, not demonstrated improvement.'));
    text('reference-guidance',cfg.focus==='tilt'?'Enter the signed ruler-measured angle, then confirm the supported phone is still. Tilt uses gravity; motion also changes the reading.':`Enter an independently known ${cfg.focus.toUpperCase()} component in m/s². A single axis value does not specify the full three-dimensional reference vector.`);
    $('presentation').dataset.source=state.source;
  }
  function draw(view){
    const state=getState(),valid=hasReference(state),mode=cfg.mode==='error'&&!valid?'correction':cfg.mode;
    const canvas=$('focus-chart'),bounds=canvas.getBoundingClientRect();if(bounds.width<1||bounds.height<1)return;
    const dpr=Math.min(devicePixelRatio||1,2),w=bounds.width,h=bounds.height;
    if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);}
    const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
    const pad={left:60,right:20,top:20,bottom:31},pw=w-pad.left-pad.right,ph=h-pad.top-pad.bottom;
    const key=`${view.key}:${cfg.focus}:${cfg.tiltAxis}:${mode}:${reference()}:${cfg.active?.since}:${Math.floor(pw)}`;
    if(cached?.key!==key){
      const points=[];
      for(const p of view.visible){
        if(mode==='error'&&p.t<=cfg.active.since)continue;
        const r=compareSample(p,cfg.focus,cfg.tiltAxis,mode==='error'?reference():null);if(!r)continue;
        points.push({t:p.t,raw:[mode==='correction'?r.delta:mode==='error'?r.rawError:r.raw],corrected:[mode==='error'?r.correctedError:r.corrected]});
      }
      let max=cfg.focus==='tilt'?.02:.002;
      for(const p of points)max=Math.max(max,Math.abs(p.raw[0]),mode==='correction'?0:Math.abs(p.corrected[0]));
      const target=max*1.2,magnitude=10**Math.floor(Math.log10(target));
      const extent=Math.ceil(target/magnitude*2)/2*magnitude;
      cached={key,points,extent,raw:traceForPixels(points,'raw',0,Math.ceil(pw),view.start,view.duration),corrected:mode==='correction'?[]:traceForPixels(points,'corrected',0,Math.ceil(pw),view.start,view.duration)};
    }
    const px=t=>pad.left+(t-view.start)/view.duration*pw,py=v=>pad.top+(1-v/cached.extent)*ph/2;
    ctx.font='9px Consolas, monospace';ctx.textBaseline='middle';
    for(let i=0;i<=4;i++){
      const value=cached.extent*(1-i/2),y=py(value);ctx.strokeStyle=i===2?'#9ba98b':'#dce1d3';ctx.lineWidth=1;ctx.setLineDash(i===2?[4,4]:[]);
      ctx.beginPath();ctx.moveTo(pad.left,y);ctx.lineTo(w-pad.right,y);ctx.stroke();ctx.fillStyle='#71806a';ctx.textAlign='right';ctx.fillText(fmt(value,cached.extent>=10?0:cached.extent>=1?1:3),pad.left-10,y);
    }
    ctx.setLineDash([]);
    for(let i=0;i<=5;i++){const t=view.start+view.duration*i/5,x=px(t);ctx.strokeStyle='#e3e6dc';ctx.beginPath();ctx.moveTo(x,pad.top);ctx.lineTo(x,h-pad.bottom);ctx.stroke();ctx.fillStyle='#71806a';ctx.textAlign='center';ctx.fillText(`${fmt(t,view.duration<=5?1:0)}s`,x,h-12);}
    ctx.save();ctx.beginPath();ctx.rect(pad.left,pad.top,pw,ph);ctx.clip();
    for(const [trace,color,dash] of [[cached.raw,mode==='correction'?'#9a783a':'#b46147',mode==='correction'?[]:[5,4]],[cached.corrected,'#347e75',[]]]){
      ctx.beginPath();let last=null;for(const [t,value] of trace){if(last===null||t-last>1)ctx.moveTo(px(t),py(value));else ctx.lineTo(px(t),py(value));last=t;}
      ctx.strokeStyle=color;ctx.lineWidth=1.8;ctx.setLineDash(dash);ctx.stroke();ctx.setLineDash([]);
      const end=trace.at(-1);if(end){ctx.fillStyle=color;ctx.beginPath();ctx.arc(px(end[0]),py(end[1]),2.7,0,Math.PI*2);ctx.fill();}
    }
    ctx.restore();
    $('focus-empty').hidden=cached.points.length>0;
    text('focus-empty',mode==='error'?'Waiting for fresh measurements at the confirmed reference.':state.points.length?'No valid inclination in this window.':'Connect your phone to bring the instruments to life.');
  }
  document.querySelectorAll('input[name="focus"]').forEach(el=>el.addEventListener('change',()=>{cfg.focus=el.value;invalidate();persist();}));
  $('tilt-direction').addEventListener('change',()=>{cfg.tiltAxis=$('tilt-direction').value;invalidate();persist();});
  $('reference-value').addEventListener('input',()=>{const input=$('reference-value');cfg.references[cfg.focus]=input.value!==''&&input.validity.valid&&Number.isFinite(input.valueAsNumber)?input.valueAsNumber:null;invalidate();persist();});
  $('reference-confirm').addEventListener('change',()=>{const state=getState(),last=state.points.at(-1);if($('reference-confirm').checked&&Number.isFinite(reference())&&last){cfg.active={epoch:state.epoch,since:last.t};cfg.mode='error';}else invalidate();persist();});
  $('reference-clear').addEventListener('click',()=>{cfg.references[cfg.focus]=null;invalidate();persist();});
  $('focus-mode').addEventListener('change',()=>{cfg.mode=$('focus-mode').value;persist();});
  $('focus-window').addEventListener('change',()=>{cfg.duration=Number($('focus-window').value);persist();});
  $('time-window').addEventListener('change',()=>{cfg.duration=Number($('time-window').value);persist();});
  $('trace-inspector').addEventListener('toggle',requestDraw);
  window.addEventListener('storage',event=>{if(event.key===STORAGE){cfg=readSettings();cached=null;syncControls();update(getState());requestDraw();}});
  if('ResizeObserver' in window)new ResizeObserver(requestDraw).observe($('focus-chart'));
  syncControls();return {update,draw};
}
