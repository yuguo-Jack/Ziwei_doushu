import React,{useEffect,useRef,useState} from 'react';
import {Icon,StarMark} from './Icons';
import './product-tour.css';

const MEDIA='/media/product-tour';
const VIDEO=`${MEDIA}/intro.mp4`;
function clock(value){const seconds=Math.max(0,Math.floor(value||0));return `${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;}

export default function ProductTour({open,onClose}){
 const dialog=useRef(null),video=useRef(null);
 const [chapters,setChapters]=useState([]),[failed,setFailed]=useState(false),[duration,setDuration]=useState(0),[active,setActive]=useState(-1);
 useEffect(()=>{
   if(!open)return;
   const modal=dialog.current,player=video.current,controller=new AbortController(),previousOverflow=document.documentElement.style.overflow;
   setFailed(false);setActive(-1);modal.showModal();document.documentElement.style.overflow='hidden';
   fetch(`${MEDIA}/chapters.json`,{signal:controller.signal}).then(response=>{
     if(!response.ok)throw new Error('Chapter metadata unavailable');return response.json();
   }).then(data=>setChapters(Array.isArray(data.chapters)?data.chapters.filter(row=>typeof row.label==='string'&&Number.isFinite(row.start)&&row.start>=0):[])).catch(()=>{});
   return()=>{controller.abort();player?.pause();modal.close();document.documentElement.style.overflow=previousOverflow;};
 },[open]);
 function jump(start){
   const player=video.current;if(!player||!Number.isFinite(player.duration))return;
   player.currentTime=Math.min(start,Math.max(0,player.duration-.1));player.play().catch(()=>{});
 }
 function close(){video.current?.pause();dialog.current?.close();onClose();}
 if(!open)return null;
 return <dialog ref={dialog} className="product-tour" aria-labelledby="product-tour-title" onCancel={event=>{event.preventDefault();close();}} onClick={event=>{
   if(event.target!==event.currentTarget)return;const box=event.currentTarget.getBoundingClientRect();
   if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)close();
 }}>
   <div className="tour-heading"><StarMark/><div><h2 id="product-tour-title">产品介绍</h2></div><button type="button" className="tour-close" autoFocus aria-label="关闭产品介绍" onClick={close}>×</button></div>
   <div className="tour-screen"><video ref={video} controls playsInline preload="metadata" poster={`${MEDIA}/poster.jpg`} aria-label="紫微研习产品介绍，含中文旁白与画面字幕" onLoadedMetadata={event=>setDuration(event.currentTarget.duration)} onError={()=>setFailed(true)} onTimeUpdate={event=>{
     const current=event.currentTarget.currentTime;let selected=-1;chapters.forEach((row,index)=>{if(current>=row.start)selected=index;});setActive(selected);
   }}><source src={VIDEO} type="video/mp4"/>你的浏览器暂不支持视频播放，可通过下方链接下载观看。</video></div>
   {failed&&<p className="tour-error" role="alert">视频暂时未能加载，请刷新重试，也可以下载后观看。</p>}
   <div className="tour-meta"><span><i/>{duration?clock(duration):'30 秒'}</span><span>虚构资料演示</span><a href={VIDEO} download="紫微研习-产品介绍.mp4"><Icon name="download" size={15}/>下载视频</a></div>
   {chapters.length>0&&<nav className="tour-chapters" aria-label="视频章节">{chapters.map((row,index)=><button key={row.start} type="button" className={active===index?'current':''} aria-current={active===index?'true':undefined} onClick={()=>jump(row.start)}><small>{clock(row.start)}</small><span>{row.label}</span></button>)}</nav>}
   <div className="tour-reading"><a href={`${MEDIA}/zh-CN.vtt`} download="紫微研习-字幕.vtt">下载字幕</a><a href="https://github.com/yuguo-Jack/Ziwei_doushu#快速开始" target="_blank" rel="noreferrer">安装说明 ↗</a></div>
 </dialog>;
}
