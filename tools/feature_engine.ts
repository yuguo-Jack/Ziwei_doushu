import {astro} from '../repo/node_modules/iztro/lib/index';
import {Solar} from '../repo/node_modules/lunar-javascript/index.js';
import {lunarToSolar} from '../repo/lib/ziwei/lunar-solar';
import {isValidGregorianDate,shiftGregorianDate} from '../repo/lib/ziwei/true-solar-time';
import {resolveEffectiveLunarDate} from '../repo/lib/ziwei/algorithm';
import {BRANCHES,STEMS,SI_HUA_TABLE} from '../repo/lib/ziwei/constants';
import {getChildhoodDaXianPalace} from '../repo/lib/ziwei/yunxian-context';
import {SCHOOL_AX} from '../repo/lib/ziwei/school-tables.generated';
import {schoolStarBrightness} from '../repo/lib/ziwei/school-data';

export const GENG_VARIANTS:Record<string,string[]>={
  GYWYT:['太阳','武曲','太阴','天同'],GYWTY:['太阳','武曲','天同','太阴'],
  GYWFT:['太阳','武曲','天府','天同'],GYWFX:['太阳','武曲','天府','天相'],GYWTX:['太阳','武曲','天同','天相']
};
const rev='a600484a49255039d0725f1ba9e11ca81a948f97';
const source=(file:string)=>`https://github.com/Renhuai123/ziwei-doushu/blob/${rev}/lib/ziwei/${file}`;
const mod=(n:number)=>((n%12)+12)%12;
const sihua=['禄','权','科','忌'];
export function applyStaticSchoolVariants(chart:any,input:any,brightness:any){
  const ky=input.kuiyue_school??'qs1',jk=input.jiekong_school??'double';
  const tables:any={qs1:SCHOOL_AX.KY_ARR1,qs2:SCHOOL_AX.KY_ARR2,'zhong-yiming':SCHOOL_AX.KY_ARR3,network:SCHOOL_AX.KY_ARR4};
  if(!Object.hasOwn(tables,ky)||!['double','single','zhanyan'].includes(jk))throw Error('魁钺或截空排表不支持。');
  function move(name:string,branch:number){
    let star:any;
    for(const p of chart.palaces){const found=p.stars.find((s:any)=>s.name===name);if(found)star=found;p.stars=p.stars.filter((s:any)=>s.name!==name);}
    if(!star)throw Error(`基准盘缺少${name}，无法切换表。`);
    const raw=schoolStarBrightness(name,branch,brightness==='default'?'QS':brightness);
    star.brightnessRaw=raw;star.brightness=raw===undefined?undefined:['庙','旺'].includes(raw)?'bright':['陷','不','闲'].includes(raw)?'dim':'normal';
    chart.palaces.find((p:any)=>p.branch===branch).stars.push(star);
  }
  if(ky!=='qs1'){
    const row=tables[ky][chart.lunarInfo.yearStem+1];move('天魁',row[0]-1);move('天钺',row[1]-1);
  }
  if(jk!=='double'){
    const table=jk==='single'?SCHOOL_AX.JK_ARR1:SCHOOL_AX.JK_ARR3;
    move('截空',table[chart.lunarInfo.yearStem+1]-1);
    for(const p of chart.palaces)p.stars=p.stars.filter((s:any)=>s.name!=='副截');
  }
  return {kuiyue_school:ky,jiekong_school:jk,source_url:source('school-tables.generated.ts'),
    scope:'Disclosed KY_ARR1..4 and JK_ARR1..3 tables only; 旬空/副旬 retain the pinned native baseline. Not a reconstruction of the missing school-patches module.'};
}
export function exactClockPillars(input:any,solar:any,trueSolarDay:any,utc:number,dst:number){
  const beijing=new Date(Date.UTC(input.year,input.month-1,input.day,input.clock_hour,input.clock_minute??0)-(utc+dst)*60000+480*60000);
  const eight=Solar.fromYmdHms(beijing.getUTCFullYear(),beijing.getUTCMonth()+1,beijing.getUTCDate(),beijing.getUTCHours(),beijing.getUTCMinutes(),0).getLunar().getEightChar();
  const late=solar.branch===0&&solar.normalizedMinutes>=1380,rule=input.late_zi??'next-day';
  const dayDate=shiftGregorianDate(trueSolarDay,late&&rule==='next-day'?1:0);
  const lunar=Solar.fromYmd(dayDate.year,dayDate.month,dayDate.day).getLunar();
  const day=lunar.getDayInGanZhi(),dayStem=STEMS.indexOf(day[0]);
  if(dayStem<0)throw Error('日柱天干无法解析。');
  const hourBase=mod(dayStem+(late&&rule==='day-cur-time-next'?1:0))%10;
  const hourStem=(hourBase%5*2+solar.branch)%10;
  return {pillars:[eight.getYear(),eight.getMonth(),day,STEMS[hourStem]+BRANCHES[solar.branch]],
    policy:'year/month: actual instant converted to UTC+8 solar-term clock; day/hour: selected local true-solar and late-Zi policy',
    solar_term_reference_utc8:beijing.toISOString().slice(0,19),true_solar_civil_date:trueSolarDay,
    source:'lunar-javascript 1.7.7 plus explicit five-rats hour-stem formula; not a claim that all BaZi schools agree'};
}
export function transforms(stem:number,geng='GYWYT'){
  return Object.fromEntries((stem===6?GENG_VARIANTS[geng]:SI_HUA_TABLE[stem]).map((star,i)=>[sihua[i],star]));
}
export function calendarOperation(input:any){
  if(input.calendar==='lunar'){
    if(input.is_leap_month!==undefined&&typeof input.is_leap_month!=='boolean')throw Error('is_leap_month 必须为布尔值。');
    const date=lunarToSolar(input.year,input.month,input.day,input.is_leap_month??false);
    if(!date)throw Error('农历日期非法、闰月不存在或超过1900–2050范围。');
    return {calendar:'lunar',input:{year:input.year,month:input.month,day:input.day,is_leap_month:input.is_leap_month??false},solar:date,source_url:source('lunar-solar.ts')};
  }
  if(input.calendar!==undefined&&input.calendar!=='solar')throw Error('calendar 只能为 solar 或 lunar。');
  if(!isValidGregorianDate(input.year,input.month,input.day)||input.year<1900||input.year>2100)throw Error('公历日期不存在或超过1900–2100范围。');
  const lunar=Solar.fromYmd(input.year,input.month,input.day).getLunar();
  return {calendar:'solar',solar:{year:input.year,month:input.month,day:input.day},lunar:{year:lunar.getYear(),month:Math.abs(lunar.getMonth()),day:lunar.getDay(),is_leap_month:lunar.getMonth()<0},source_url:source('lunar-solar.ts')};
}
export function liurenOperation(input:any){
  const date=calendarOperation(input);const solar=date.solar;
  const lunar=Solar.fromYmd(solar.year,solar.month,solar.day).getLunar();
  let branch=input.hour;
  if(input.clock_hour!==undefined){
    if(input.hour!==undefined)throw Error('hour 与 clock_hour 不可同时指定。');
    if(!Number.isInteger(input.clock_hour)||input.clock_hour<0||input.clock_hour>23)throw Error('钟表小时非法。');
    branch=input.clock_hour===23?0:Math.floor((input.clock_hour+1)/2);
  }
  if(!Number.isInteger(branch)||branch<0||branch>11)throw Error('需要明确的时辰hour 0–11或clock_hour 0–23。');
  const names=['大安','留连','速喜','赤口','小吉','空亡'];
  const month=Math.abs(lunar.getMonth()),day=lunar.getDay();
  const m=(month-1)%6,d=(m+day-1)%6,h=(d+branch)%6;
  return {operation:'liuren',solar,lunar:{year:lunar.getYear(),month,day,is_leap_month:lunar.getMonth()<0},hour_branch:BRANCHES[branch],
    steps:[{step:'月',count:month,result:names[m]},{step:'日',count:day,result:names[d]},{step:'时',count:branch+1,result:names[h]}],
    result:names[h],method:'inclusive counting; lunar leap month uses its month number; 23:00 stays on the civil calendar day; no true-solar correction',
    source_url:'https://ouranic.cn/liuren',usage:'传统文化算法演示；算术结果不是事件必然发生的证据。'};
}
export function flightInfo(chart:any,geng='GYWYT'){
  return {source_url:source('sihua.ts'),geng_year_sihua:geng,
    palaces:chart.palaces.map((p:any)=>({palace:p.name,branch:p.branch,stem:STEMS[p.stem],
      transforms:Object.entries(transforms(p.stem,geng)).map(([kind,star])=>{
        const target=chart.palaces.find((q:any)=>q.stars.some((s:any)=>s.name===star));
        return {kind,star,target_palace:target?.name??null,target_branch:target?.branch??null,self:target?.branch===p.branch,opposite:target?.branch===mod(p.branch+6)};
      })})),
    applicability:'Palace-stem transformations are factual under the selected table; no automatic relationship/event judgment.'};
}
export function periodOperation(chart:any,birth:any,input:any){
  const request=input.period??{};
  const allowed=new Set(['view','target_date','target_year','hour','decadal_index','annual_method']);
  for(const k of Object.keys(request))if(!allowed.has(k))throw Error(`未知运限字段：${k}`);
  const view=request.view??'yearly',annual=request.annual_method??'xiaoxian';
  if(!['natal','decadal','yearly','monthly','daily','hourly','age'].includes(view))throw Error('运限view不支持。');
  if(!['xiaoxian','taishui'].includes(annual))throw Error('annual_method 必须为 xiaoxian 或 taishui。');
  if(['monthly','daily','hourly'].includes(view)&&annual!=='taishui')throw Error('流月/流日/流时目前只实现已核的iztro太岁体系；请显式选annual_method=taishui，不能冒套为网站小限体系。');
  let target=request.target_date??input.as_of;
  if(['target_date','target_year','decadal_index'].filter(k=>request[k]!==undefined).length>1)throw Error('目标公历日、农历流年和大限索引不能同时指定。');
  if(request.target_year!==undefined){
    if(request.target_date!==undefined)throw Error('target_year(农历流年)与target_date不可同时指定。');
    const date=lunarToSolar(request.target_year,1,1,false);if(!date)throw Error('目标农历年范围1900–2050。');
    target=`${date.year}-${String(date.month).padStart(2,'0')}-${String(date.day).padStart(2,'0')}`;
  }
  if(request.decadal_index!==undefined){
    if(!Number.isInteger(request.decadal_index)||!chart.daXians[request.decadal_index])throw Error('大限索引不存在。');
    const date=lunarToSolar(chart.lunarInfo.lunarYear+chart.daXians[request.decadal_index].startAge-1,1,1);
    if(!date)throw Error('所选大限超过历法适配范围。');target=`${date.year}-${date.month}-${date.day}`;
  }
  if(typeof target!=='string'||!/^\d{4}-\d{1,2}-\d{1,2}$/.test(target))throw Error('目标日期应为公历YYYY-MM-DD。');
  const [y,m,d]=target.split('-').map(Number);
  if(!isValidGregorianDate(y,m,d)||y<1900||y>2100)throw Error('目标公历日期非法。');
  target=`${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
  const hour=request.hour??6;
  if(!Number.isInteger(hour)||hour<0||hour>11)throw Error('目标时辰hour应为0–11。');
  const lunar=Solar.fromYmd(y,m,d).getLunar(),age=lunar.getYear()-chart.lunarInfo.lunarYear+1;
  if(age<1)throw Error('目标日期早于出生农历年，不生成运限。');
  const exactBirth=Solar.fromYmd(birth.year,birth.month,birth.day),exactTarget=Solar.fromYmd(y,m,d);
  if(exactTarget.getJulianDay()<exactBirth.getJulianDay())throw Error('目标日期早于出生日期。');
  const effective=resolveEffectiveLunarDate(birth.year,birth.month,birth.day,input.leap_month??'split');
  let astrolabe:any;
  if((input.leap_month??'split')!=='split'&&effective.rawLunarMonth<0){
    astrolabe=astro.byLunar(`${effective.lunarYear}-${effective.lunarMonth}-${effective.lunarDay}`,birth.hour,birth.gender==='male'?'男':'女',effective.isLeapMonth,false,'zh-CN');
  }else astrolabe=astro.bySolar(`${birth.year}-${birth.month}-${birth.day}`,birth.hour,birth.gender==='male'?'男':'女',true,'zh-CN');
  const flow:any=astrolabe.horoscope(target,hour).toJSON();
  const geng=input.geng_year_sihua??'GYWYT';
  const yearStem=STEMS.indexOf(lunar.getYearGan());
  const dxIndex=chart.daXians.findIndex((q:any)=>age>=q.startAge&&age<=q.endAge);
  const dx=dxIndex>=0?chart.daXians[dxIndex]:null;
  const childhood=age<chart.daXians[0].startAge;
  const dxPalace=dx?chart.palaces.find((p:any)=>p.branch===dx.palaceBranch):childhood?getChildhoodDaXianPalace(chart,lunar.getYear()):null;
  function layer(name:string,anchor:number|null,stem:number,extra:any={}){
    return {name,anchor_branch:anchor,anchor_palace:chart.palaces.find((p:any)=>p.branch===anchor)?.name??null,stem:STEMS[stem],transforms:transforms(stem,geng),
      palaces:anchor===null?[]:chart.palaces.map((p:any)=>({branch:p.branch,natal_palace:p.name,period_palace:chart.palaces.find((q:any)=>q.branch===mod(p.branch-anchor!+chart.mingGongBranch))?.name,
        physical_main_stars:p.stars.filter((s:any)=>s.type==='major'),is_empty:p.isEmpty,borrowed_stars:p.borrowedStars??[]})),...extra};
  }
  const fromFlow=(item:any)=>item.index>=0?mod(item.index+2):null;
  const layers:any={natal:layer('本命',chart.mingGongBranch,chart.lunarInfo.yearStem),
    decadal:layer(dx?'大限':childhood?'童限':'超出大限范围',dxPalace?.branch??null,dxPalace?.stem??chart.lunarInfo.yearStem,{index:dxIndex,range:dx?[dx.startAge,dx.endAge]:childhood?[1,chart.daXians[0].startAge-1]:null}),
    yearly:layer(annual==='xiaoxian'?'小限流年':'太岁流年',fromFlow(annual==='xiaoxian'?flow.age:flow.yearly),yearStem),
    age:layer('小限',fromFlow(flow.age),yearStem)};
  for(const key of ['monthly','daily','hourly'])layers[key]=layer({monthly:'流月',daily:'流日',hourly:'流时'}[key]!,fromFlow(flow[key]),STEMS.indexOf(flow[key].heavenlyStem),{method:'iztro taishui hierarchy; not the proprietary website period engine'});
  const chosen=layers[view];
  return {view,target_date:target,target_lunar_year:lunar.getYear(),lunar:{month:lunar.getMonth(),day:lunar.getDay()},hour,nominal_age:age,annual_method:annual,
    selected:chosen,layers,source_urls:[source('yunxian-context.ts'),source('sihua.ts'),'https://github.com/SylarLong/iztro/tree/v2.6.1'],
    interpretation_status:'Calculated layers plus original natal stars only; no released full period-reading archive. Do not relabel natal text as a period prediction.',
    caveats:['小限与太岁流年分开；本工具未核为网站闭源运限同款。','流月/日/时仅太岁层级；未将未知小限子层规则拼接。','目标日期是公历，target_year则明确为农历流年；时辰为0–11。']};
}
