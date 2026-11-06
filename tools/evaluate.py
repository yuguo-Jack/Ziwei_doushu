"""Frozen source-retrieval questions plus behavioral tool/invariant checks."""
import sys,json,hashlib,time,statistics,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ziwei_kb.common import connect,normalize,write_json,read_json
from ziwei_kb.retrieval import search,source_record
from ziwei_kb.cases import lookup
from ziwei_kb.engine import chart,context

def prepare():
    path=ROOT/'evaluations/questions.json'
    if path.exists():return read_json(path)
    items=[]
    guides=[('三方四正究竟由哪几个宫位组成？','sanfang'),('为什么命盘只有十二宫，解读却有十三个主题？','twelve'),('排盘具体在计算什么，谁负责解释？','paipan'),('把钟表时间转成真太阳时，需要考虑哪些修正？','time'),('晚子时为什么会影响排盘日期，时辰序号是什么？','time'),('闰月有哪些归属方法，目前默认用哪一种？','leap'),('现有排盘和v4存档是不是同一套亮度规则？','versions'),('资料里出现紫微化忌，但四化表没有，如何处理？','invalid-sihua'),('空宫借对面的星，等不等于那些星实际坐在本宫？','borrow')]
    for q,id in guides:items.append({'query':q,'gold':['GUIDE-'+id],'type':'retrieval','split':'development'})
    with connect() as c:
        for star in ['紫微','天机','太阳','武曲','天同','廉贞','天府','太阴','贪狼','巨门','天相','天梁','七杀','破军']:
            gold=[r[0] for r in c.execute('SELECT DISTINCT source_unit_id FROM chunks WHERE eligible=1 AND (title LIKE ? OR source_unit_id=?)',('%主星 / '+star+'%','TERM-'+star))]
            items.append({'query':f'{star}星的性质和传统关键词是什么？','gold':gold,'type':'retrieval','split':'development'})
        for palace in ['命宫','兄弟宫','夫妻宫','子女宫','财帛宫','疾厄宫','迁移宫','仆役（交友）宫','官禄宫','田宅宫','福德宫','父母宫']:
            gold=[r[0] for r in c.execute("SELECT DISTINCT source_unit_id FROM chunks WHERE evidence_kind='course_quote' AND title LIKE ?",('% / 十二宫 / '+palace+'%',))]
            if not gold:
                gold=[r[0] for r in c.execute("SELECT DISTINCT source_unit_id FROM chunks WHERE evidence_kind='course_quote' AND text LIKE ?",('%'+palace+'%',))]
            assert gold,palace
            q=palace.replace('仆役（交友）','交友')
            items.append({'query':f'倪海厦《天纪》怎样讲{q}？请找可回放的课程依据。','gold':gold,'type':'retrieval','split':'development'})
        for name,function in [('紫府同宫','detectZiFu'),('府相朝垣','detectFuXiangChaoYuan'),('火贪格或铃贪格','detectHuoTanLingTan'),('双禄朝垣','detectShuangLuChaoYuan'),('化权入官','detectHuaQuanRuGuan'),('羊陀夹忌','detectYangTuoJiaJi'),('马头带箭','detectMaTouDaiJian'),('机月同梁','detectJiYueTongLiang')]:
            items.append({'query':f'程序如何判断{name}，成立和破格条件是什么？','gold':['CODE-'+function],'type':'retrieval','split':'held_out'})
        for stem in ['甲','乙','庚','癸']:items.append({'query':f'{stem}年干的化禄、化权、化科、化忌分别对应哪些星？','gold':['SIHUA-'+stem],'type':'retrieval','split':'held_out'})
        rows=[dict(r) for r in c.execute('SELECT u.id,u.raw_text,c.title FROM source_units u JOIN chunks c ON c.source_unit_id=u.id WHERE c.evidence_kind=\'course_quote\' AND c.namespace=\'ziwei\'')]
        special=[('倪师怎样比较太阳入庙和落陷的差别？',lambda r:'主星 / 太阳' in r['title'] and '入庙落陷' in r['title']),('倪师说斗数判断六亲有什么局限？',lambda r:'六亲' in normalize(r['raw_text']) and '差' in normalize(r['raw_text'])),('倪师说文字像船、真理像彼岸，是怎样的学习观？',lambda r:'神 vs 形' in r['title'])]
        for q,predicate in special:
            gold=sorted({r['id'] for r in rows if predicate(r)});assert gold,q
            items.append({'query':q,'gold':gold,'type':'retrieval','split':'held_out'})
    assert len(items)==50
    tools=[('case_all','完整13主题和哈希'),('leap_case','闰日案例精确查询'),('outside','1940范围外不替代'),('invalid_date','无效日期拒绝'),('clock','钟表8点不当时辰8'),('solar_boundary','均时差跨时辰'),('unknown_time','未知时辰拒绝确定盘'),('profile','当前与v4配置差异保留'),('context_conditions','空宫与规则命中条件核对'),('source_roundtrip','原文及出处回查')]
    for i,(test,label) in enumerate(tools):items.append({'type':'tool','test':test,'query':label,'split':'development' if i<5 else 'held_out'})
    for i,row in enumerate(items):row['id']=f'Q{i+1:02d}'
    write_json(path,items);return items

