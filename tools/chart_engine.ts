/** JSON/stdin interface to the pinned engine. No web/backend dependency. */
import fs from 'node:fs';
import * as nodeModule from 'node:module';
import {generateChart,setBrightnessSchool} from '../repo/lib/ziwei/algorithm';
import {calculateTrueSolarTime,resolveZiweiDayOffset,shiftGregorianDate,isValidGregorianDate} from '../repo/lib/ziwei/true-solar-time';
import {isChinaDST,chinaDSTSpan} from '../repo/lib/ziwei/dst-cn';
import {Solar} from '../repo/node_modules/lunar-javascript/index.js';
import {astro} from '../repo/node_modules/iztro/lib/index';
import {calendarOperation,liurenOperation,periodOperation,flightInfo,GENG_VARIANTS,exactClockPillars,applyStaticSchoolVariants} from './feature_engine';
const hooks=(nodeModule as any).registerHooks;
hooks({resolve(s:any,c:any,next:any){return s==='server-only'?{url:'data:text/javascript,',shortCircuit:true}:next(s,c);},
load(u:any,c:any,next:any){return u==='data:text/javascript,'?{format:'commonjs',source:'',shortCircuit:true}:next(u,c);}});
const revision='a600484a49255039d0725f1ba9e11ca81a948f97';
async function main(){
  const input=JSON.parse(fs.readFileSync(0,'utf8'));
  if(!input||Array.isArray(input)||typeof input!=='object')throw new Error('输入必须为JSON对象。');
  if(input._operation==='calendar'){process.stdout.write(JSON.stringify(calendarOperation(input)));return;}
  if(input._operation==='liuren'){process.stdout.write(JSON.stringify(liurenOperation(input)));return;}
  const accepted=new Set(['_operation','year','month','day','gender','hour','clock_hour','clock_minute','longitude','utc_offset_minutes','dst_adjust_minutes','brightness','leap_month','late_zi','as_of','unknown_time','calendar','is_leap_month','name','period','geng_year_sihua','kuiyue_school','jiekong_school','place_name']);
  for(const key of Object.keys(input))if(!accepted.has(key))throw new Error(`未知出生字段：${key}；未静默忽略流派或其它输入。`);
  if(input.place_name!==undefined&&(typeof input.place_name!=='string'||input.place_name.length>120))throw new Error('place_name应为最多120字符的地点标签，计算仍以显式经度和时区为准。');
  const calendar=calendarOperation(input);
  if(input.calendar==='lunar')Object.assign(input,calendar.solar);
  if(input.hour!==undefined&&input.clock_hour!==undefined)throw new Error('hour与clock_hour不能同时指定，避免时辰歧义。');
  if(input.clock_minute!==undefined&&input.clock_hour===undefined)throw new Error('clock_minute需要clock_hour。');
  if(input.late_zi!==undefined&&!['next-day','current-day','all-current','day-cur-time-next'].includes(input.late_zi))throw new Error('late_zi 非法。');
  if(input.period!==undefined&&(!input.period||typeof input.period!=='object'||Array.isArray(input.period)))throw new Error('period必须为JSON对象。');
  const {year,month,day,gender}=input;
  if(!isValidGregorianDate(year,month,day)||year<1900||year>2100)throw new Error('出生日期必须真实存在，支持 1900–2100 年。');
  if(!['male','female'].includes(gender))throw new Error('gender 必须为 male 或 female。');
  let normalized={year,month,day},hour=input.hour,solar:any=null;
  let effectiveUtc:number|null=null,effectiveDst:number|null=null;
  let clockPillars:any=null;
  const notices:string[]=[];
  if(input.unknown_time)throw new Error('时辰不详，不能生成一张确定命盘；请提供时辰或分别比较候选时辰。');
  const leap=input.leap_month??'split';
  if(input.clock_hour!==undefined){
    if(!Number.isInteger(input.clock_hour)||input.clock_hour<0||input.clock_hour>23||!Number.isInteger(input.clock_minute??0)||(input.clock_minute??0)<0||(input.clock_minute??0)>59)throw new Error('钟表时间非法。');
    if(input.longitude!==undefined&&(!Number.isFinite(input.longitude)||input.longitude< -180||input.longitude>180))throw new Error('经度范围为 -180–180。');
    const utc=input.utc_offset_minutes??480;
    if(!Number.isInteger(utc)||utc< -840||utc>840)throw new Error('utc_offset_minutes 非法。');
    const dst=input.dst_adjust_minutes??0;
    if(!Number.isInteger(dst)||Math.abs(dst)>180)throw new Error('dst_adjust_minutes 非法。');
    effectiveUtc=utc;effectiveDst=dst;
    let clock=input.clock_hour*60+(input.clock_minute??0)-dst;
    normalized=shiftGregorianDate(normalized,Math.floor(clock/1440));clock=((clock%1440)+1440)%1440;
    solar=calculateTrueSolarTime({...normalized,clockHour:Math.floor(clock/60),clockMinute:clock%60,longitude:input.longitude,utcOffsetMinutes:utc});
    const late=input.late_zi??'next-day';
    if(!['next-day','current-day','all-current','day-cur-time-next'].includes(late))throw new Error('late_zi 非法。');
    clockPillars=exactClockPillars(input,solar,shiftGregorianDate(normalized,solar.dayOffset),utc,dst);
    normalized=shiftGregorianDate(normalized,resolveZiweiDayOffset(solar,late));hour=solar.branch;
    if(utc===480&&isChinaDST(year,month,day)&&dst===0)notices.push('本日期落在工程夏令时参照表内；未自动减时。请核实输入是否已为标准时间；1988 年等与 IANA 表有分歧。');
    if(input.longitude===undefined)notices.push('未提供经度，按输入标准钟表时间判定时辰，不加经度或均时差。');
  }
  if(!Number.isInteger(hour)||hour<0||hour>11)throw new Error('需要 hour 时辰序号 0–11，或 clock_hour/clock_minute。');
  const brightness=input.brightness??'QS';
  if(!['QS','XD1','XD2','ZZ','default'].includes(brightness))throw new Error('brightness 需为 QS/XD1/XD2/ZZ/default。');
  setBrightnessSchool(brightness);
  const geng=input.geng_year_sihua??'GYWYT';
  if(typeof geng!=='string'||!Object.hasOwn(GENG_VARIANTS,geng))throw new Error('geng_year_sihua不支持。');
  astro.config({mutagens:{庚:GENG_VARIANTS[geng] as any}});
  const chart=generateChart({...normalized,hour,gender,longitude:input.longitude},{leapMonth:leap});
  const staticVariants=applyStaticSchoolVariants(chart,input,brightness);
  const legacyPillars=chart.lunarInfo.fourPillars;
  if(clockPillars){
    chart.lunarInfo.fourPillars=clockPillars.pillars;
    if(chart.lunarInfo.fourPillarsLunar)chart.lunarInfo.fourPillarsLunar=[...chart.lunarInfo.fourPillarsLunar.slice(0,2),...clockPillars.pillars.slice(2)] as any;
  }
  const asOf=input.as_of??new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  if(!/^\d{4}-\d{2}-\d{2}$/.test(asOf))throw new Error('as_of 必须为 YYYY-MM-DD。');
  const [ay,am,ad]=asOf.split('-').map(Number);
  if(!isValidGregorianDate(ay,am,ad))throw new Error('as_of 日期不存在。');
  const referenceLunarYear=Number(Solar.fromYmd(ay,am,ad).getLunar().getYear());
  chart.currentAge=referenceLunarYear-chart.lunarInfo.lunarYear+1;
  chart.currentDaXianIndex=chart.daXians.findIndex(dx=>chart.currentAge>=dx.startAge&&chart.currentAge<=dx.endAge);
  for(const palace of chart.palaces)palace.isCurrentDaXian=!!palace.daXianAge&&chart.currentAge>=palace.daXianAge[0]&&chart.currentAge<=palace.daXianAge[1];
  const {detectPatterns}=await import('../repo/lib/ziwei/patterns');
  const patterns=detectPatterns(chart);
  const key=`${normalized.year}-${String(normalized.month).padStart(2,'0')}-${String(normalized.day).padStart(2,'0')}-${hour}-${gender}`;
  const result:any={engine_revision:revision,input,calendar_conversion:calendar,normalized_birth:{...normalized,hour,gender},birth_key:key,
    calculation_profile:{brightness,leap_month:leap,late_zi:input.late_zi??'next-day',as_of:asOf,age_policy:'lunar-year nominal age: reference lunar year minus birth lunar year plus one',reference_lunar_year:referenceLunarYear,birth_lunar_year:chart.lunarInfo.lunarYear,effective_utc_offset_minutes:effectiveUtc,effective_dst_adjust_minutes:effectiveDst,clock_policy:input.clock_hour!==undefined?'standard time; caller-supplied DST adjustment; longitude + equation of time when longitude supplied':'explicit branch index and caller-resolved chart date; no clock conversion',solar},
    chart,patterns,notices,dst_reference_span:chinaDSTSpan(year),case_compatibility:{status:brightness==='XD2'?'unknown':'partial',
      differences:brightness==='XD2'?['v4 private engine and leap-month details are not fully known']:['current brightness QS/selected school differs from v4 XD2','v4 private engine and leap-month details are not fully known']}};
  result.calculation_profile.geng_year_sihua=geng;
  result.calculation_profile.static_school_variants=staticVariants;
  if(staticVariants.kuiyue_school!=='qs1'||staticVariants.jiekong_school!=='double')result.case_compatibility.differences.push('Selected public auxiliary-star table is not assumed compatible with the legacy archive.');
  result.calculation_profile.four_pillars_precision=clockPillars?clockPillars.policy:'Branch-only input uses a midpoint approximation; exact clock time is unknown.';
  result.calculation_profile.exact_clock_pillars=clockPillars;
  if(clockPillars)result.calculation_profile.legacy_midpoint_four_pillars=legacyPillars;
  result.flights=flightInfo(chart,geng);
  if(input._operation==='period')result.period=periodOperation(chart,result.normalized_birth,{...input,as_of:asOf});
  process.stdout.write(JSON.stringify(result));
}
main().catch(e=>{process.stdout.write(JSON.stringify({error:String(e.message??e)}));process.exitCode=1;});
