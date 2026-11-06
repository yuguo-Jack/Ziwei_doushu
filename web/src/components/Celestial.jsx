import React,{useEffect,useMemo,useRef,useState} from 'react';
import {StarMark,Icon} from './Icons';

export const BRANCHES='子丑寅卯辰巳午未申酉戌亥';
export const PALACE_TOPICS={'命':'overview','夫妻':'love','官禄':'career','财帛':'wealth','疾厄':'health','兄弟':'family','子女':'children','迁移':'move','仆役':'friends','交友':'friends','田宅':'home','福德':'spirit','父母':'parents'};
const TOPIC_NAMES={overview:'命',personality:'命',career:'官禄',wealth:'财帛',love:'夫妻',health:'疾厄',family:'兄弟',children:'子女',move:'迁移',friends:'仆役',home:'田宅',spirit:'福德',parents:'父母'};
const POSITIONS={5:[0,0],6:[1,0],7:[2,0],8:[3,0],4:[0,1],9:[3,1],3:[0,2],10:[3,2],2:[0,3],1:[1,3],0:[2,3],11:[3,3]};

export function CelestialBackdrop({moving,theme}){
 const canvas=useRef(null);
 useEffect(()=>{
  const el=canvas.current,ctx=el.getContext('2d'),preference=matchMedia('(prefers-reduced-motion: reduce)');let frame=0,last=0,width=0,height=0,stars=[];
  let seed=181247;const random=()=>{seed=(seed*16807)%2147483647;return(seed-1)/2147483646;};
  function resize(){width=innerWidth;height=innerHeight;const ratio=Math.min(devicePixelRatio,1.5);el.width=width*ratio;el.height=height*ratio;ctx.setTransform(ratio,0,0,ratio,0,0);seed=181247;stars=Array.from({length:Math.min(130,Math.round(width*height/10000))},()=>({x:random()*width,y:random()*height,r:.4+random()*.9,a:.16+random()*.42,phase:random()*Math.PI*2}));paint(0);}
  function paint(time){ctx.clearRect(0,0,width,height);for(const star of stars){const twinkle=moving&&!preference.matches ? .3*Math.sin(time/3200+star.phase) : 0;ctx.globalAlpha=Math.max(.08,star.a+twinkle);ctx.fillStyle=theme==='light'?'#7f704e':'#d0bd89';ctx.beginPath();ctx.arc(star.x,star.y,star.r,0,Math.PI*2);ctx.fill();}ctx.globalAlpha=1;}
  function loop(time){if(time-last>45){paint(time);last=time;}frame=requestAnimationFrame(loop);}
  function resume(){cancelAnimationFrame(frame);if(moving&&!preference.matches&&!document.hidden)frame=requestAnimationFrame(loop);else paint(0);}
  resize();resume();window.addEventListener('resize',resize);document.addEventListener('visibilitychange',resume);preference.addEventListener('change',resume);
  return()=>{cancelAnimationFrame(frame);window.removeEventListener('resize',resize);document.removeEventListener('visibilitychange',resume);preference.removeEventListener('change',resume);};
 },[moving,theme]);
 return <canvas className="celestial-backdrop" ref={canvas} aria-hidden="true"/>;
}

function OrbitGeometry(){
 return <svg className="orbit-geometry" viewBox="0 0 400 400" fill="none" aria-hidden="true"><circle cx="200" cy="200" r="185"/><circle cx="200" cy="200" r="172"/><circle cx="200" cy="200" r="143" strokeDasharray="1 8"/><circle cx="200" cy="200" r="110"/>{Array.from({length:60},(_,i)=>{const a=i*Math.PI/30,r=i%5===0?174:180;return <path key={i} d={`M${200+Math.sin(a)*r} ${200-Math.cos(a)*r}L${200+Math.sin(a)*185} ${200-Math.cos(a)*185}`}/>;})}<path d="M200 2v22M200 376v22M2 200h22M376 200h22"/></svg>;
}

