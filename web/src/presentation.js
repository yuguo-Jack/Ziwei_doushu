export const DOMAIN_LABELS={ziwei:'紫微斗数',yijing:'易经',fengshui:'风水',tieban:'铁板神数',tianji:'天纪课程',historical_ziwei:'历史紫微',renji:'历史医籍',all:'全部资料'};
export const KIND_LABELS={adapter_code:'排盘说明',source_code:'判定方法',code_rule:'判定方法',course_quote:'课程引文',course_quotes:'课程引文',course_quote_group:'课程引文',classic_transcription:'古籍原文',compiled_secondary:'整理资料',historical_medical_course_quotes:'历史医籍课程',quarantined_excerpt:'待核节选',unverified_curated_excerpt:'待核节选',dataset_candidate:'旧版案例节选',project_guide:'排盘说明'};
export const BRIGHTNESS_LABELS={QS:'全书亮度表',XD2:'现代修订表二',XD1:'现代修订表一',ZZ:'中州亮度表'};
export const GENG_LABELS={GYWYT:'太阳禄 · 武曲权 · 太阴科 · 天同忌',GYWTY:'太阳禄 · 武曲权 · 天同科 · 太阴忌',GYWFT:'太阳禄 · 武曲权 · 天府科 · 天同忌',GYWFX:'太阳禄 · 武曲权 · 天府科 · 天相忌',GYWTX:'太阳禄 · 武曲权 · 天同科 · 天相忌'};
export const titleLabel=title=>String(title||'研读资料').replaceAll('代码格局规则 / ','格局判定 · ').replaceAll('代码格局规则','格局判定方法');
export function conditionLabel(hit){
 if(hit.applicability==='detected_in_this_chart')return '本次排盘已识别此项格局，仍需结合其他宫位和条件理解。';
 if(hit.applicability?.startsWith('current palace has no main stars'))return '当前宫位没有十四主星，需区分借星与实际同宫。';
 if(['adapter_code','source_code','code_rule','project_guide'].includes(hit.kind))return '这条说明用于核对排盘方法，不等同于古籍断语。';
 return '需结合实际宫位、同宫或借宫关系、庙陷、四化和流派，逐项核对原文条件。';
}
export function locationLabel(locator){
 if(!locator)return '';
 if(Number.isFinite(locator.seconds)){const n=Math.max(0,Math.floor(locator.seconds));return (locator.part?'第'+locator.part+'段 · ':'')+(n>=3600?`${Math.floor(n/3600)}:${String(Math.floor(n%3600/60)).padStart(2,'0')}`:String(Math.floor(n/60)).padStart(2,'0'))+':'+String(n%60).padStart(2,'0');}
 return locator.paragraph!==undefined?'原文第'+locator.paragraph+'段':'';
}
export function timezoneLabel(zone){
 if(!zone)return '默认采用中国标准时间';
 try{return new Intl.DateTimeFormat('zh-CN',{timeZone:zone,timeZoneName:'longGeneric'}).formatToParts(new Date()).find(p=>p.type==='timeZoneName')?.value||'所选地区时区';}catch{return '自定义地区时区';}
}
export function scopeDescription(scope){
 if(!scope)return '知识问答 · 未附带个人命盘';
 if(scope.mode==='knowledge')return (DOMAIN_LABELS[scope.namespace]||'紫微斗数')+' · 知识问答';
 if(scope.mode==='compare')return '已固定甲乙双方资料 · '+({love:'感情',business:'合伙',hierarchy:'上下级',friendship:'朋友'})[scope.relation||'love'];
 if(scope.mode==='source')return '当前选定资料'+(scope.payload?' · 同时结合已排命盘':'');
 const p=scope.payload||{},date=(p.calendar==='lunar'?'农历 ':'公历 ')+`${p.year}年${p.month}月${p.day}日`,who=scope.is_example?'虚构示例':p.gender==='male'?'男命':'女命';
 if(scope.mode==='tool')return ({liuren:'小六壬结果',calendar:'历法换算',twins:'同盘结构','time-candidates':'十二时辰假设'})[scope.tool]+' · '+(scope.tool==='liuren'?(scope.tool_input?`${scope.tool_input.year}年${scope.tool_input.month}月${scope.tool_input.day}日`:'所选时刻'):date);
 return who+' · '+date+' · '+(p.period?(({yearly:'流年',monthly:'流月',daily:'流日',hourly:'流时',decadal:'大限'})[p.period.view]||'运限')+(p.period.target_year?' '+p.period.target_year+'年':p.period.target_date?' '+p.period.target_date:''):'本命');
}