def tool_check(test):
    if test=='case_all':
        r=lookup('1990-01-01-0-male','all',100000);assert len(r['topics'])==13 and all(t['hash_verified'] for t in r['topics'].values());return '13 topics and exact SHA verified'
    if test=='leap_case':assert lookup('2000-02-29-11-female','career')['found'];return 'real leap date found'
    if test=='outside':assert not lookup('1940-01-01-0-male')['found'];return 'outside coverage; no nearest substitution'
    if test=='invalid_date':
        try:lookup('1990-02-30-0-male')
        except ValueError:return 'invalid date rejected'
        raise AssertionError('invalid date accepted')
    if test=='clock':
        r=chart(read_json(ROOT/'evaluations/birth-example.json'));assert r['normalized_birth']['hour']==4;assert r['calculation_profile']['as_of'];return 'clock08:30 remains branch4 with source longitude'
    if test=='solar_boundary':
        r=chart({'year':2026,'month':11,'day':3,'clock_hour':12,'clock_minute':55,'longitude':120,'gender':'male'});assert r['normalized_birth']['hour']==7;return 'equation of time crosses noon branch'
    if test=='unknown_time':
        try:chart({'year':1990,'month':1,'day':1,'gender':'male','unknown_time':True})
        except ValueError:return 'unknown time explicitly rejected'
        raise AssertionError('unknown time silently accepted')
    if test=='profile':
        r=chart({'year':1990,'month':1,'day':1,'hour':0,'gender':'male'});assert r['case_compatibility']['status']=='partial';assert lookup(r['birth_key'])['profile']['leap_month_policy']=='unknown';return 'known and unknown policy differences retained'
    if test=='context_conditions':
        r=context(read_json(ROOT/'evaluations/birth-example.json'),'解释事业及依据','career');assert r['topic_geometry']['is_empty'];assert r['topic_geometry']['physical_main_stars']==[];assert r['topic_geometry']['borrowed_stars'];assert all(h['evidence_id']!='CODE-detectHuaQuanRuGuan' for h in r['evidence']['hits']);assert r['archive_consistency_notes'];return 'physical placement and borrowed stars distinct; inactive code rule excluded'
    if test=='source_roundtrip':
        r=source_record('TJ-462faa4-0396');assert r['locator']['seconds']==1347 and r['revision'].startswith('462faa4') and r['notes'];return 'quote, timestamp, revision and editorial note preserved'
    raise AssertionError(test)

def main():
    questions=prepare();frozen=hashlib.sha256((ROOT/'evaluations/questions.json').read_bytes()).hexdigest()
    search('知识库检索预热',limit=1)
    results=[];times=[];citation_errors=[]
    for q in questions:
        try:
            if q['type']=='retrieval':
                r=search(q['query'],limit=10);ids=[h['evidence_id'] for h in r['hits']];passed=bool(set(ids).intersection(q['gold']));times.append(r['seconds'])
                assert r['degraded_to_lexical'] is None,'semantic retrieval degraded'
                for hit in r['hits']:
                    original=source_record(hit['evidence_id'],100000)
                    if hit['text'] not in original['text']:citation_errors.append({'question':q['id'],'source':hit['evidence_id']})
                row={'id':q['id'],'query':q['query'],'type':q['type'],'split':q['split'],'passed':passed,'top10':ids,'gold_ids':q['gold'],'seconds':r['seconds']}
            else:row={'id':q['id'],'query':q['query'],'type':q['type'],'split':q['split'],'passed':True,'detail':tool_check(q['test'])}
        except Exception as exc:row={'id':q['id'],'query':q['query'],'type':q['type'],'split':q['split'],'passed':False,'error':str(exc)}
        results.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ['gold_ids','top10']},ensure_ascii=False),flush=True)
    retrieval=[r for r in results if r['type']=='retrieval'];tools=[r for r in results if r['type']=='tool'];recall=sum(r['passed'] for r in retrieval)/len(retrieval)
    report={'questions':len(results),'passed_questions':sum(r['passed'] for r in results),'retrieval_questions':len(retrieval),'retrieval_recall_at_10':recall,
        'development_recall_at_10':sum(r['passed'] for r in retrieval if r['split']=='development')/35,
        'held_out_recall_at_10':sum(r['passed'] for r in retrieval if r['split']=='held_out')/15,
        'tool_checks_passed':sum(r['passed'] for r in tools),'tool_checks':len(tools),'citation_errors':citation_errors,
        'warm_retrieval_p95_seconds':sorted(times)[int(.95*(len(times)-1))] if times else None,'questions_sha256':frozen,
        'acceptance_passed':recall>=.9 and all(r['passed'] for r in tools) and not citation_errors,
        'scope':'topic/source retrieval and tool behavior; not independent truth validation of all traditional rules, nor prediction accuracy',
        'results':results}
    write_json(ROOT/'evaluations/results.json',report)
    print('EVALUATION SUMMARY',json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False),flush=True)
    return 0 if report['acceptance_passed'] else 1

if __name__=='__main__':raise SystemExit(main())
