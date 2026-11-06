"""Download the complete v4.0 yearly archives and verify each published SHA-256."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'sources/v4.0-13d'
OUT.mkdir(parents=True,exist_ok=True)
MANIFEST=json.loads((ROOT/'data/MANIFEST.json').read_text(encoding='utf-8'))

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def get(entry):
    name=f"year-{entry['year']}.jsonl.zst"
    target=OUT/name
    if not target.exists() and (ROOT/'data'/name).exists():shutil.copy2(ROOT/'data'/name,target)
    if target.exists() and digest(target)==entry['sha256']:
        return {'year':entry['year'],'status':'verified_existing','bytes':target.stat().st_size,'sha256':entry['sha256']}
    url='https://github.com/Renhuai123/ziwei-doushu/releases/download/v4.0-13d/'+name
    error=None
    part=target.with_suffix('.zst.part')
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'ZiweiLocalKnowledge/1.0'})
            with urllib.request.urlopen(req,timeout=90) as response, part.open('wb') as f:shutil.copyfileobj(response,f)
            assert part.stat().st_size==entry['zstBytes'],name+' size mismatch'
            assert digest(part)==entry['sha256'],name+' hash mismatch'
            part.replace(target)
            return {'year':entry['year'],'status':'downloaded_verified','bytes':target.stat().st_size,'sha256':entry['sha256']}
        except Exception as exc:error=exc;time.sleep(attempt+1)
    raise RuntimeError(f'{name}: {error}')

if __name__=='__main__':
    for name in ['MANIFEST.json','SHA256SUMS.txt']:shutil.copy2(ROOT/'data'/name,OUT/name)
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for task in as_completed([pool.submit(get,x) for x in MANIFEST['files']]):
            row=task.result();results.append(row);print(json.dumps(row),flush=True)
    results.sort(key=lambda x:x['year'])
    assert len(results)==77
    (ROOT/'manifests/v4-downloads.json').write_text(json.dumps({'complete':True,'files':results,'total_bytes':sum(x['bytes'] for x in results)},indent=2),encoding='utf-8')
    print('ALL 77 YEAR ARCHIVES VERIFIED',flush=True)
