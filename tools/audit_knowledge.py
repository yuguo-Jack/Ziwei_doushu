"""Read-only corpus, archive and cross-source traceability audit. No prediction claims."""
import sys,json,hashlib,calendar,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ziwei_kb.common import connect,read_json,write_json,sha
from ziwei_kb.cases import lookup

OUT=ROOT/'evaluations/maintenance-review';OUT.mkdir(exist_ok=True)
def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda:file.read(4*1024*1024),b''):value.update(block)
    return value.hexdigest()

def main():
    began=time.monotonic();findings=[];stats={}
    def problem(kind,id):
        if len(findings)<50:findings.append({'kind':kind,'id':id})
    with connect() as c:
        units={r['id']:dict(r) for r in c.execute('SELECT id,raw_text,content_sha256 FROM source_units')}
        for id,row in units.items():
            if sha(row['raw_text'])!=row['content_sha256']:problem('source_text_hash',id)
        chunks=0;conditions=0;nonliteral=[]
        for row in c.execute('SELECT * FROM chunks'):
            chunks+=1;raw=units[row['source_unit_id']]['raw_text']
            if sha(row['text'])!=row['content_sha256']:problem('chunk_hash',row['stable_id'])
            if row['text'] not in raw:problem('chunk_not_in_source',row['stable_id'])
            if row['eligible'] and ('\ufffd' in raw or row['evidence_kind'] in ['quarantined_excerpt','course_quote_line','dataset_candidate']):problem('ineligible_material_promoted',row['stable_id'])
            metadata=json.loads(row['metadata_json'])
            for clause in metadata.get('conditions_verbatim',[]):
                conditions+=1
                if clause not in raw:nonliteral.append(row['stable_id'])
        stats['core']={'units':len(units),'chunks':chunks,'verbatim_condition_occurrences':conditions,'nonliteral_condition_chunk_ids':list(dict.fromkeys(nonliteral))[:30]}
        if nonliteral:problem('conditions_marked_verbatim_but_not_literal',nonliteral[0])
        fts_checks=0
        for row in c.execute('SELECT id,body_terms FROM chunks WHERE id%251=0'):
            terms=row['body_terms'].split()
            if not terms:continue
            term=terms[0].replace('"','""')
            if c.execute('SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? AND rowid=?',('"'+term+'"',row['id'])).fetchone() is None:problem('fts_posting_missing',str(row['id']))
            fts_checks+=1
        stats['fts_posting_checks']=fts_checks
        artifacts=[dict(r) for r in c.execute('SELECT id,local_path,artifact_sha256 FROM sources')]
        groups=list(c.execute("SELECT source_unit_id,metadata_json FROM chunks WHERE evidence_kind='course_quote_group'"));group_members=0
        for row in groups:
            ids=json.loads(row['metadata_json'])['member_quote_ids'];text='\n'.join(units[id]['raw_text'] for id in ids)
            if text!=units[row['source_unit_id']]['raw_text']:problem('group_member_roundtrip',row['source_unit_id'])
            group_members+=len(ids)
        stats['renji_group_trace']={'groups':len(groups),'member_line_references':group_members}
    with connect(ROOT/'knowledge/reference-materials.sqlite') as c:
        total=0
        for row in c.execute('SELECT id,raw_text,content_sha256 FROM source_units'):
            if sha(row['raw_text'])!=row['content_sha256']:problem('candidate_hash',row['id'])
            total+=1
        stats['candidate_units_hashed']=total
        artifacts.extend(dict(r) for r in c.execute('SELECT id,local_path,artifact_sha256 FROM sources'))
    for row in artifacts:
        if digest(ROOT/row['local_path'])!=row['artifact_sha256']:problem('source_artifact_hash',row['id'])
    stats['source_artifacts_hashed']=len(artifacts)
    years=[];topics=0;max_chars=0
    release={r['year']:r for r in read_json(ROOT/'manifests/v4-downloads.json')['files']}
    for year in range(1950,2027):
        archive=ROOT/f'sources/v4.0-13d/year-{year}.jsonl.zst';entry=release[year]
        if archive.stat().st_size!=entry['bytes'] or digest(archive)!=entry['sha256']:problem('archive_hash',str(year))
        with connect(ROOT/f'cases/v4.0-13d/year-{year}.sqlite') as c:
            charts=c.execute('SELECT count(*) FROM cases').fetchone()[0];readings=c.execute('SELECT count(*) FROM case_topics').fetchone()[0]
            expected=(366 if calendar.isleap(year) else 365)*24
            if charts!=expected or readings!=expected*13:problem('case_counts',str(year))
            if c.execute('PRAGMA quick_check').fetchone()[0]!='ok':problem('case_database_integrity',str(year))
            largest=c.execute('SELECT max(chars) FROM topic_texts').fetchone()[0];max_chars=max(max_chars,largest)
        keys=[f'{year}-01-01-{year%12}-male',f'{year}-12-31-{(year+5)%12}-female']
        if calendar.isleap(year):keys.append(f'{year}-02-29-11-female')
        for key in keys:
            result=lookup(key,'all',100000)
            if not result['found'] or len(result['topics'])!=13:problem('case_sample_missing',key)
            for item in result.get('topics',{}).values():
                topics+=1
                if not item['hash_verified'] or item['truncated']:problem('case_sample_roundtrip',key)
        years.append({'year':year,'charts':charts,'readings':readings,'samples':len(keys),'max_topic_chars':largest})
        if year%10==0:print(f'Archive, shard and source samples verified through {year}',flush=True)
    if max_chars>100000:problem('full_export_character_limit',str(max_chars))
    stats['case_years']=years;stats['sample_topics_reconstructed']=topics;stats['maximum_archived_topic_chars']=max_chars
    report={'passed':not findings,'seconds':round(time.monotonic()-began,2),'stats':stats,'findings':findings,
        'scope':'All core/candidate text hashes and registered source artifacts, all77 original archive hashes/shard counts/quick checks, sampled exact 13-topic reconstruction across every year; not renewed reconstruction of every archived topic or expert validation of all doctrines.'}
    write_json(OUT/'knowledge-audit.json',report)
    print(json.dumps({'passed':report['passed'],'seconds':report['seconds'],'findings':findings,'sample_topics':topics},ensure_ascii=False))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
