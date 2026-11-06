"""Frozen source-retrieval questions plus behavioral tool/invariant checks."""
import sys,json,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ziwei_kb.common import write_json,read_json
from ziwei_kb.retrieval import search,source_record
from ziwei_kb.cases import lookup
from ziwei_kb.engine import chart,context

def prepare():
    (ROOT/'evaluations').mkdir(exist_ok=True)
    return read_json(ROOT/'tests/fixtures/retrieval-questions.json')

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
        r=chart(read_json(ROOT/'examples/fictional-first.json'));assert r['normalized_birth']['hour']==4;assert r['calculation_profile']['as_of'];return 'clock08:30 remains branch4 with source longitude'
    if test=='solar_boundary':
        r=chart({'year':2026,'month':11,'day':3,'clock_hour':12,'clock_minute':55,'longitude':120,'gender':'male'});assert r['normalized_birth']['hour']==7;return 'equation of time crosses noon branch'
    if test=='unknown_time':
        try:chart({'year':1990,'month':1,'day':1,'gender':'male','unknown_time':True})
        except ValueError:return 'unknown time explicitly rejected'
        raise AssertionError('unknown time silently accepted')
    if test=='profile':
        r=chart({'year':1990,'month':1,'day':1,'hour':0,'gender':'male'});assert r['case_compatibility']['status']=='partial';assert lookup(r['birth_key'])['profile']['leap_month_policy']=='unknown';return 'known and unknown policy differences retained'
    if test=='context_conditions':
        r=context(read_json(ROOT/'examples/fictional-first.json'),'解释事业及依据','career');assert r['topic_geometry']['is_empty'];assert r['topic_geometry']['physical_main_stars']==[];assert r['topic_geometry']['borrowed_stars'];assert all(h['evidence_id']!='CODE-detectHuaQuanRuGuan' for h in r['evidence']['hits']);assert r['archive_consistency_notes'];return 'physical placement and borrowed stars distinct; inactive code rule excluded'
    if test=='source_roundtrip':
        r=source_record('TJ-462faa4-0396');assert r['locator']['seconds']==1347 and r['revision'].startswith('462faa4') and r['notes'];return 'quote, timestamp, revision and editorial note preserved'
    raise AssertionError(test)

def main():
    questions=prepare();frozen=hashlib.sha256((ROOT/'tests/fixtures/retrieval-questions.json').read_bytes()).hexdigest()
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
