// Quaternions are device-to-world rotations, [x,y,z,w], with world +Z up.
export function normalizeQuaternion(q) {
  if(!Array.isArray(q)||q.length!==4||!q.every(Number.isFinite))return null;
  const norm=Math.hypot(...q);return Number.isFinite(norm)&&norm>1e-9?q.map(v=>v/norm):null;
}

export function gravityQuaternion(vector, previous=null) {
  if(!Array.isArray(vector)||vector.length!==3||!vector.every(Number.isFinite))return null;
  const norm=Math.hypot(...vector);if(!Number.isFinite(norm)||norm<.05)return null;
  let [x,y,z]=vector.map(v=>v/norm);
  const prior=normalizeQuaternion(previous);
  if(prior){
    // Correct the previous pose by the smallest rotation in world space.
    // Unlike choosing a new zero-heading pose on every sample, this stays
    // continuous through screen-down. Heading remains unmeasured.
    const [qx,qy,qz,qw]=prior;
    const tx=2*(qy*z-qz*y),ty=2*(qz*x-qx*z),tz=2*(qx*y-qy*x);
    [x,y,z]=[x+qw*tx+qy*tz-qz*ty,y+qw*ty+qz*tx-qx*tz,z+qw*tz+qx*ty-qy*tx];
    const delta=z<-.999999?[1,0,0,0]:normalizeQuaternion([y,-x,0,1+z]);
    const [a,b,c,d]=delta;
    return normalizeQuaternion([
      d*qx+a*qw+b*qz-c*qy,d*qy-a*qz+b*qw+c*qx,
      d*qz+a*qy-b*qx+c*qw,d*qw-a*qx-b*qy-c*qz,
    ]);
  }
  // Minimum rotation mapping observed body-frame specific force onto world +Z.
  // Heading about world gravity is unobservable from an accelerometer alone.
  return z<-.999999?[1,0,0,0]:normalizeQuaternion([y,-x,0,1+z]);
}

// Display buffered, timestamped measurements between network deliveries.
// Read never extrapolates a rotation beyond the measured endpoints.
export function createPoseTimeline({delayMs=70,maxSeconds=.5,maxPoints=300}={}) {
  let samples=[],receivedAt=null;
  return {
    clear(){samples=[];receivedAt=null;},
    latest(){return samples.at(-1)||null;},
    push(batch,arrival){
      let added=false;
      for(const sample of batch){
        const q=normalizeQuaternion(sample?.q);
        if(!Number.isFinite(sample?.t)||!q||(samples.length&&sample.t<=samples.at(-1).t))continue;
        samples.push({t:sample.t,q});added=true;
      }
      if(added){
        receivedAt=arrival;
        const cutoff=samples.at(-1).t-maxSeconds;
        let first=0;while(first+1<samples.length&&samples[first+1].t<cutoff)first++;
        samples=samples.slice(Math.max(first,samples.length-maxPoints));
      }
      return added;
    },
    read(now,{immediate=false}={}){
      if(!samples.length)return null;
      if(immediate)return samples.at(-1).q;
      const t=samples.at(-1).t+(now-receivedAt)/1000-delayMs/1000;
      if(t<=samples[0].t)return samples[0].q;
      for(let i=1;i<samples.length;i++)if(t<=samples[i].t){
        const a=samples[i-1],b=samples[i];
        return slerpQuaternion(a.q,b.q,(t-a.t)/(b.t-a.t));
      }
      return samples.at(-1).q;
    },
  };
}

export function slerpQuaternion(from,to,alpha) {
  const a=normalizeQuaternion(from),b=normalizeQuaternion(to);if(!a)return b;if(!b)return a;
  let dot=a.reduce((s,v,i)=>s+v*b[i],0);const end=dot<0?b.map(v=>-v):b;dot=Math.abs(dot);
  const t=Math.max(0,Math.min(1,alpha));
  if(dot>.9995)return normalizeQuaternion(a.map((v,i)=>v+(end[i]-v)*t));
  const angle=Math.acos(Math.min(1,dot)),sin=Math.sin(angle);
  return a.map((v,i)=>(Math.sin((1-t)*angle)*v+Math.sin(t*angle)*end[i])/sin);
}

