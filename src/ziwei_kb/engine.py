import json,subprocess,re
from .common import ROOT,TOPICS,normalize,read_json
from .retrieval import search,source_record
from .cases import lookup

def run_engine(payload):
    command=['node','--import','./node_modules/tsx/dist/loader.mjs','../tools/chart_engine.ts']
    result=subprocess.run(command,input=json.dumps(payload,ensure_ascii=False),encoding='utf-8',text=True,capture_output=True,cwd=ROOT/'repo',timeout=45)
    try:data=json.loads(result.stdout)
    except Exception:raise RuntimeError('排盘适配器没有返回有效JSON：'+result.stderr[-1500:])
    if result.returncode or 'error' in data:raise ValueError(data.get('error',result.stderr[-1000:]))
    return data

def chart(payload,operation='chart'):
    if not isinstance(payload,dict):raise ValueError('输入应为JSON对象。')
    if '_operation' in payload:raise ValueError('_operation为内部字段，请使用对应命令。')
    original=dict(payload);working=dict(payload);conversion=None
    if working.get('calendar')=='lunar':
        conversion=run_engine({'_operation':'calendar',**{k:working[k] for k in ['year','month','day','calendar','is_leap_month'] if k in working}})
        working.update(conversion['solar']);working['calendar']='solar';working.pop('is_leap_month',None)
    from .geography import resolve_clock
    working,time_resolution=resolve_clock(working)
    data=run_engine({**working,'_operation':operation});data['input']=original
    if conversion:data['calendar_conversion']=conversion
    if time_resolution:data['calculation_profile']['timezone_resolution']=time_resolution
    if data['calculation_profile'].get('geng_year_sihua')!='GYWYT':data['case_compatibility']['differences'].append('Selected Geng-year transformation variant is not assumed compatible with the legacy archive.')
    return data

def calendar(payload):return run_engine({**payload,'_operation':'calendar'})
def liuren(payload):return run_engine({**payload,'_operation':'liuren'})

def time_candidates(payload):
    rows=[]
    for hour in range(12):
        data={k:v for k,v in payload.items() if k not in ['clock_hour','clock_minute','hour','timezone','fold','unknown_time','period','utc_offset_minutes','dst_adjust_minutes']}
        data['hour']=hour;c=chart(data);ming=next(p for p in c['chart']['palaces'] if p.get('isMingGong'))
        rows.append({'hour':hour,'branch':'子丑寅卯辰巳午未申酉戌亥'[hour],'birth_key':c['birth_key'],'ming_palace_branch':c['chart']['mingGongBranch'],'shen_palace_branch':c['chart']['shenGongBranch'],
            'ming_main_stars':[s['name'] for s in ming['stars'] if s['type']=='major'],'borrowed_stars':ming.get('borrowedStars',[]),'patterns':[p['name'] for p in c['patterns']]})
    return {'candidates':rows,'selected_as_true':None,'scope':'Twelve branch hypotheses on the explicitly supplied chart date; no clock/longitude cross-date resolution because the time is unknown. Do not choose one as true without evidence.'}

def merge_evidence(primary,additional,key='chunk_id'):
    ids={h[key] for h in primary['hits']}
    primary['hits'] += [h for h in additional['hits'] if h[key] not in ids]
    reason=additional.get('degraded_to_lexical')
    if reason:
        reasons=[r for r in [primary.get('degraded_to_lexical'),reason] if r]
        primary['degraded_to_lexical']='; '.join(dict.fromkeys(reasons))

