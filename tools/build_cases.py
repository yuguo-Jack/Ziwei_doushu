"""Build all verified yearly case archives, with exact reconstruction verification."""
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib,io,json,re,sqlite3,time
from pathlib import Path
import zstandard

ROOT=Path(__file__).resolve().parents[1]
BUILD_VERSION='cases-1.0'

def build_year(entry):
    year=entry['year'];dest=ROOT/f'cases/v4.0-13d/year-{year}.sqlite';meta=dest.with_suffix('.json')
    if dest.exists() and meta.exists():
        old=json.loads(meta.read_text(encoding='utf-8'))
        if old.get('build_version')==BUILD_VERSION and old.get('archive_sha256')==entry['sha256'] and old.get('validated') and old.get('sqlite_bytes')==dest.stat().st_size:
            with sqlite3.connect(dest.resolve().as_uri()+'?mode=ro',uri=True) as existing:
                if existing.execute('PRAGMA quick_check').fetchone()[0]=='ok':return old
    archive=ROOT/f'sources/v4.0-13d/year-{year}.jsonl.zst'
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==entry['sha256']
    stage=dest.with_suffix('.building.sqlite')
    if stage.exists():
        assert stage.resolve().parent==(ROOT/'cases/v4.0-13d').resolve();stage.unlink()
    conn=sqlite3.connect(stage)
    conn.executescript((ROOT/'design/case-shard-schema.sql').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'data/MANIFEST.json').read_text(encoding='utf-8'))
    profile={'scope':'natal','calendar':'Gregorian','hour_kind':'branch_index_0_11',
        'longitude_correction':'not_per_location','brightness_school':'XD2 (declared in upstream README)',
        'leap_month_policy':'unknown','late_zi_policy':'branch-index archive; no clock input',
        'engine_source':manifest['engineCommit'],'current_engine_compatibility':'not_assumed'}
    conn.execute('INSERT INTO dataset_profile VALUES (?,?,?,?,?,?,?,?)',('v4.0-13d',manifest['contentVersion'],entry['sha256'],year,json.dumps(profile,ensure_ascii=False),entry['charts'],entry['readings'],'staging'))
    block_ids={};block_text={};topics={};topic_layouts={};compressor=zstandard.ZstdCompressor(level=3)
    raw_bytes=0;count=0;started=time.perf_counter()
    with archive.open('rb') as source,zstandard.ZstdDecompressor(max_window_size=128*1024*1024).stream_reader(source) as stream:
        for cid,line in enumerate(io.TextIOWrapper(stream,encoding='utf-8',newline=''),1):
            raw_bytes+=len(line.encode('utf-8'));row=json.loads(line)
            import datetime
            date=datetime.date(row['y'],row['m'],row['d'])
            assert row['y']==year and 0<=row['h']<=11 and row['g'] in ['male','female']
            assert row['k']==f"{date.isoformat()}-{row['h']}-{row['g']}"
            assert set(row['c'])==set(manifest['topics'])
            conn.execute('INSERT INTO cases VALUES (?,?,?,?,?,?,?,?)',(cid,row['k'],row['y'],row['m'],row['d'],row['h'],row['g'],json.dumps({k:v for k,v in row.items() if k!='c'},ensure_ascii=False)))
            for topic,text in row['c'].items():
                data=text.encode('utf-8');sha=hashlib.sha256(data).digest();tid=topics.get(sha)
                if tid is None:
                    layout=[]
                    for part in re.split(r'(\n{2,})',text):
                        if not part:continue
                        ph=hashlib.sha256(part.encode('utf-8')).digest();bid=block_ids.get(ph)
                        if bid is None:
                            bid=len(block_ids)+1;block_ids[ph]=bid;block_text[bid]=part
                            conn.execute('INSERT INTO text_blocks VALUES (?,?,?)',(bid,ph,part))
                        layout.append(bid)
                    tid=len(topics)+1;topics[sha]=tid
                    packed=compressor.compress(json.dumps(layout,separators=(',',':')).encode())
                    topic_layouts[tid]=(sha,packed)
                    conn.execute('INSERT INTO topic_texts VALUES (?,?,?,?,?)',(tid,sha,packed,len(text),len(data)))
                conn.execute('INSERT INTO case_topics VALUES (?,?,?)',(cid,topic,tid));count+=1
            if cid%512==0:conn.commit()
    assert raw_bytes==entry['rawBytes'] and cid==entry['charts'] and count==entry['readings']
    conn.commit();decoder=zstandard.ZstdDecompressor()
    # Verify every unique persisted topic layout, not merely a few examples.
    for tid,sha,packed in conn.execute('SELECT id,sha256,layout_zstd FROM topic_texts'):
        text=''.join(block_text[n] for n in json.loads(decoder.decompress(packed)))
        assert hashlib.sha256(text.encode('utf-8')).digest()==sha,(year,tid)
    assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert not conn.execute('PRAGMA foreign_key_check').fetchall()
    assert conn.execute('SELECT count(*) FROM cases').fetchone()[0]==entry['charts']
    conn.execute("UPDATE dataset_profile SET coverage_status='validated'");conn.commit();conn.close()
    stage.replace(dest)
    result={'year':year,'build_version':BUILD_VERSION,'validated':True,'archive_sha256':entry['sha256'],
        'charts':cid,'readings':count,'unique_topic_texts':len(topics),'unique_text_blocks':len(block_ids),
        'reconstructed_unique_topics_verified':len(topics),'sqlite_bytes':dest.stat().st_size,
        'source_raw_bytes':raw_bytes,'seconds':round(time.perf_counter()-started,2),'path':str(dest.relative_to(ROOT))}
    meta.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=3);p.add_argument('--years',type=int,nargs='*');args=p.parse_args()
    manifest=json.loads((ROOT/'data/MANIFEST.json').read_text(encoding='utf-8'))
    rows=[x for x in manifest['files'] if not args.years or x['year'] in args.years];results=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for task in as_completed([pool.submit(build_year,x) for x in rows]):
            result=task.result();results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
    results.sort(key=lambda x:x['year'])
    report={'build_version':BUILD_VERSION,'complete':len(results)==77,'years':len(results),
        'charts':sum(x['charts'] for x in results),'readings':sum(x['readings'] for x in results),
        'sqlite_bytes':sum(x['sqlite_bytes'] for x in results),'files':results}
    if report['complete']:
        assert report['charts']==674976 and report['readings']==8774688
    (ROOT/'manifests/cases.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('CASE BUILD FINISHED',json.dumps({k:v for k,v in report.items() if k!='files'}),flush=True)
