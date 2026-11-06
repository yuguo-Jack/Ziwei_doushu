"""Extract the full released dataset's reusable explanation/source sections as candidates.

Candidate text is searchable explicitly, with its exact source case and topic.
It is not promoted to universally valid or executable theory by repetition.
"""
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import hashlib,json,re,sqlite3,sys
import zstandard
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'sources/supplementary/v4-references';OUT.mkdir(exist_ok=True)
HEADS={'一句话定调','核心论断','命盘依据','经典出处'}

def extract(year):
    target=OUT/f'year-{year}.jsonl';meta=OUT/f'year-{year}.json'
    if target.exists() and meta.exists():return json.loads(meta.read_text(encoding='utf-8'))
    path=ROOT/f'cases/v4.0-13d/year-{year}.sqlite';c=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)
    blocks=dict(c.execute('SELECT id,exact_text FROM text_blocks'));decoder=zstandard.ZstdDecompressor();found={}
    rows=c.execute('''SELECT t.id,t.layout_zstd,ct.topic,min(cs.birth_key),count(*)
        FROM topic_texts t JOIN case_topics ct ON ct.text_id=t.id JOIN cases cs ON cs.id=ct.case_id
        GROUP BY t.id,ct.topic''')
    for tid,packed,topic,key,count in rows:
        text=''.join(blocks[n] for n in json.loads(decoder.decompress(packed)))
        matches=list(re.finditer(r'\*\*【([^】]+)】\*\*',text))
        for i,m in enumerate(matches):
            head=m[1]
            if head not in HEADS:continue
            part=text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)].strip()
            if len(part)<8:continue
            digest=hashlib.sha256((topic+'\0'+head+'\0'+part).encode()).hexdigest()
            if digest not in found:found[digest]={'hash':digest,'topic':topic,'section':head,'text':part,'occurrences':0,'examples':[]}
            row=found[digest];row['occurrences']+=count
            if len(row['examples'])<2:row['examples'].append({'year':year,'key':key,'topic':topic,'text_id':tid})
    c.close();target.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in found.values()),encoding='utf-8')
    result={'year':year,'reference_sections':len(found),'bytes':target.stat().st_size};meta.write_text(json.dumps(result),encoding='utf-8');return result

if __name__=='__main__':
    # The merged snapshot remains sufficient after removing verified yearly intermediates.
    # An explicit --rebuild regenerates those intermediates from the lossless case shards.
    manifest=ROOT/'manifests/dataset-references.json'
    snapshot=ROOT/'sources/supplementary/v4-reference-materials.jsonl'
    if '--rebuild' not in sys.argv and manifest.exists() and snapshot.exists():
        saved=json.loads(manifest.read_text(encoding='utf-8'))
        if saved.get('complete') and saved.get('sha256'):
            digest=hashlib.sha256()
            with snapshot.open('rb') as f:
                for block in iter(lambda:f.read(4*1024*1024),b''):digest.update(block)
            if snapshot.stat().st_size==saved.get('bytes') and digest.hexdigest()==saved['sha256']:
                print(json.dumps({'status':'verified_existing_snapshot',**saved},ensure_ascii=False),flush=True)
                raise SystemExit(0)
    results=[]
    with ProcessPoolExecutor(max_workers=3) as pool:
        for f in as_completed([pool.submit(extract,y) for y in range(1950,2027)]):
            row=f.result();results.append(row);print(json.dumps(row),flush=True)
    merged={}
    for year in range(1950,2027):
        for line in (OUT/f'year-{year}.jsonl').read_text(encoding='utf-8').splitlines():
            row=json.loads(line);h=row['hash']
            if h not in merged:merged[h]=row
            else:
                merged[h]['occurrences']+=row['occurrences']
                for ex in row['examples']:
                    if len(merged[h]['examples'])<4 and ex not in merged[h]['examples']:merged[h]['examples'].append(ex)
    path=ROOT/'sources/supplementary/v4-reference-materials.jsonl'
    path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in merged.values()),encoding='utf-8')
    report={'complete':True,'years':77,'distinct_sections':len(merged),'by_section':{},'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'policy':'candidate source-linked interpretations, not recovered private universal rules'}
    for row in merged.values():report['by_section'][row['section']]=report['by_section'].get(row['section'],0)+1
    (ROOT/'manifests/dataset-references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False),flush=True)