def period_context(payload,question,topic='overview',limit=8):
    if type(limit) is not int or not 1<=limit<=20:raise ValueError('证据条数limit范围1–20。')
    calculated=chart(payload,'period');period=calculated['period'];target_name={'overview':'命','personality':'命','career':'官禄','wealth':'财帛','love':'夫妻','health':'疾厄','family':'兄弟','children':'子女','move':'迁移','friends':'仆役','home':'田宅','spirit':'福德','parents':'父母'}[topic]
    facts=next((p for p in period['selected']['palaces'] if p['period_palace'].replace('宫','')==target_name),None)
    stars=' '.join(s['name'] for s in facts['physical_main_stars']) if facts else ''
    evidence=search(f'{question} {period["selected"]["name"]} {target_name} {stars}',limit=16,namespace='ziwei')
    focused=search(f'{stars} {target_name}宫 适用条件',limit=8,namespace='ziwei') if stars else {'hits':[]}
    merge_evidence(evidence,focused,'evidence_id')
    filtered=[];rejected=[];branches='子丑寅卯辰巳午未申酉戌亥';target_year_branch=branches[(period['target_lunar_year']-4)%12]
    anchor=period['selected']['anchor_branch'];anchor_branch=branches[anchor] if anchor is not None else None
    for hit in evidence['hits']:
        reason=None;text=normalize(hit['text']);title=normalize(hit['title'])
        if hit['kind']=='code_rule':reason='natal detector is not a verified period rule'
        elif re.search(r'六壬|六爻|占断',title):reason='different divination method, not Ziwei period evidence'
        elif '安身命例' in title and not re.search(r'举例|案例|原例',question):reason='specific historical worked example, not current conditions'
        else:
            match=re.search(r'([子丑寅卯辰巳午未申酉戌亥])年太岁并小限到([子丑寅卯辰巳午未申酉戌亥])宫',text)
            if match and (period['view'] not in ['yearly','age'] or period['annual_method']!='xiaoxian' or match.group(1)!=target_year_branch or match.group(2)!=anchor_branch):
                reason='explicit yearly-branch/small-limit-palace predicate does not match selected layer'
        if reason:rejected.append({'evidence_id':hit['evidence_id'],'reason':reason});continue
        hit['applicability']='reference passage; all star placement, brightness, layer and other clauses still require condition matching'
        filtered.append(hit)
    guide=source_record('GUIDE-period',4000)
    mandatory={'evidence_id':'GUIDE-period','chunk_id':'GUIDE-period:exact','title':guide['title'],'text':guide['text'],'kind':'project_guide','source_url':guide['canonical_url'],'revision':guide['revision'],'conditions_status':guide['conditions_status'],'notes':guide['notes'],'applicability':'calculation-method boundary for this tool'}
    evidence['hits']=[mandatory]+[h for h in filtered if h['evidence_id']!='GUIDE-period'][:limit-1]
    evidence['rejected_nonapplicable_passages']=rejected
    compact={k:calculated[k] for k in ['birth_key','engine_revision','normalized_birth','calculation_profile','patterns','notices','case_compatibility']}
    compact.update(current_age=calculated['chart']['currentAge'],da_xians=calculated['chart']['daXians'])
    # Selected layer keeps all its palace facts. Other layers expose anchors/tables without
    # duplicating 7 x 12 palaces and the full chart inside every conversational turn.
    selected_period={**period,'layers':{k:{a:b for a,b in v.items() if a!='palaces'} for k,v in period['layers'].items()}}
    remaining=11000
    for hit in evidence['hits']:
        full=len(hit['text']);hit['text']=hit['text'][:remaining];hit['text_truncated_by_budget']=len(hit['text'])<full
        remaining=max(0,remaining-len(hit['text']))
    evidence['hits']=[h for h in evidence['hits'] if h['text']];evidence['text_budget_chars']=11000
    return {'question':question,'topic':topic,'calculation':compact,'period':selected_period,'topic_facts':facts,'evidence':evidence,
        'archived_period_reading':None,'answer_contract':['No natal archive is returned as a period-specific reading.','Retain annual method and date boundaries.','Retrieved quotations still need period and actual-star condition matching.','Full layer palace mappings are available through the period command.']}

