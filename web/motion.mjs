import { createPhoneModel } from './phone-model.mjs';
import { gravityQuaternion, normalizeQuaternion, createPoseTimeline, motionEvidence, angularSpeedDegrees, createMotionGuard, slerpQuaternion } from './orientation.mjs';

const $=id=>document.getElementById(id);
function text(id,value){const el=$(id);if(el&&el.textContent!==value)el.textContent=value;}
const number=v=>Number.isFinite(v)?v.toFixed(2):'—';

export function createMotionView({ getState }) {
  const section=$('motion-section'),host=$('motion-model-host');
  if(!section||!host)return {update(){},dispose(){}};
  const model=createPhoneModel(host),mode=$('motion-mode'),stage=$('motion-stage'),world=$('motion-world');
  let epoch=null,started=false,selected=false,lastMeasuring=false,frame=null,visible=true,sourceMode=null,lastPoseT=null,previousGravity=null;
  const timeline=createPoseTimeline();
  const guard=createMotionGuard();
  let motionPaused=false,lastRendered=null,resumeBlend=null;
  let cameraX=52,cameraZ=-24,drag=null;
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  function animate(){
    frame=null;if(!visible||document.hidden||motionPaused)return;
    const state=getState(),fused=mode.value==='attitude';
    const received=fused?state.orientationReceivedAt:state.lastReceivedAt;
    const fresh=received&&Date.now()-received<1500&&!state.error;
    if(!fresh)return;
    let q=timeline.read(Date.now(),{immediate:reduced.matches||!state.measuring});
    if(q&&resumeBlend&&!reduced.matches){
      const t=Math.min(1,(performance.now()-resumeBlend.start)/80);
      q=slerpQuaternion(resumeBlend.from,q,t*t*(3-2*t));
      if(t>=1)resumeBlend=null;
    }
    if(q){model.setQuaternion(q);lastRendered=q;}
    if(state.measuring&&!reduced.matches)frame=requestAnimationFrame(animate);
  }
  function schedule(){if(frame===null&&visible&&!document.hidden)frame=requestAnimationFrame(animate);}
  function camera(){world.style.transform=`rotateX(${cameraX}deg) rotateZ(${cameraZ}deg)`;}
  function update(state=getState()){
    if(epoch!==state.epoch){epoch=state.epoch;started=false;lastMeasuring=false;sourceMode=null;timeline.clear();guard.reset();motionPaused=false;lastRendered=null;resumeBlend=null;model.reset();}
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
    $('motion-setup').hidden=available;
    if(sourceMode!==mode.value){sourceMode=mode.value;timeline.clear();guard.reset();motionPaused=false;resumeBlend=null;lastPoseT=null;previousGravity=null;}
    const attitudeFresh=state.orientationReceivedAt&&Date.now()-state.orientationReceivedAt<1500;
    const candidate=fused?(available&&attitudeFresh?normalizeQuaternion(state.orientation?.q):null):gravityQuaternion(latest?.corrected,previousGravity);
    const wasPaused=motionPaused;
    const rotationSamples=attitudeFresh?state.orientationSamples:[];
    const rotationSpeed=angularSpeedDegrees(rotationSamples);
    const hold=active&&state.measuring&&!state.error&&age<1500?guard.update({time:latest?.t,evidence,angularSpeedDegS:rotationSpeed,rotationAvailable:available}):{paused:motionPaused,settling:false};
    motionPaused=hold.paused;
    if(motionPaused)resumeBlend=null;
    else if(wasPaused&&lastRendered)resumeBlend={from:lastRendered,start:performance.now()};
    host.hidden=!active||(motionPaused&&!lastRendered);
    const warning=active&&state.measuring&&!state.error&&age<1500&&motionPaused;
    $('motion-warning').hidden=!warning;
    section.dataset.motionHold=String(warning);
    text('motion-warning-title',hold.settling?'Motion eased · resuming':`${hold.reason||'High motion'} · display paused`);
    text('motion-warning-detail','Pose held by display policy. Live sensor data continues.');
    let status='idle',label='Ready for a measurement';
    if(active&&!state.measuring){status='paused';label='Paused · last measured pose';}
    else if(active&&(state.error||age>1500)){status='stale';label='Stream interrupted · pose held';}
    else if(active&&fused&&!candidate){status='stale';label='No fresh attitude · pose held';}
    else if(active&&motionPaused){status='uncertain';label=hold.settling?'Settling · pose held':'High motion · display paused';}
    else if(active&&!candidate){status='uncertain';label='Tilt undefined · pose held';}
    else if(active&&evidence.level==='uncertain'){status='uncertain';label=fused?'Strong motion · fused estimate':'Strong motion · tilt uncertain';}
    else if(active&&evidence.level==='moving'){status='moving';label=fused?'Following fused orientation':'Motion detected · tilt uncertain';}
    else if(active){status='steady';label=fused?'Following fused orientation':'Following gravity-based tilt';}
    if(active&&!state.error&&age<1500&&candidate){
      if(fused){
        // Backward compatible with bridges that send only the latest quaternion.
        const batch=state.orientationSamples?.length?state.orientationSamples:[state.orientation];
        if(lastPoseT!==null&&batch.at(-1)?.t<lastPoseT)timeline.clear();
        timeline.push(batch,state.orientationReceivedAt);lastPoseT=batch.at(-1)?.t??lastPoseT;
      }else{
        const batch=[];
        for(const point of state.points){
          if(point.t<latest.t-.5||(lastPoseT!==null&&point.t<=lastPoseT))continue;
          const q=gravityQuaternion(point.corrected,previousGravity);
          if(q){batch.push({t:point.t,q});previousGravity=q;lastPoseT=point.t;}
        }
        timeline.push(batch,state.lastReceivedAt);
      }
      schedule();
    }
    section.dataset.state=status==='uncertain'?'unreliable':status;section.dataset.source=state.source;
    text('motion-status',`${synthetic?'SYNTHETIC · ':''}${label}`);
    text('motion-source',synthetic?'SYNTHETIC PREVIEW':!fromPhone?'NO ACTIVE SOURCE':fused?'DEVICE-FUSED ATTITUDE':'CALIBRATED GRAVITY TILT');
    text('motion-yaw-note',fused?'All three rotations use device-fused attitude, interpolated with a 70 ms display buffer. This is the phone’s estimate, not ground truth.':available?'Tilt only · heading is unmeasured. Select Fused attitude to follow all three rotations.':'Tilt only · one rotation cannot be measured by this experiment. Set up full rotation below.');
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
