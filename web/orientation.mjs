// Quaternions are device-to-world rotations, [x,y,z,w], with world +Z up.
export function normalizeQuaternion(q) {
  if(!Array.isArray(q)||q.length!==4||!q.every(Number.isFinite))return null;
  const norm=Math.hypot(...q);return Number.isFinite(norm)&&norm>1e-9?q.map(v=>v/norm):null;
}

export function gravityQuaternion(vector) {
  if(!Array.isArray(vector)||vector.length!==3||!vector.every(Number.isFinite))return null;
  const norm=Math.hypot(...vector);if(!Number.isFinite(norm)||norm<.05)return null;
  const [x,y,z]=vector.map(v=>v/norm);
  // Minimum rotation mapping observed body-frame specific force onto world +Z.
  // Heading about world gravity is unobservable from an accelerometer alone.
  return z<-.999999?[1,0,0,0]:normalizeQuaternion([y,-x,0,1+z]);
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
