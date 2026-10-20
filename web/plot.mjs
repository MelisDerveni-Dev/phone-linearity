// Pure plotting helpers. Retain measured extrema; never smooth sensor values.
export function lowerBound(points, time) {
  let lo=0,hi=points.length;
  while(lo<hi){const mid=(lo+hi)>>>1;if(points[mid].t<time)lo=mid+1;else hi=mid;}
  return lo;
}

export function mergeUpdate(current, update) {
  if(update.append && current.epoch!==update.epoch)throw new Error('Stream reset required.');
  const points=update.append?(update.points.length?[...current.points,...update.points]:current.points):update.points;
  const cutoff=(points.at(-1)?.t??0)-32;
  const first=Math.max(lowerBound(points,cutoff),points.length-30000);
  return {...update,points:first>0?points.slice(first):points};
}

export function traceForPixels(points, field, index, columns, start, duration) {
  if(points.length<=columns*4)return points.map(p=>[p.t,p[field][index]]);
  const result=[];
  let bucket=null,first=null,last=null,min=null,max=null;
  const flush=()=>{
    if(!first)return;
    const ordered=[first,min,max,last].sort((a,b)=>a[0]-b[0]);
    for(const point of ordered)if(result.at(-1)?.[0]!==point[0])result.push(point);
  };
  for(const p of points){
    const value=p[field][index],column=Math.floor((p.t-start)/duration*columns);
    if(!Number.isFinite(value))continue;
    const point=[p.t,value];
    if(column!==bucket){flush();bucket=column;first=last=min=max=point;}
    else {last=point;if(value<min[1])min=point;if(value>max[1])max=point;}
  }
  flush();return result;
}