export function quaternionDistance(a,b) {
  const x=normalizeQuaternion(a),y=normalizeQuaternion(b);if(!x||!y)return Infinity;
  return 2*Math.acos(Math.min(1,Math.abs(x.reduce((s,v,i)=>s+v*y[i],0))));
}

export function motionEvidence(points,windowSeconds=.25) {
  if(!points.length)return {norm:null,variation:null,samples:0,level:'unavailable'};
  const end=points.at(-1).t,values=[];
  for(let i=points.length-1;i>=0&&points[i].t>=end-windowSeconds;i--){const v=points[i].corrected;if(v?.length===3&&v.every(Number.isFinite))values.push(v);}
  if(!values.length)return {norm:null,variation:null,samples:0,level:'unavailable'};
  const norm=Math.hypot(...values[0]),mean=[0,0,0];for(const v of values)for(let k=0;k<3;k++)mean[k]+=v[k]/values.length;
  let sum=0;for(const v of values)for(let k=0;k<3;k++)sum+=(v[k]-mean[k])**2;
  const variation=Math.sqrt(sum/values.length),deviation=Math.abs(norm-9.81);
  // Indicators only: neither near-g readings nor low variation prove stillness.
  const level=norm<.05||deviation>1.5||variation>1.5?'uncertain':deviation>.35||variation>.35?'moving':'steady';
  return {norm,variation,samples:values.length,level};
}

// Measured quaternion change, not a claim of raw gyroscope access or accuracy.
export function angularSpeedDegrees(samples,windowSeconds=.15) {
  if(!samples?.length)return null;
  const cutoff=samples.at(-1).t-windowSeconds;
  let distance=0,duration=0;
  for(let i=1;i<samples.length;i++){
    const a=samples[i-1],b=samples[i],dt=b.t-a.t;
    if(b.t<cutoff||!Number.isFinite(dt)||dt<=0||dt>.1)continue;
    const angle=quaternionDistance(a.q,b.q);
    if(!Number.isFinite(angle))continue;
    const span=Math.min(dt,b.t-cutoff);
    distance+=angle*span/dt;duration+=span;
  }
  return duration>0?distance/duration*180/Math.PI:null;
}

// Explicit presentation policy, not a detected sensor failure or confidence score.
// Quiet time must be observed continuously: a gap longer than maxGapSeconds restarts it.
export function createMotionGuard({pauseMagnitude=60,resumeMagnitude=30,pauseDegS=720,resumeDegS=180,settleSeconds=.15,maxGapSeconds=.25}={}) {
  let paused=false,quietSince=null,lastTime=null,reason=null;
  const reset=()=>{paused=false;quietSince=null;lastTime=null;reason=null;};
  return {
    reset,
    update({time,evidence,angularSpeedDegS=null,rotationAvailable=false}){
      if(!Number.isFinite(time))return {paused,settling:false,reason};
      if(lastTime!==null&&time<lastTime)reset();
      const gap=lastTime===null?0:time-lastTime;
      lastTime=time;
      const fastRotation=Number.isFinite(angularSpeedDegS)&&angularSpeedDegS>pauseDegS;
      const strongAcceleration=Number.isFinite(evidence.norm)&&evidence.norm>pauseMagnitude;
      if(strongAcceleration||fastRotation){
        paused=true;quietSince=null;reason=fastRotation?'Fast rotation':'Strong acceleration';
      }else if(paused){
        const quiet=Number.isFinite(evidence.norm)&&evidence.norm<resumeMagnitude&&(!rotationAvailable||(Number.isFinite(angularSpeedDegS)&&angularSpeedDegS<resumeDegS));
        if(!quiet)quietSince=null;
        else{
          if(quietSince===null||gap>maxGapSeconds)quietSince=time;
          if(time-quietSince>=settleSeconds){paused=false;quietSince=null;reason=null;}
        }
      }
      return {paused,settling:quietSince!==null,reason};
    },
  };
}
