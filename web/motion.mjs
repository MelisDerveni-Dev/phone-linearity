import { createPhoneModel } from './phone-model.mjs';
import { gravityQuaternion, normalizeQuaternion, slerpQuaternion, quaternionDistance, motionEvidence } from './orientation.mjs';

const $=id=>document.getElementById(id);
function text(id,value){const el=$(id);if(el&&el.textContent!==value)el.textContent=value;}
const number=v=>Number.isFinite(v)?v.toFixed(2):'—';

export function createMotionView({ getState }) {
  const section=$('motion-section'),host=$('motion-model-host');
  if(!section||!host)return {update(){},dispose(){}};
  const model=createPhoneModel(host),mode=$('motion-mode'),stage=$('motion-stage'),world=$('motion-world');
  let epoch=null,started=false,selected=false,lastMeasuring=false,target=[0,0,0,1],current=[0,0,0,1],frame=null,lastFrame=0,visible=true;
  let cameraX=52,cameraZ=-24,drag=null;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  function animate(now){
    frame=null;if(!visible||document.hidden)return;
    const dt=Math.min(.1,Math.max(0,(now-lastFrame)/1000));lastFrame=now;
    current=slerpQuaternion(current,target,reduced.matches?1:1-Math.exp(-dt/.055));
    model.setQuaternion(current);
    if(quaternionDistance(current,target)>.0001)frame=requestAnimationFrame(animate);
  }
  function schedule(){if(frame===null&&visible&&!document.hidden){lastFrame=performance.now();frame=requestAnimationFrame(animate);}}
  function camera(){world.style.transform=`rotateX(${cameraX}deg) rotateZ(${cameraZ}deg)`;}
  function update(state=getState()){
    if(epoch!==state.epoch){epoch=state.epoch;started=false;lastMeasuring=false;current=target=[0,0,0,1];model.reset();}
    const latest=state.points.at(-1),age=state.lastReceivedAt?Date.now()-state.lastReceivedAt:Infinity;
    const fromPhone=state.source==='phone'&&state.connected,synthetic=state.source==='synthetic';
    const available=state.attitudeAvailable===true;
    const attitudeOption=mode.querySelector('[value="attitude"]');attitudeOption.disabled=!available;attitudeOption.textContent=available?'Fused attitude':'Fused attitude · unavailable';
    if(!selected)mode.value=available?'attitude':'gravity';
    if(state.measuring&&latest&&(fromPhone||synthetic)&&age<1500){
      if(!started||!lastMeasuring)$('trace-inspector').open=true;
      started=true;
    }
    lastMeasuring=state.measuring;
    const active=started&&(fromPhone||synthetic);
    host.hidden=!active;
    $('motion-placeholder').hidden=active;
    const evidence=motionEvidence(state.points);
    text('motion-norm',number(evidence.norm));text('motion-variation',number(evidence.variation));
    text('motion-latency',active&&Number.isFinite(age)?String(Math.round(age)):'—');
    const fused=mode.value==='attitude';
    const attitudeFresh=state.orientationReceivedAt&&Date.now()-state.orientationReceivedAt<1500;
    const candidate=fused?(available&&attitudeFresh?normalizeQuaternion(state.orientation?.q):null):gravityQuaternion(latest?.corrected);
    let status='idle',label='Ready for a measurement';
    if(active&&!state.measuring){status='paused';label='Paused · last measured pose';}
    else if(active&&(state.error||age>1500)){status='stale';label='Stream interrupted · pose held';}
    else if(active&&fused&&!candidate){status='stale';label='No fresh attitude · pose held';}
    else if(active&&!candidate){status='uncertain';label='Tilt undefined · pose held';}
    else if(active&&evidence.level==='uncertain'){status='uncertain';label=fused?'Strong motion · fused estimate':'Strong motion · tilt uncertain';}
    else if(active&&evidence.level==='moving'){status='moving';label=fused?'Following fused orientation':'Motion detected · tilt uncertain';}
    else if(active){status='steady';label=fused?'Following fused orientation':'Following gravity-based tilt';}
    if(active&&state.measuring&&!state.error&&age<1500&&candidate){target=candidate;schedule();}
    section.dataset.state=status==='uncertain'?'unreliable':status;section.dataset.source=state.source;
    text('motion-status',`${synthetic?'SYNTHETIC · ':''}${label}`);
    text('motion-source',synthetic?'SYNTHETIC PREVIEW':!fromPhone?'NO ACTIVE SOURCE':fused?'DEVICE-FUSED ATTITUDE':'CALIBRATED GRAVITY TILT');
    text('motion-yaw-note',fused?'Fused attitude includes heading. It is the phone’s orientation estimate, not independent ground truth.':available?'Gravity mode cannot determine heading. Switch to fused attitude for full rotation.':'Heading is unobserved with acceleration alone. Import the optional motion experiment for full rotation.');
    text('motion-placeholder',fromPhone?'Press Start phone. The model will follow fresh measurements.':'Connect your phone, then press Start phone.');
  }
  mode.addEventListener('change',()=>{selected=true;update();});
  $('motion-view-reset').addEventListener('click',()=>{cameraX=52;cameraZ=-24;camera();});
  stage.addEventListener('pointerdown',event=>{
    if(event.button!==0||event.target.closest('button,select,a'))return;
    drag={x:event.clientX,y:event.clientY,rx:cameraX,rz:cameraZ};stage.dataset.dragging='true';stage.setPointerCapture(event.pointerId);
  });
  stage.addEventListener('pointermove',event=>{if(!drag)return;cameraX=Math.max(-75,Math.min(75,drag.rx-(event.clientY-drag.y)*.3));cameraZ=drag.rz+(event.clientX-drag.x)*.4;camera();});
  for(const type of ['pointerup','pointercancel','lostpointercapture'])stage.addEventListener(type,()=>{drag=null;stage.dataset.dragging='false';});
  const observer='IntersectionObserver'in window?new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;if(visible)schedule();else if(frame!==null){cancelAnimationFrame(frame);frame=null;}},{rootMargin:'80px'}):null;
  observer?.observe(stage);
  const resume=()=>{if(!document.hidden)schedule();};document.addEventListener('visibilitychange',resume);
  return {update,dispose(){observer?.disconnect();if(frame!==null)cancelAnimationFrame(frame);model.dispose?.();document.removeEventListener('visibilitychange',resume);}};
}