def context(payload,question,topic='overview',limit=8):
    if type(limit) is not int or not 1<=limit<=20:raise ValueError('证据条数limit范围1–20。')
    if payload.get('period'):return period_context(payload,question,topic,limit)
    calculated=chart(payload);archive=lookup(calculated['birth_key'],topic,max_chars=5000)
    palace_name={'overview':'命','personality':'命','career':'官禄','wealth':'财帛','love':'夫妻','health':'疾厄','family':'兄弟','children':'子女','move':'迁移','friends':'仆役','home':'田宅','spirit':'福德','parents':'父母'}[topic]
    palaces=calculated['chart']['palaces'];target=next((p for p in palaces if p['name'].replace('宫','')==palace_name),None)
    actual_stars=[s['name'] for s in target['stars'] if s['type']=='major'] if target else []
    borrowed=target.get('borrowedStars',[]) if target else []
    stars=' '.join(actual_stars or borrowed)
    evidence=search(f'{question} {TOPICS[topic]} {palace_name}宫 {stars}',limit=20,namespace='ziwei')
    if stars:
        focused=search(f'{stars} {palace_name} 入庙 适用条件',limit=8,namespace='ziwei')
        merge_evidence(evidence,focused)
    if target and target.get('isEmpty'):
        additional=search(f'空宫 借对宫 三方四正 {palace_name}宫',limit=10,namespace='ziwei')
        merge_evidence(evidence,additional)
    active={p['name'] for p in calculated['patterns']};definitions={r['function']:r['names'] for r in read_json(ROOT/'sources/supplementary/engine-knowledge.json')['rules']}
    def rule_active(function,names):
        if active.intersection(names):return True
        if function=='detectHuaLuRuMing':return any(n.endswith('化禄入命') for n in active)
        if function=='detectHuaJiRuMingQian':return any('化忌入命' in n or '化忌入迁' in n for n in active)
        return False
    filtered=[];rejected=[]
    for hit in evidence['hits']:
        if hit['kind']=='course_quote' and re.search(r'(?:她|他|这个人|那个人).{0,8}\d{1,3}岁|来找你|这个案例|这张盘|这个女的|这个男的',hit['text']) and not re.search(r'案例|盘例|举例',question):
            rejected.append({'evidence_id':hit['evidence_id'],'reason':'other-person illustrative passage; not applied to the current birth chart'});continue
        if hit['kind']=='code_rule':
            function=hit['evidence_id'].removeprefix('CODE-');names=definitions.get(function,[])
            hit['applicability']='detected_in_this_chart' if rule_active(function,names) else 'not_detected_or_dynamic_name_unresolved'
            if not rule_active(function,names):rejected.append({'evidence_id':hit['evidence_id'],'reason':hit['applicability']});continue
        else:hit['applicability']='source passage; individual clauses require condition matching'
        title=normalize(hit['title']);priority=hit['score']
        if palace_name in title:priority*=2
        if target and target.get('isEmpty') and ('借星' in title or '空宫' in title):priority*=1.5
        if any(t in title for t in ['案例','实例','盘例','命例']):hit['applicability']='illustrative example, not the current person';priority*=.7
        filtered.append((priority,hit))
    # Source diversity: several anecdotes under one course heading are not independent support.
    filtered.sort(key=lambda x:x[0],reverse=True);chosen=[];title_counts={}
    for _,hit in filtered:
        if title_counts.get(hit['title'],0)>=2:continue
        chosen.append(hit);title_counts[hit['title']]=title_counts.get(hit['title'],0)+1
    mandatory=[]
    def exact_evidence(id,applicability):
        row=source_record(id,4000)
        return {'evidence_id':id,'chunk_id':id+':exact','title':row.get('title',id),'text':row['text'],'kind':row['artifact_kind'],
            'source_url':row['canonical_url']+('#L'+str(row['locator']['line']) if row['locator'].get('line') else ''),
            'revision':row['revision'],'locator':row['locator'],'license':row['license'],'notes':row['notes'],
            'verification':row['verification'],'applicability':applicability,'conditions_status':'actual implementation/source text; retain complete predicate context'}
    for function,names in definitions.items():
        if rule_active(function,names):mandatory.append(exact_evidence('CODE-'+function,'detected_in_this_chart'))
    if target and target.get('isEmpty'):
        mandatory.insert(0,exact_evidence('GUIDE-borrow','current palace has no main stars; borrowing is distinct from physical placement'))
    # Ensure a focused original-text passage can be read alongside, without treating it as unconditional.
    classics=[h for h in chosen if h['kind']=='classic_transcription' and palace_name in normalize(h['title'])]
    if classics:mandatory.append(classics[0])
    final=[];used=set()
    for h in mandatory+chosen:
        if h['evidence_id'] in used:continue
        used.add(h['evidence_id']);final.append(h)
        if len(final)>=limit:break
    remaining=11000
    for hit in final:
        full=len(hit['text']);hit['text']=hit['text'][:remaining];hit['text_truncated_by_budget']=len(hit['text'])<full
        remaining=max(0,remaining-len(hit['text']))
    evidence['hits']=[h for h in final if h['text']];evidence['rejected_code_rules']=rejected
    evidence['text_budget_chars']=11000
    san_branches=[(target['branch']+delta)%12 for delta in [0,4,8,6]] if target else []
    sha_names={'擎羊','陀罗','火星','铃星','地空','地劫'}
    geometry={'palace':target['name'] if target else None,'is_empty':target.get('isEmpty',False) if target else None,
        'borrowed_from':target.get('borrowedFromName') if target else None,'borrowed_stars':borrowed,
        'physical_main_stars':actual_stars,'san_fang_branches':san_branches,
        'sha_definition':'six standard sha names only: 擎羊、陀罗、火星、铃星、地空、地劫; other type=sha labels are separate',
        'sha_stars_in_current_san_fang':[{'palace':p['name'],'star':s['name']} for p in palaces if p['branch'] in san_branches for s in p['stars'] if s['name'] in sha_names],
        'other_sha_typed_in_current_san_fang':[{'palace':p['name'],'star':s['name']} for p in palaces if p['branch'] in san_branches for s in p['stars'] if s['type']=='sha' and s['name'] not in sha_names]}
    consistency=[]
    archived_text=' '.join(t['text'] for t in archive.get('topics',{}).values())
    if target and target.get('isEmpty') and any(w in archived_text for w in ['双星同宫','雙星同宮','本宫形成']):
        consistency.append('存档同时使用借星与本宫双星同宫措辞；当前本宫无主星，借入解读不代表实际星位移动。')
    compact={'birth_key':calculated['birth_key'],'engine_revision':calculated['engine_revision'],'normalized_birth':calculated['normalized_birth'],
        'calculation_profile':calculated['calculation_profile'],'patterns':calculated['patterns'],'notices':calculated['notices'],
        'palaces':[{'name':p['name'],'branch':p['branch'],'stars':[s for s in p['stars'] if s['type']=='major' or s.get('siHua') or s['type']=='sha'],
            'is_empty':p.get('isEmpty',False),'borrowed_from':p.get('borrowedFromName'),'borrowed_stars':p.get('borrowedStars',[])} for p in palaces],
        'current_age':calculated['chart']['currentAge'],'da_xians':calculated['chart']['daXians'],'case_compatibility':calculated['case_compatibility']}
    return {'question':question,'topic':topic,'calculation':compact,'topic_geometry':geometry,'archived_case':archive,'archive_consistency_notes':consistency,'evidence':evidence,
        'answer_contract':['Keep calculated facts, archived v4 text and current synthesis distinct.','State applicability and known profile differences.','Use source IDs and citations for substantive source-dependent claims.','If no support, state the source gap; do not use neighboring birth dates.']}

