import React,{useState} from 'react';
import {Icon,StarMark} from './Icons';
import {CelestialBackdrop} from './Celestial';

const DESTINATIONS={chart:['命盘研究','十二宫与运限'],chat:['问答研读','解读与连续追问'],library:['资料库','原典与课程'],compare:['合盘','双盘关系对照'],tools:['工具箱','历法与传统算法'],records:['本地记录','留存每次研习']};

export default function AppShell({tab,theme,onTheme,ready,children}){
 const [moving,setMoving]=useState(true);
 return <div className="app-shell">
  <CelestialBackdrop moving={moving} theme={theme}/>
  <a className="skip-link" href="#main-content">跳到主要内容</a>
  <aside className="app-sidebar">
   <a className="brand" href="#chart" aria-label="紫微研习首页"><StarMark/><div><strong>紫微<span>研习</span></strong><small>星有所位 · 言有所据</small></div></a>
   <nav aria-label="主导航">{Object.entries(DESTINATIONS).map(([key,[label,description]])=><a key={key} href={'#'+key} aria-label={label} aria-current={tab===key?'page':undefined} className={tab===key?'active':''}><Icon name={key}/><span>{label}<small>{description}</small></span><Icon name="arrow" size={14} className="nav-arrow"/></a>)}</nav>
   <div className="sidebar-close"><div className="sidebar-seal" aria-hidden="true">紫<br/>微</div><p>观星不离其位<br/>研习不离其本</p><span>本地知识库 · Codex 研读</span></div>
  </aside>
  <div className="app-content">
   <header className="app-topbar"><div className="workspace-name"><Icon name={tab}/><span>紫微研习室</span><i/><span>{DESTINATIONS[tab][0]}</span></div><div className="header-right"><span className={'connection-state '+(ready?'ready':'')}><i/>{ready?'本地计算就绪':'连接本地计算'}</span><button className="icon-button motion-toggle" aria-label={moving?'停用星光动效':'启用星光动效'} aria-pressed={moving} onClick={()=>setMoving(!moving)}><Icon name={moving?'pause':'play'} size={16}/></button><button className="theme-toggle" aria-label="切换明暗主题" onClick={onTheme}><Icon name={theme==='dark'?'sun':'moon'} size={17}/><span>{theme==='dark'?'日景':'夜景'}</span></button></div></header>
   {children}
   <footer><StarMark/><span>以星为引，循典而读。</span><p>本地计算 · 原文可溯 · 问答由 Codex 完成</p></footer>
  </div>
 </div>;
}
