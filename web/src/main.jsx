import React,{useState,useRef,useEffect} from 'react';
import {createRoot} from 'react-dom/client';
import {run,SAMPLE,TOPICS,download} from './api';
import BirthForm from './components/BirthForm';
import ReadingPanel from './components/ReadingPanel';
import SourcePanel from './components/SourcePanel';
import LibraryView from './components/LibraryView';
import {CompareView,ToolsView,RecordsView} from './components/OtherViews';
import AppShell from './components/AppShell';
import ChatPage from './components/ChatPage';
import {ChartStage,SurfaceIntro,PALACE_TOPICS} from './components/Celestial';
import {Icon} from './components/Icons';
import './style.css';
import './observatory.css';
import './chat.css';

const TABS={chart:'命盘研究',chat:'问答研读',library:'资料库',compare:'合盘',tools:'工具箱',records:'本地记录'};
const VIEWS={natal:'本命',decadal:'大限',yearly:'流年',monthly:'流月',daily:'流日',hourly:'流时'};
const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
function App(){
 const [tab,setTab]=useState(()=>TABS[location.hash.slice(1)]?location.hash.slice(1):'chart');
 const [draft,setDraft]=useState({...SAMPLE}),[isExample,setIsExample]=useState(true),[bound,setBound]=useState(null),[boundExample,setBoundExample]=useState(true),[calculated,setCalculated]=useState(null),[context,setContext]=useState(null);
 const [topic,setTopic]=useState('career'),[options,setOptions]=useState({view:'natal',date:today,method:'xiaoxian',hour:6,decadalIndex:''}),[mode,setMode]=useState('sanhe'),[hidden,setHidden]=useState(false);
 const [chartBusy,setChartBusy]=useState(false),[readBusy,setReadBusy]=useState(false),[exportBusy,setExportBusy]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState(''),[source,setSource]=useState(null);
 const [palaceExpanded,setPalaceExpanded]=useState(false),[saveMode,setSaveMode]=useState(false),[name,setName]=useState('研习命盘'),[theme,setTheme]=useState(()=>localStorage.getItem('ziwei-observatory-theme')||'dark');
 const chartRequest=useRef(0),readRequest=useRef(0),currentTopic=useRef(topic),sourceOpener=useRef(null),sourceRequest=useRef(0),saveInput=useRef(null),messageTimer=useRef(null),committedOptions=useRef(options),retryAction=useRef(null),saveRequest=useRef(false);
 const [saveBusy,setSaveBusy]=useState(false);
 const [chatIntent,setChatIntent]=useState(null),[activeChatScope,setActiveChatScope]=useState(null);
 currentTopic.current=topic;
 function notice(text){setMessage(text);clearTimeout(messageTimer.current);messageTimer.current=setTimeout(()=>setMessage(''),5000);}
 function clearError(){setError('');retryAction.current=null;}
 function fail(error,again){retryAction.current=again;setError(error.message);}
 function retry(){const again=retryAction.current;clearError();if(again)again();else calculate(bound||draft,committedOptions.current);}
 function payloadFor(birth,opt){if(opt.view==='natal'){const p={...birth};delete p.period;return p;}const p={...birth,period:{view:opt.view,target_date:opt.date,annual_method:opt.method,hour:opt.hour}};if(opt.view==='decadal'&&opt.decadalIndex!==''){delete p.period.target_date;p.period.decadal_index=Number(opt.decadalIndex);}return p;}
 async function loadReading(birth,opt,selectedTopic){
   const id=++readRequest.current;setReadBusy(true);setContext(null);clearError();
   try{const d=await run(opt.view==='natal'?'context':'period-context',{payload:payloadFor(birth,opt),topic:selectedTopic,question:`结合实际星位解释${TOPICS[selectedTopic]}，核对借星、运限范围和原文适用条件`});if(id===readRequest.current)setContext(d);}
   catch(e){if(id===readRequest.current)fail(e,()=>loadReading(birth,opt,selectedTopic));}finally{if(id===readRequest.current)setReadBusy(false);}
 }
 async function calculate(birth=draft,opt=options,newMode=mode,hide=hidden,example=bound&&JSON.stringify(birth)===JSON.stringify(bound)?boundExample:isExample){
   const id=++chartRequest.current;readRequest.current++;setReadBusy(false);setChartBusy(true);setOptions(opt);clearError();
   try{const d=await run(opt.view==='natal'?'chart':'period',{payload:payloadFor(birth,opt),mode:newMode,hide_birth:hide});if(id!==chartRequest.current)return;
     committedOptions.current=opt;setCalculated(d);setBound({...birth});setBoundExample(example);setOptions(opt);setMode(newMode);setHidden(hide);setContext(null);loadReading(birth,opt,currentTopic.current);
   }catch(e){if(id===chartRequest.current){setOptions(committedOptions.current);fail(e,()=>calculate(birth,opt,newMode,hide,example));}}finally{if(id===chartRequest.current)setChartBusy(false);}
 }
 useEffect(()=>{calculate({...SAMPLE},{view:'natal',date:today,method:'xiaoxian',hour:6,decadalIndex:''},'sanhe',false,true);const change=()=>{const next=location.hash.slice(1);if(TABS[next])setTab(next);};window.addEventListener('hashchange',change);return()=>window.removeEventListener('hashchange',change);},[]);
 useEffect(()=>{document.documentElement.dataset.theme=theme;localStorage.setItem('ziwei-observatory-theme',theme);},[theme]);
 useEffect(()=>{if(!source)return;document.querySelector('.source-close')?.focus({preventScroll:true});if(matchMedia('(max-width:1100px)').matches)document.querySelector('.source-inspector')?.scrollIntoView({block:'start'});const escape=e=>{if(e.key==='Escape')closeSource();};document.addEventListener('keydown',escape);return()=>document.removeEventListener('keydown',escape);},[source]);

 function closeSource(){sourceRequest.current++;const id=source?.id;setSource(null);requestAnimationFrame(()=>{const old=sourceOpener.current;const target=old?.isConnected?old:Array.from(document.querySelectorAll('[data-evidence-id]')).find(el=>el.dataset.evidenceId===id);target?.focus({preventScroll:true});});}
 useEffect(()=>{if(saveMode)saveInput.current?.focus();},[saveMode]);
 function switchView(view){let method=options.method;if(['monthly','daily','hourly'].includes(view)&&method!=='taishui'){method='taishui';notice('流月、流日、流时采用已实现的太岁体系；与网站小限子层未核为相同。');}const next={...options,view,method};if(bound)calculate(bound,next);else setOptions(next);}
 async function openSource(id){const requestId=++sourceRequest.current;sourceOpener.current=document.activeElement;try{const data=await run('source',{id});if(requestId===sourceRequest.current)setSource({...data,id});}catch(e){if(requestId===sourceRequest.current)notice(e.message);}}
 async function save(e){e?.preventDefault();if(saveRequest.current)return;saveRequest.current=true;setSaveBusy(true);clearError();try{await run('personal',{operation:'save',kind:'profile',title:name,payload:bound});setSaveMode(false);notice('命盘已保存，可在本地记录查看。');}catch(e){fail(e,()=>save());}finally{saveRequest.current=false;setSaveBusy(false);}}
 async function exportReport(){setExportBusy(true);clearError();try{const d=await run('report',{payload:payloadFor(bound,committedOptions.current),hide_birth:hidden,mode});const a=document.createElement('a');a.href='/exports/'+d.file_stem+'.html';a.target='_blank';a.rel='noopener';a.click();notice('13主题HTML、PDF、PNG、SVG和Markdown已保存在exports。');}catch(e){fail(e,()=>exportReport());}finally{setExportBusy(false);}}
 function openAsk(scope,question){sourceRequest.current++;setSource(null);setChatIntent({id:crypto.randomUUID(),scope,question});location.hash='chat';}
 function askSource(id){const scope={mode:'source',source_id:id};if(tab==='chart'&&bound&&!chartBusy&&!dirty){scope.payload=payloadFor(bound,committedOptions.current);scope.topic=topic;scope.is_example=boundExample;}if(tab==='chat'&&activeChatScope?.payload&&['chart','source'].includes(activeChatScope.mode)){scope.payload=activeChatScope.payload;scope.topic=activeChatScope.topic;scope.is_example=!!activeChatScope.is_example;}openAsk(scope,scope.payload?'请解释这条资料的含义、上下文和适用条件，并核对它与当前命盘的关系，给出出处。':'请通俗解释这条资料的含义、上下文及适用条件，说明容易误解的地方，给出出处。');}
 async function png(){try{const image=new Image();const url=URL.createObjectURL(new Blob([calculated.svg],{type:'image/svg+xml'}));await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src=url;});const canvas=document.createElement('canvas');canvas.width=2400;canvas.height=2400;canvas.getContext('2d').drawImage(image,0,0,2400,2400);URL.revokeObjectURL(url);canvas.toBlob(blob=>{if(blob)download(blob,'ziwei-chart.png','image/png');else notice('PNG导出失败，可先导出SVG。');});}catch(e){notice('PNG导出失败：'+e.message);}}
 function selectPalace(branch){const p=calculated.chart.palaces.find(p=>p.branch===branch);if(!p)return;const label=calculated.period?.selected.palaces.find(p=>p.branch===branch)?.period_palace||p.name;const next=PALACE_TOPICS[label.replace('宫','')];if(next){setTopic(next);loadReading(bound,committedOptions.current,next);}}
 const dirty=bound&&JSON.stringify(draft)!==JSON.stringify(bound);
 const chartScope=bound?{mode:'chart',payload:payloadFor(bound,committedOptions.current),topic,is_example:boundExample}:null;
 return <AppShell tab={tab} theme={theme} onTheme={()=>setTheme(theme==='light'?'dark':'light')} ready={!!bound}>
 <main id="main-content"><div className="page-title"><SurfaceIntro tab={tab}/>{tab==='chart'&&<div className="page-actions">{saveMode?<form className="save-inline" onSubmit={save}><input aria-label="命盘名称" ref={saveInput} value={name} required maxLength={120} onChange={e=>setName(e.target.value)}/><button type="submit" disabled={saveBusy}>{saveBusy?'正在保存…':'确认保存'}</button><button type="button" disabled={saveBusy} onClick={()=>setSaveMode(false)}>取消</button></form>:<button aria-label="保存命盘" title="保存命盘" disabled={!bound||chartBusy} onClick={()=>setSaveMode(true)}><Icon name="save" size={16}/>保存命盘</button>}<button aria-label={exportBusy?"正在生成报告…":"导出报告"} title="导出报告" disabled={!bound||chartBusy||exportBusy} onClick={exportReport}><Icon name="download" size={16}/>{exportBusy?'正在生成报告…':'导出报告'}</button></div>}</div>
 {error&&<div className="inline-error" role="alert"><span>{error}</span><button onClick={retry}>重试</button></div>}
 {tab==='chart'&&<>{dirty&&<p className="scope-notice">出生资料已修改，当前图和依据仍属于上次已排{boundExample?'示例命盘':'命盘'}；点击“排盘并查资料”更新。</p>}<div className="study-grid"><BirthForm isExample={isExample} value={draft} onChange={value=>{setDraft(value);setIsExample(false);}} onSubmit={()=>calculate(draft,{...options,view:'natal'},mode,hidden,isExample)} busy={chartBusy}/><section className="panel chart-panel" aria-label="命盘研究图"><div className="time-toolbar"><div className="seg" aria-label="排盘层次">{Object.entries(VIEWS).map(([key,label])=><button key={key} aria-pressed={options.view===key} disabled={chartBusy} className={options.view===key?'active':''} onClick={()=>switchView(key)}>{label}</button>)}</div>{options.view!=='natal'&&<input aria-label="运限目标日期" type="date" value={options.date} onChange={e=>{const next={...options,date:e.target.value};setOptions(next);if(bound&&next.view!=='natal')calculate(bound,next);}}/>}</div>
 {options.view!=='natal'&&<div className="period-options"><label>流年体系<select aria-label="流年体系" value={options.method} onChange={e=>{const next={...options,method:e.target.value};calculate(bound,next);}}><option value="xiaoxian">小限</option><option value="taishui">太岁</option></select></label>{options.view==='decadal'&&<label>选择大限<select aria-label="选择大限" value={options.decadalIndex} onChange={e=>calculate(bound,{...options,decadalIndex:e.target.value})}><option value="">按目标日期</option>{calculated?.chart.daXians.map((dx,i)=><option key={i} value={i}>{dx.startAge}–{dx.endAge} · {dx.palaceName}</option>)}</select></label>}{options.view==='hourly'&&<label>时辰<select value={options.hour} onChange={e=>calculate(bound,{...options,hour:Number(e.target.value)})}>{'子丑寅卯辰巳午未申酉戌亥'.split('').map((n,i)=><option key={n} value={i}>{n}时</option>)}</select></label>}</div>}
 <ChartStage calculated={calculated} topic={topic} busy={chartBusy} hidden={hidden} onSelect={selectPalace}/>
 {calculated?.period&&<p className="muted period-note">{calculated.period.selected.name} · 农历流年 {calculated.period.target_lunar_year} · 虚岁 {calculated.period.nominal_age}；{calculated.period.annual_method==='xiaoxian'?'小限':'太岁'}体系。</p>}
 {calculated&&<details className="palace-reader" open={palaceExpanded} onToggle={e=>setPalaceExpanded(e.currentTarget.open)}><summary>逐宫文字 · 查看全部星曜</summary><div className="palace-reader-grid">{calculated.chart.palaces.map(p=><article key={p.branch}><h3>{'子丑寅卯辰巳午未申酉戌亥'[p.branch]} · {p.name}</h3><p>{p.stars.filter(s=>s.type==='major').map(s=>s.name+(s.brightnessRaw?'（'+s.brightnessRaw+'）':'')+(s.siHua?'化'+s.siHua:'')).join('、')||'无十四主星；借看'+(p.borrowedStars||[]).join('、')}</p><p className="muted">{p.stars.filter(s=>s.type!=='major').map(s=>s.name+(s.siHua?'化'+s.siHua:'')).join('、')}</p></article>)}</div></details>}
 <div className="chart-bottom"><div className="seg">{Object.entries({sanhe:'三合',feixing:'飞星',sihua:'四化'}).map(([key,label])=><button key={key} aria-pressed={mode===key} className={mode===key?'active':''} disabled={chartBusy} onClick={()=>calculate(bound,options,key,hidden)}>{label}</button>)}</div><div className="chart-download"><button disabled={!calculated||chartBusy} onClick={()=>calculate(bound,options,mode,!hidden)}>{hidden?'显示生辰':'隐藏生辰'}</button><button disabled={!calculated||chartBusy} onClick={()=>download(calculated.svg,'ziwei-chart.svg','image/svg+xml')}>SVG</button><button disabled={!calculated||chartBusy} onClick={png}>PNG</button></div></div></section>
 {source?<SourcePanel source={source} onClose={closeSource} notice={notice} onAsk={askSource}/>:<ReadingPanel context={context} topic={topic} onTopic={next=>{setTopic(next);if(bound)loadReading(bound,committedOptions.current,next);}} busy={chartBusy||readBusy} onSource={openSource} canAsk={!!bound&&!dirty} onAsk={()=>openAsk(chartScope,`请结合当前已排命盘解读${TOPICS[topic]}，说明盘面事实、相关原典、适用条件与还不能下结论的部分，并给出出处。`)}/>}</div></>}
 <div className={source&&tab!=='chart'?'with-source':''}><div><div hidden={tab!=='chat'}><ChatPage active={tab==='chat'} intent={chatIntent} chartScope={chartScope} chartReady={!!bound&&!chartBusy&&!dirty} onSource={openSource} onScope={setActiveChatScope} onSelection={()=>{sourceRequest.current++;setSource(null);}} notice={notice}/></div>{tab==='library'&&<LibraryView onSource={openSource} notice={notice}/>}{tab==='compare'&&<CompareView first={bound||draft} firstIsExample={boundExample} notice={notice} onSource={openSource} onAsk={openAsk}/>}{tab==='tools'&&<ToolsView birth={bound||draft} birthIsExample={boundExample} notice={notice} onAsk={openAsk}/>}{tab==='records'&&<RecordsView onLoad={data=>{setDraft(data);setIsExample(false);location.hash='chart';calculate(data,{...options,view:'natal'},mode,hidden,false);}} onSource={openSource} notice={notice}/>}</div>{source&&tab!=='chart'&&<SourcePanel source={source} onClose={closeSource} notice={notice} onAsk={askSource}/>}</div>
 </main>{message&&<div className="toast" role="status"><Icon name="check" size={17}/>{message}</div>}
 </AppShell>;
}
createRoot(document.getElementById('root')).render(<App/>);
