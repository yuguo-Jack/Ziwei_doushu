import React,{useState} from 'react';
import {TOPICS} from '../api';
import {Icon} from './Icons';
import {titleLabel,conditionLabel} from '../presentation';
export default function ReadingPanel({context,topic,onTopic,busy,onSource,onAsk,canAsk=true}){
 const geometry=context?.topic_geometry||context?.topic_facts;
 const raw=context?.archived_case?.topics?.[topic];
 const palace=geometry?(context?.period?`${context.period.selected.name}${geometry.period_palace}（本命${geometry.natal_palace}）`:geometry.palace):'';
 const facts=geometry?geometry.is_empty?`${palace}无十四主星，借看对宫${(geometry.borrowed_stars||[]).join('、')}。`:`${palace}：${(geometry.physical_main_stars||[]).map(s=>typeof s==='string'?s:s.name).join('、')}。`:'排盘后显示当前宫位事实。';
 const hits=context?.evidence?.hits||[];
 return <aside className="panel reading"><h2><Icon name="library" size={17}/>研读与依据</h2><div className="reading-body"><label className="field topic-field">研究主题<select aria-label="研究主题" value={topic} onChange={e=>onTopic(e.target.value)}>{Object.entries(TOPICS).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
 <h3>当前盘面</h3><p className="fact">{busy?'正在检索与核对适用条件…':facts}</p>
 {context?.period&&<p className="muted">{context.period.selected.name} · {context.period.target_date} · {context.period.annual_method==='taishui'?'太岁':'小限'}体系</p>}
 <h3>原文与出处</h3><div className="source-list">{hits.slice(0,4).map(h=><button data-evidence-id={h.evidence_id} key={h.chunk_id} onClick={()=>onSource(h.evidence_id)}><span>{titleLabel(h.title)}</span><svg className="chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="m6 3 5 5-5 5" fill="none" stroke="currentColor" strokeWidth="1.5"/></svg></button>)}</div>
 {context?.evidence?.degraded_to_lexical&&<p role="status" className="error">语义检索暂不可用，本次改用原文关键词查找；出处仍可核对。</p>}
 <details className="conditions"><summary>查看适用条件</summary>{hits.map(h=><div key={h.chunk_id}><h4>{titleLabel(h.title)}</h4><p>{conditionLabel(h)}</p>{!['adapter_code','code_rule','source_code'].includes(h.kind)&&<p>{(h.conditions||[]).join('；')||'还需结合完整原文核对，不能默认无条件成立。'}</p>}</div>)}</details>
 <p className="muted">旧版案例与当前排盘分别核对。</p>
 {raw&&<details><summary>阅读旧版本命解读</summary>{context?.archived_case_view?<div className="chat-answer archived-reading" dangerouslySetInnerHTML={{__html:context.archived_case_view}}/>:<div className="verbatim">{raw.text}</div>}<p className="muted">旧版存档采用不同的亮度口径，不能当作当前流年原文。</p></details>}
 <button className="outline wide codex" disabled={!canAsk||busy} onClick={onAsk}><Icon name="sparkle" size={17}/>解读当前命盘</button></div></aside>;
}
