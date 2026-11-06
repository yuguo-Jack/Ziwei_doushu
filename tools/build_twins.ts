/** Current-engine major-star geometry index; never a database of real people. */
import fs from 'node:fs';import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Solar} from '../repo/node_modules/lunar-javascript/index.js';
import {astro} from '../repo/node_modules/iztro/lib/index';
import {generateChart} from '../repo/lib/ziwei/algorithm';
import {STEMS,BRANCHES} from '../repo/lib/ziwei/constants';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const folder=path.join(root,'indexes','twins-major-split-v1');fs.mkdirSync(folder,{recursive:true});
const mod=(n:number)=>((n%12)+12)%12;
const names=['紫微','天机','太阳','武曲','天同','廉贞','天府','太阴','贪狼','巨门','天相','天梁','七杀','破军'];
function features(lunar:any,h:number){
  const month=Math.abs(lunar.getMonth())+(lunar.getMonth()<0&&lunar.getDay()>15?1:0);
  const ming=mod(month+1-h),shen=mod(month+1+h);
  const stem=(lunar.getYearGanIndex()%5*2+2+mod(ming-2))%10;
  const label=astro.getFiveElementsClass(STEMS[stem] as any,BRANCHES[ming] as any);
  const ju=({'水二局':2,'木三局':3,'金四局':4,'土五局':5,'火六局':6} as any)[label];
  if(!ju)throw Error('Unknown five-elements class '+label);
  let extra=0;while((lunar.getDay()+extra)%ju)extra++;
  const ziwei=mod((lunar.getDay()+extra)/ju%12-1+(extra%2?-extra:extra));
  const tianfu=mod(12-ziwei);
  return [ming,shen,...[0,1,3,4,5,8].map(i=>mod(ziwei-i+2)),...[0,1,2,3,4,5,6,10].map(i=>mod(tianfu+i+2))];
}
// Validate deterministic random and leap/boundary samples against the complete public engine.
let seed=20261105;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/2**32;};
let tested=0;
for(let i=0;i<240;i++){
  const year=1950+Math.floor(random()*77),month=1+Math.floor(random()*12),day=1+Math.floor(random()*28),hour=Math.floor(random()*12);
  const chart=generateChart({year,month,day,hour,gender:i%2?'male':'female'},{leapMonth:'split'});
  const actual=[chart.mingGongBranch,chart.shenGongBranch,...names.map(n=>chart.palaces.find(p=>p.stars.some(s=>s.type==='major'&&s.name===n))!.branch)];
  const thin=features(Solar.fromYmd(year,month,day).getLunar(),hour);
  if(JSON.stringify(thin)!==JSON.stringify(actual))throw Error(JSON.stringify({year,month,day,hour,thin,actual}));
  tested++;
}
const output=path.join(folder,'features.jsonl'),fd=fs.openSync(output,'w');let rows=0;
for(let year=1950;year<=2026;year++){
  for(let t=Date.UTC(year,0,1);t<Date.UTC(year+1,0,1);t+=86400000){
    const date=new Date(t),month=date.getUTCMonth()+1,day=date.getUTCDate(),lunar=Solar.fromYmd(year,month,day).getLunar();
    fs.writeSync(fd,JSON.stringify([year,month,day,Array.from({length:12},(_,h)=>features(lunar,h))])+'\n');rows+=12;
  }
  process.stderr.write(`twins ${year} ${rows}\n`);
}
fs.closeSync(fd);
fs.writeFileSync(path.join(folder,'build.json'),JSON.stringify({rows,chart_configurations_with_two_genders:rows*2,validated_native_samples:tested,features:['ming_branch','shen_branch',...names],
  profile:{engine_revision:'a600484a49255039d0725f1ba9e11ca81a948f97',leap_month:'split',feature_scope:'14 major-star positions plus ming/shen branches; excludes minor stars, brightness and transformations'},
  source_files:['tools/build_twins.ts','repo/lib/ziwei/algorithm.ts','repo/node_modules/iztro/lib/star/location.js','repo/node_modules/iztro/lib/star/majorStar.js']},null,2));
console.log(JSON.stringify({rows,validated_native_samples:tested,output}));