export function ChartStage({calculated,topic,busy,hidden,onSelect}){
 const [hovered,setHovered]=useState(null),[zoomed,setZoomed]=useState(false),native=useRef(null);
 const palaces=calculated?.chart.palaces||[],period=calculated?.period;
 const displayName=p=>period?.selected.palaces.find(q=>q.branch===p.branch)?.period_palace||p.name;
 const selected=palaces.find(p=>displayName(p).replace('宫','')===TOPIC_NAMES[topic]);
 const branch=hovered??selected?.branch;
 const related=branch===undefined?[]:[branch,(branch+4)%12,(branch+8)%12,(branch+6)%12];
 const current=palaces.find(p=>p.branch===branch)||selected;
 const enhanced=useMemo(()=>{
  if(!calculated)return '';
  return calculated.svg.replace('role="img"','role="group"').replace(/<g data-branch="(\d+)">/g,(_,value)=>{
   const b=Number(value),p=palaces.find(p=>p.branch===b),name=displayName(p);
   return `<g data-branch="${b}" role="button" tabindex="0" aria-label="查看${name}研读" class="palace">`;
  });
 },[calculated]);
 useEffect(()=>{for(const group of native.current?.querySelectorAll('[data-branch]')||[]){const b=Number(group.dataset.branch);group.classList.toggle('is-selected',b===branch);group.classList.toggle('is-related',b!==branch&&related.includes(b));group.setAttribute('aria-pressed',String(b===selected?.branch));}},[calculated,branch,selected?.branch]);
 const points=related.map(b=>{const [x,y]=POSITIONS[b];return[165+x*290,165+y*290];});
 const onActivate=e=>{const value=e.target.closest('[data-branch]')?.getAttribute('data-branch');if(value!==undefined&&value!==null)onSelect(Number(value));};
 const birth=calculated?.normalized_birth,info=calculated?.chart;
 return <>
  <div className="chart-reading-line"><span><i className="legend-dot"/> {current?displayName(current):'十二宫星图'}</span><span className="muted desktop-chart-hint">{hovered!==null?'点击宫位，查看研读':'点选宫位 · 联看三方四正'}</span><button className="chart-scale-toggle" onClick={()=>setZoomed(!zoomed)} aria-pressed={zoomed}>{zoomed?'适应屏幕':'放大命盘'}</button></div>
  <div tabIndex="0" role="region" aria-label="十二宫命盘，可放大查看" className={'chart-image '+(busy?'is-loading':'')}>
   {calculated?<div className={'chart-viewport '+(zoomed?'is-zoomed':'')} onClick={onActivate} onFocusCapture={()=>setHovered(null)} onKeyDown={e=>{if((e.key==='Enter'||e.key===' ')&&e.target.closest('[data-branch]')){e.preventDefault();setHovered(null);onActivate(e);}}} onPointerOver={e=>{const value=e.target.closest('[data-branch]')?.getAttribute('data-branch');if(value!==undefined&&value!==null)setHovered(Number(value));}} onPointerLeave={()=>setHovered(null)}>
    <div className="native-chart" ref={native} dangerouslySetInnerHTML={{__html:enhanced}}/>
    <svg className="palace-connections" viewBox="0 0 1200 1200" fill="none" aria-hidden="true">{points.length===4&&<><path d={`M${points[0].join(' ')}L${points[1].join(' ')}L${points[2].join(' ')}Z`}/><path className="opposition-line" d={`M${points[0].join(' ')}L${points[3].join(' ')}`}/></>}</svg>
    <div className="chart-hub"><OrbitGeometry/><div className="chart-hub-content"><StarMark/><h2>紫微命盘</h2><span className="hub-rule"/><p className="hub-birth">{hidden?'生辰已隐藏':`${birth.year}年${birth.month}月${birth.day}日`}</p><p className="hub-time">{hidden?'':`${BRANCHES[birth.hour]}时 · ${birth.gender==='male'?'男':'女'}`}</p><strong>{info.wuxingJuName||''}</strong><dl><div><dt>命主</dt><dd>{info.mingZhu||'—'}</dd></div><div><dt>身主</dt><dd>{info.shenZhu||'—'}</dd></div></dl></div></div>
   </div>:<div className="chart-loading"><StarMark/><p>正在推演十二宫星位…</p><span>初始为虚构示例命盘</span></div>}
  </div>
  <div className="chart-legend"><span><i className="legend-dot"/>所选宫位</span><span><i className="legend-dot jade"/>三方四正</span><span>星位由本地引擎计算</span></div>
  {selected&&<div className="chart-palace-summary"><div><strong>{displayName(selected)} · {BRANCHES[selected.branch]}</strong><p>{selected.stars.filter(s=>s.type==='major').map(s=>s.name+(s.brightnessRaw?'（'+s.brightnessRaw+'）':'')+(s.siHua?'化'+s.siHua:'')).join('、')||'无十四主星；借看'+(selected.borrowedStars||[]).join('、')}</p></div><button onClick={()=>document.querySelector('.reading,.source-inspector')?.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})}>查看依据<Icon name="arrow" size={15}/></button></div>}
 </>;
}

export function SurfaceIntro({tab}){
 const lines={chart:['命盘研究','以星为引，循典而读。'],chat:['问答研读','循着问题，读懂星位与原典。'],library:['资料库','让每一次解读，都有来处。'],compare:['合盘','两张命盘，四种关系视角。'],tools:['工具箱','历法、时辰与星位，逐一推演。'],records:['本地记录','把一次研习，留作下一次的起点。']};
 return <div className="surface-intro"><div><h1>{lines[tab][0]}</h1><p>{lines[tab][1]}</p></div><div className="intro-orbit" aria-hidden="true"><StarMark/><span>观星循典</span></div></div>;
}
