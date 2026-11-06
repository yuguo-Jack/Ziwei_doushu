"""Build canonical quotations, original texts, code rules and provenance indexes."""
import sys,json,re,sqlite3,hashlib,urllib.parse,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ziwei_kb.common import normalize,tokenize,write_json,sha,TOPICS

REV='a600484a49255039d0725f1ba9e11ca81a948f97'
BASE=f'https://github.com/Renhuai123/ziwei-doushu/blob/{REV}/'
DB=ROOT/'knowledge/knowledge.building.sqlite'

def qualifiers(text):
    clauses=re.split(r'(?<=[。；;\n])',text)
    return [s.strip() for s in clauses if re.search(r'若|倘|如果|假如|只有|必须|必須|除非|男命|女命|同宫|同宮|落陷|入庙|入廟|会照|會照|遇|逢|不宜|不可',s)][:20]

class Builder:
    def __init__(self):
        if DB.exists():DB.unlink()
        self.conn=sqlite3.connect(DB);self.conn.executescript((ROOT/'design/knowledge-schema.sql').read_text(encoding='utf-8'))
        self.counts=collections.Counter();self.seen=set();self.rows=[]
    def source(self,id,kind,url,revision,file,license,meta=None):
        file=Path(file);digest=hashlib.sha256(file.read_bytes()).hexdigest()
        self.conn.execute('INSERT OR IGNORE INTO sources VALUES (?,?,?,?,?,?,?,?)',(id,kind,url,revision,digest,str(file.relative_to(ROOT)),json.dumps(license,ensure_ascii=False),json.dumps(meta or {},ensure_ascii=False)))
    def add(self,id,source_id,title,text,url,kind,namespace='ziwei',locator=None,metadata=None,notes='',eligible=True,conditions=None):
        if id in self.seen:return
        self.seen.add(id);metadata=metadata or {};metadata.update({'source_url':url,'conditions_verbatim':conditions if conditions is not None else qualifiers(text),'conditions_status':'verbatim qualifiers retained; not automatically executable','source_kind':kind})
        verification={'text_preserved':True,'source_locatable':True,'independently_collated_edition':False,'semantic_rule_verified':False,'implementation_preserved':kind=='code_rule','project_contract':kind=='project_guide'}
        if '\ufffd' in text:
            verification['encoding_damage_detected']=True;notes+='；源文含替代字符，需核对原件，不能作为完整逐字引文。';eligible=False
        self.conn.execute('INSERT INTO source_units VALUES (?,?,?,?,?,?,?,?,?)',(id,source_id,json.dumps(locator or {},ensure_ascii=False),text,normalize(text),sha(text),namespace,notes,json.dumps(verification)))
        sid='S:'+id;is_rule=kind=='code_rule'
        self.conn.execute('INSERT INTO statements VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(sid,'conditional_rule' if is_rule else 'interpretation',title,text,metadata.get('topic','general'),namespace,metadata.get('school','source-specific'),'conditional' if is_rule else 'unknown',json.dumps({'verbatim':metadata['conditions_verbatim'],'logic_source':metadata.get('function'),'status':metadata['conditions_status']},ensure_ascii=False),json.dumps(metadata.get('exceptions',[]),ensure_ascii=False),'reviewed' if kind in ['code_rule','project_guide'] else 'candidate',json.dumps(verification)))
        self.conn.execute('INSERT INTO statement_sources VALUES (?,?,?)',(sid,id,'quote' if kind in ['course_quote','classic_transcription'] else 'supports'))
        # Quotes stay whole; long source paragraphs/code are chunked by intact lines/sentences.
        pieces=[];current=''
        if len(text)<=1100:pieces=[text]
        else:
            for bit in re.split(r'(?<=[。；\n])',text):
                if len(current)+len(bit)>1100 and current:pieces.append(current);current=''
                if len(bit)>1400:
                    if current:pieces.append(current);current=''
                    pieces.extend(bit[i:i+1000] for i in range(0,len(bit),1000))
                else:current+=bit
            if current:pieces.append(current)
        for idx,piece in enumerate(pieces):
            stable=id+f':{idx}'
            self.conn.execute('INSERT INTO chunks(stable_id,source_unit_id,statement_id,title,text,title_terms,body_terms,namespace,evidence_kind,eligible,content_sha256,metadata_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                (stable,id,sid,title,piece,tokenize(title),tokenize(piece),namespace,kind,int(eligible),sha(piece),json.dumps(metadata,ensure_ascii=False)))
            self.counts[kind]+=1
        self.rows.append({'id':id,'title':title,'text':text,'kind':kind,'namespace':namespace,'source_url':url,'conditions':metadata['conditions_verbatim'],'notes':notes,'eligible':eligible})
    def finish(self):
        self.conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES ('rebuild')");self.conn.commit()
        assert self.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not self.conn.execute('PRAGMA foreign_key_check').fetchall()
        stats={'sources':self.conn.execute('SELECT count(*) FROM sources').fetchone()[0],
            'source_units':len(self.seen),'chunks':sum(self.counts.values()),'by_kind':dict(self.counts),
            'eligible_chunks':self.conn.execute('SELECT count(*) FROM chunks WHERE eligible=1').fetchone()[0],
            'by_namespace':dict(self.conn.execute('SELECT namespace,count(*) FROM source_units GROUP BY namespace').fetchall()),
            'quote_rows_raw':4886,'quote_source_combinations_unique':4881,'review_policy':'raw source text is searchable; inferred statements remain candidates; native code rules keep source and conditions',
            'coverage_gaps':['紫微斗数全集的完整可核电子底本未取得；仓库节选已隔离','未恢复作者闭源断语库','传统古籍不同版本未逐字通校','v4 主要为固定版本本命解读，不代表任意运限/流派均有原文结果']}
        self.conn.close();DB.replace(ROOT/'knowledge/knowledge.sqlite')
        (ROOT/'exports/knowledge-records.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in self.rows),encoding='utf-8')
        write_json(ROOT/'manifests/knowledge.json',stats);return stats

def main():
    eng=json.loads((ROOT/'sources/supplementary/engine-knowledge.json').read_text(encoding='utf-8'))
    constants=eng['constants'];concepts=[]
    for name,data in constants['STAR_DESCRIPTIONS'].items():concepts.append({'id':'star:'+name,'kind':'star','name':name,'aliases':[],'description':data})
    for name in constants['PALACE_NAMES_ORDER']:
        aliases=[name.replace('宫','')]
        if name=='交友宫':aliases+=['仆役','仆役宫','朋友宫']
        if name=='官禄宫':aliases+=['事业宫']
        concepts.append({'id':'palace:'+name,'kind':'palace','name':name,'aliases':aliases})
    for name in ['化禄','化权','化科','化忌']:concepts.append({'id':'sihua:'+name,'kind':'sihua','name':name,'aliases':[]})
    for kind,key in [('branch','BRANCHES'),('stem','STEMS')]:
        for name in constants[key]:concepts.append({'id':kind+':'+name,'kind':kind,'name':name,'aliases':[]})
    for row in eng['rules']:
        for name in row['names']:concepts.append({'id':'pattern:'+name,'kind':'pattern','name':name,'aliases':[]})
    concepts.extend([{'id':'term:'+x,'kind':'term','name':x,'aliases':[]} for x in ['三方四正','对宫','三合','夹宫','排盘','命盘','真太阳时','均时差','夏令时','晚子时','闰月','大限','流年','流月','流日']])
    write_json(ROOT/'knowledge/concepts.json',concepts)
    b=Builder()
    for c in concepts:
        b.conn.execute('INSERT OR IGNORE INTO concepts VALUES (?,?,?,?)',(c['id'],c['kind'],c['name'],json.dumps(c.get('description',{}),ensure_ascii=False)))
        for alias in c['aliases']:b.conn.execute('INSERT OR IGNORE INTO concept_aliases VALUES (?,?,?)',(alias,c['id'],'synonym'))
    corpus=ROOT/'sources/tianji-462faa4/data/entries.jsonl'
    b.source('tianji-462faa4','course_quotes','https://github.com/Renhuai123/nihai-tianji-corpus','462faa4c70af40b8b87ad82ffa82a5823a485e94',corpus,{'declared':'CC-BY-NC-SA-4.0','rights_holder':'original course rights reserved by holder'})
    local=[json.loads(x) for x in (ROOT/'repo/docs/tianji-ziwei/entries.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    key=lambda r:(r['bvid'],r['part'],r['t_hms'],r['quote'])
    ziwei={key(x) for x in local};seen={};duplicates=[]
    booknames={'01-stars':'主星','02-palaces':'十二宫','03-patterns':'格局','04-sihua':'四化','05-illness':'疾厄','07-methodology':'方法论','08-yili':'易理','09-hexagrams':'六十四卦','10-divination':'占断','11-fengshui':'堪舆','12-tieban':'铁板神数'}
    for i,line in enumerate(corpus.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip():continue
        row=json.loads(line);k=key(row)
        if k in seen:duplicates.append({'duplicate_line':i,'canonical_unit':seen[k],'note':row.get('note','')});continue
        id=f'TJ-462faa4-{i:04d}';seen[k]=id;h,m,s=map(int,row['t_hms'].split(':'));seconds=h*3600+m*60+s
        ns='ziwei' if k in ziwei else {'08-yili':'yijing','09-hexagrams':'yijing','11-fengshui':'fengshui','12-tieban':'tieban'}.get(row['book'],'tianji')
        title='倪海厦《天纪》 / '+booknames[row['book']]+' / '+row['h2']+(' / '+row['h3'] if row['h3'] else '')
        url=f"https://www.bilibili.com/video/{row['bvid']}?p={row['part']}&t={seconds}"
        b.add(id,'tianji-462faa4',title,row['quote'],url,'course_quote',ns,{'line':i,'bvid':row['bvid'],'part':row['part'],'seconds':seconds,'section':row['section']},
            {'book':row['book'],'school':'Ni Haixia course','quote_status':'source transcription; retained editorial corrections; not individually re-listened'},row.get('note',''))
    write_json(ROOT/'manifests/tianji-duplicates.json',duplicates)
    for p in sorted((ROOT/'sources/classics').glob('wikisource-*.json')):
        row=json.loads(p.read_text(encoding='utf-8'));id=row['id'];b.source(id,'classic_transcription',row['canonical_url'],row['revision'],p,{'declared':row['license']},{'edition_note':row['edition_note'],'complete_page_range':True})
        for para in row['paragraphs']:
            url=row['permanent_url']+('#'+urllib.parse.quote(para['anchor']) if para['anchor'] else '')
            b.add(f"WS-{row['revision']}-{para['ordinal']:04d}",id,row['title']+' / '+para['heading'],para['text'],url,'classic_transcription',row['namespace'],{'paragraph':para['ordinal'],'heading':para['heading'],'anchor':para['anchor']},{'school':'historical text; edition-specific','edition_note':row['edition_note']})
    # Native rules retain the entire actual implementation, rather than inferred predicates.
    rulesfile=ROOT/'repo/lib/ziwei/patterns.ts';b.source('engine-patterns','source_code',BASE+'lib/ziwei/patterns.ts',REV,rulesfile,{'declared':'MIT'})
    for row in eng['rules']:
        id='CODE-'+row['function'];url=BASE+row['source_path']+'#L'+str(row['line'])
        title='代码格局规则 / '+('、'.join(row['names']) or row['function'])
        b.add(id,'engine-patterns',title,row['source_code'],url,'code_rule',locator={'file':row['source_path'],'line':row['line']},metadata={'function':row['function'],'school':'pinned public engine; Ni-oriented rules','conditions_source':'actual TypeScript predicates; text labels may branch'})
        b.conn.execute('INSERT INTO executable_rule_adapters VALUES (?,?,?,?,?,?)',(row['function'],'tools/chart_engine.ts#detectPatterns',REV,id,json.dumps({'implementation':row['function']}),'tested'))
    f=ROOT/'repo/lib/ziwei/constants.ts';b.source('engine-constants','source_code',BASE+'lib/ziwei/constants.ts',REV,f,{'declared':'MIT'})
    for name,data in constants['STAR_DESCRIPTIONS'].items():
        text=f"{name}：项目术语表关键词为{data['keywords']}；性质标注{data['nature']}；五行{data['element']}。此为工程的传统命理术语定义。"
        b.add('TERM-'+name,'engine-constants','主星术语 / '+name,text,BASE+'lib/ziwei/constants.ts','code_table',metadata={'school':'project terminology'})
    for gan,names in constants['SI_HUA_TABLE'].items():
        stem=constants['STEMS'][int(gan)];text=f"本工程十干四化表：{stem}干，{names[0]}化禄、{names[1]}化权、{names[2]}化科、{names[3]}化忌。星曜四化保存在 Star.siHua 字段，不是名为化禄等的独立星曜。"
        b.add('SIHUA-'+stem,'engine-constants','四化表 / '+stem+'年干',text,BASE+'lib/ziwei/constants.ts#L47','code_table',metadata={'school':'project sihua table','stem':stem})
    hemi=ROOT/'repo/lib/ziwei/heming-knowledge.ts';b.source('engine-heming','compiled_secondary',BASE+'lib/ziwei/heming-knowledge.ts',REV,hemi,{'declared':'MIT code; quoted course wording retains separate rights'})
    for group,value in eng['heming'].items():
        values=value.items() if isinstance(value,dict) else [('method',value)]
        for key,value in values:
            text='\n'.join(f'{k}：{v}' for k,v in value.items()) if isinstance(value,dict) else str(value)
            b.add('HEMING-'+group+'-'+key,'engine-heming','合盘方法 / '+key,text,BASE+'lib/ziwei/heming-knowledge.ts','compiled_secondary',metadata={'topic':'love','school':'repository compiled method','attribution_status':'ni_quote fields do not independently establish exact course wording'})
    # Retain the existing curated excerpts with their conflict flag; never cite as checked originals.
    for book in eng['curated_classics']:
        p=ROOT/('repo/lib/classics/data/'+{'gusuifu':'gusuifu','quanji':'quanji','quanshu':'quanshu'}[book['slug']]+'.ts');sid='curated-'+book['slug']
        b.source(sid,'unverified_curated_excerpt',BASE+str(p.relative_to(ROOT/'repo')).replace('\\','/'),REV,p,{'declared':'upstream labels ancient originals public domain; editorial provenance unverified'})
        for ch in book['chapters']:
            for para in ch['paragraphs']:
                b.add('QUARANTINE-'+para['id'],sid,book['title']+' / '+ch['title'],para['text'],BASE+str(p.relative_to(ROOT/'repo')).replace('\\','/'),'quarantined_excerpt',eligible=False,notes='不是已核古籍原文；现代整理与原始引文混杂。')
    guidefile=ROOT/'tools/chart_engine.ts';b.source('project-guide','adapter_code','local:tools/chart_engine.ts','1.0',guidefile,{'declared':'local implementation'})
    guides={
      'paipan':('什么是排盘','排盘是按传统命理规则，将出生日期、时辰和选定流派转换成十二宫及星曜结构。本工具由固定版本 iztro 适配引擎计算，模型负责解释检索到的资料。'),
      'twelve':('十二宫与十三主题','命盘有十二宫：'+ '、'.join(constants['PALACE_NAMES_ORDER'])+'。数据集有十三个分析主题，因为命格总览和性格等主题可对应同一命宫，不存在第十三个物理宫。'),
      'sanfang':('三方四正是什么','本工程三方四正取本宫、相隔四支和八支的两个三合宫、相隔六支的对宫。以命宫为中心时，对应命宫、财帛宫、官禄宫和迁移宫；解读具体宫位须按该宫重新计算关系。'),
      'time':('出生时间与真太阳时','本工具支持经度差及均时差的真太阳时换算。hour 是时辰序号0–11，不是钟表小时。钟表时间需明确标准时区及夏令时是否已换算。晚子时默认按校正后的时间换日；未知时辰不能默认为已知子时。'),
      'versions':('当前排盘和v4数据的区别','v4.0-13d 是2026-10-15的本命解读快照，覆盖公历1950–2026，时辰序号0–11和男女。旧默认亮度XD2，与当前默认QS不同。当前排盘与原始案例分别返回，生日键相同不证明全部口径相同；流月流日原文未包含在该数据中。'),
      'invalid-sihua':('紫微化忌的资料冲突','工程整理节选出现“紫微化忌”，但本工程十干四化表中紫微只有化权和化科，没有化忌。该节选已隔离为存疑材料。检索到一个词组不证明对应规则成立。'),
      'leap':('闰月四种口径','引擎支持split（月中分界）、next-month（归下月）、prev-month（归前月）、origin-month（归本月闰月标识）。当前默认split。不同策略必须显式记录，不可将一种策略生成的案例直接视为其它策略相同。'),
      'age':('虚岁与参考日期','本工具显式返回as_of参考日期。当前年龄采用农历年差加一的虚岁口径，不是周岁；公历1月出生者可能仍属上一农历年。例如1990年1月1日属于己巳农历1989年，至2026年农历年虚岁为38。大限按相同虚岁口径定位。'),
      'borrow':('空宫借对宫与实际同宫的区别','本宫没有十四主星时，工程保存isEmpty、borrowedFromName和borrowedStars供借对宫分析。星曜的实际位置仍在对宫，不能把借星称为本宫实坐或双星实际同宫。原文涉及入庙、煞曜、同宫等条件时，应核对实际星位和所用借星规则，不自动视作全部满足。'),
    }
    for key,(title,text) in guides.items():b.add('GUIDE-'+key,'project-guide',title,text,'local:tools/chart_engine.ts','project_guide',metadata={'school':'local tool contract','basis':'pinned engine code, constants, README and adapter behavior'})
    featurefile=ROOT/'tools/feature_engine.ts';b.source('feature-guide','adapter_code','local:tools/feature_engine.ts','1.1',featurefile,{'declared':'local implementation'})
    additions={
      'period':('小限、太岁与运限解读边界','本工具可计算本命、大限、小限/太岁流年、太岁体系流月流日流时。小限与太岁分别返回；流月日时不冒套为未核的网站小限子层。目标公历日期与目标农历流年明确区分。本命v4原文不作为流年原文。'),
      'school-variants':('公开魁钺四表与截空三表','kuiyue_school选择qs1、qs2、zhong-yiming、network，对应固定仓库KY_ARR1至4；jiekong_school选择double、single、zhanyan，对应JK_ARR2、1、3。子起一表编码转0至11地支，换宫后按所选亮度表重算。旬空、副旬保持原生基准，未重建缺失school-patches模块。其它天马、天空、天使天伤和长生切换缺乏完整可核实现，不能静默生效。'),
      'flights':('宫干四化、自化与来因','本工具按选定四化表列出各宫天干所化星曜实际落宫、本宫自化与对宫关系；几何联系不自动构成事件判断。庚年四化可选择五种表，必须保留表名。'),
      'twins':('同盘结构匹配的范围','全库索引覆盖674976种男女配置，先比较所选性别337488个日期时辰的命身宫地支和十四主星位置16个分量。再用tools/verify_twins.ts对全部16分量相同的候选逐盘调用原生引擎，核对宫干、全部主辅杂星、亮度、四化、命身、五行局和大限结构，分别返回主星相同与完整原生盘面相同的数量。索引采用split闰月，不是实际真人档案或人口估计，同盘不表示人生经历相同。'),
      'liuren':('小六壬如何顺数','小六壬六宫顺序大安、留连、速喜、赤口、小吉、空亡。月从大安含起点数，日从月落点含起点数，时从日落点含起点数；子时计1，亥时计12。闰月取本月数，23时不更换民用农历日。这是文化算法，不是事件必然性的证据。'),
    }
    for key,(title,text) in additions.items():b.add('GUIDE-'+key,'feature-guide',title,text,'local:tools/feature_engine.ts','project_guide',metadata={'school':'explicit local tool contract'})
    from import_renji import add_renji
    add_renji(b,ROOT)
    stats=b.finish();write_json(ROOT/'manifests/conflicts.json',[{'id':'purple-ji','query':'紫微化忌','evidence_ids':['GUIDE-invalid-sihua','QUARANTINE-gsf-2-4'],'resolution':'do not promote the curated claim; use explicit sihua table and preserve disputed source'},{'id':'brightness-v4','evidence_ids':['GUIDE-versions'],'resolution':'current and archived profiles remain distinct'}]);print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
