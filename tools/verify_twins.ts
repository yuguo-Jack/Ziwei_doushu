/** Verify complete native chart structures after the necessary major-geometry filter. */
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {generateChart,setBrightnessSchool} from '../repo/lib/ziwei/algorithm';
import {astro} from '../repo/node_modules/iztro/lib/index';
import {GENG_VARIANTS,applyStaticSchoolVariants} from './feature_engine';
function signature(c:any){
  return JSON.stringify({ming:c.mingGongBranch,shen:c.shenGongBranch,ju:c.wuxingJu,yearStem:c.lunarInfo.yearStem,yearBranch:c.lunarInfo.yearBranch,
    palaces:[...c.palaces].sort((a,b)=>a.branch-b.branch).map(p=>({branch:p.branch,stem:p.stem,name:p.name,
      stars:p.stars.map((s:any)=>[s.name,s.type,s.brightnessRaw??null,s.siHua??null]).sort((a:any,b:any)=>a[0].localeCompare(b[0])),
      ageRange:p.daXianAge??null})),
    decades:c.daXians.map((d:any)=>[d.startAge,d.endAge,d.palaceBranch,d.stemIndex])});
}
try{
  const input=JSON.parse(fs.readFileSync(0,'utf8'));const profile=input.profile,gender=input.birth.gender;
  if(!Array.isArray(input.candidates)||input.candidates.length>20000)throw Error('Candidate count out of range');
  setBrightnessSchool(profile.brightness);
  astro.config({mutagens:{庚:GENG_VARIANTS[profile.geng_year_sihua] as any}});
  const make=(birth:any)=>{const c=generateChart({...birth,gender},{leapMonth:profile.leap_month});applyStaticSchoolVariants(c,profile.static_school_variants??{},profile.brightness);return c;};
  const expected=signature(make(input.birth));const matches=[];
  for(const row of input.candidates){
    const [year,month,day,hour]=row;const actual=signature(make({year,month,day,hour}));
    if(actual===expected)matches.push(`${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}-${hour}-${gender}`);
  }
  process.stdout.write(JSON.stringify({verified_candidates:input.candidates.length,matches,signature_sha256:createHash('sha256').update(expected).digest('hex'),
    scope:'All native palace stems/names, major/minor star positions, raw brightness and natal transformations, Ming/Shen, five-elements class and decade geometry; same gender and selected profile. Not a claim of identical lives or private website scoring.'}));
}catch(e:any){process.stdout.write(JSON.stringify({error:e.message}));process.exitCode=1;}