def compare(first,second,question,relation='love'):
    a=chart(first);b=chart(second)
    focuses={'love':['命','夫妻','福德','迁移'],'business':['命','官禄','兄弟','财帛','福德'],'hierarchy':['命','官禄','仆役','福德'],'friendship':['命','兄弟','仆役','福德']}
    if relation not in focuses:raise ValueError('关系类型不支持。')
    def summary(c):return {'birth_key':c['birth_key'],'normalized_birth':c['normalized_birth'],'calculation_profile':c['calculation_profile'],
        'palaces':[{'name':p['name'],'branch':p['branch'],'stars':[s for s in p['stars'] if s['type']=='major' or s.get('siHua')],
            'is_empty':p.get('isEmpty',False),'borrowed_stars':p.get('borrowedStars',[]),'borrowed_from':p.get('borrowedFromName')} for p in c['chart']['palaces']],
        'patterns':c['patterns'],'current_age':c['chart']['currentAge'],'current_da_xian':next((d for d in c['chart']['daXians'] if d['startAge']<=c['chart']['currentAge']<=d['endAge']),None)}
    evidence=search(question+' 合盘 '+' '.join(focuses[relation])+' 三方四正',limit=12)
    focused=[]
    for name in focuses[relation]:
        pair={'palace':name}
        for key,c in [('first',a),('second',b)]:
            p=next(p for p in c['chart']['palaces'] if p['name'].replace('宫','')==name)
            pair[key]={'branch':p['branch'],'physical_main_stars':[s for s in p['stars'] if s['type']=='major'],'is_empty':p.get('isEmpty',False),'borrowed_stars':p.get('borrowedStars',[]),'borrowed_from':p.get('borrowedFromName')}
        focused.append(pair)
    return {'question':question,'relation':relation,'focus_palaces':focuses[relation],'first':summary(a),'second':summary(b),'comparison':focused,'evidence':evidence,
        'score':None,'score_status':'No complete disclosed scoring function; no fabricated ten-grid/compatibility score.',
        'interpretation_status':'Evidence packet for comparative study; no reconstructed proprietary score or guarantee of website-identical judgments.'}
