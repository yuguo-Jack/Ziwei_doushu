export async function run(action,params={}){
  let response;
  try{response=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,...params})});}
  catch{throw Error('无法连接本地服务，请确认工作台已启动后重试。');}
  let data;
  try{data=await response.json();}catch{throw Error('本地服务暂未返回完整结果，请稍后重试。');}
  if(!data||typeof data!=='object'||Array.isArray(data))throw Error('本地服务暂未返回完整结果，请稍后重试。');
  if(!response.ok||data.error)throw Error(data.error||'本地服务请求失败');return data;
}
export const TOPICS={overview:'命格总览',personality:'性格',love:'感情婚姻',career:'事业职业',wealth:'财富财运',health:'健康疾厄',family:'兄弟合伙',children:'子女',move:'迁移',friends:'人际交友',home:'田宅',spirit:'福德',parents:'父母'};
export const SAMPLE={year:1990,month:1,day:1,clock_hour:8,clock_minute:30,gender:'male',longitude:118.78,place_name:'南京',timezone:'Asia/Shanghai',brightness:'QS',leap_month:'split',late_zi:'next-day'};
export function birthLabel(key){const p=String(key).split('-');return p.length===5?`公历 ${p[0]}年${Number(p[1])}月${Number(p[2])}日 · ${'子丑寅卯辰巳午未申酉戌亥'[Number(p[3])]}时 · ${p[4]==='male'?'男':'女'}`:String(key);}
export function download(data,name,type){const url=URL.createObjectURL(new Blob([data],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
export async function copy(text){if(navigator.clipboard)await navigator.clipboard.writeText(text);else{const el=document.createElement('textarea');el.value=text;document.body.append(el);el.select();document.execCommand('copy');el.remove();}}
