import hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    folder=ROOT/'indexes/twins-major-split-v1';meta=json.loads((folder/'build.json').read_text(encoding='utf-8'))
    features=np.empty((meta['rows'],16),dtype='uint8');dates=np.empty((meta['rows'],4),dtype='uint16');i=0
    for line in (folder/'features.jsonl').open(encoding='utf-8'):
        y,m,d,values=json.loads(line)
        for h,row in enumerate(values):features[i]=row;dates[i]=[y,m,d,h];i+=1
    assert i==meta['rows']==337488
    np.save(folder/'features.npy',features,allow_pickle=False);np.save(folder/'dates.npy',dates,allow_pickle=False)
    meta['files']=[{'path':str((folder/name).relative_to(ROOT)),'sha256':hashlib.sha256((folder/name).read_bytes()).hexdigest(),'bytes':(folder/name).stat().st_size} for name in ['features.npy','dates.npy']]
    verifier=ROOT/'tools/verify_twins.ts'
    meta['runtime_verifier']={'path':str(verifier.relative_to(ROOT)),'sha256':hashlib.sha256(verifier.read_bytes()).hexdigest(),'bytes':verifier.stat().st_size,'scope':'Native full-structure verification of every exact 16-component candidate; supplementary to the necessary geometry filter.'}
    (ROOT/'manifests/twins.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(meta,ensure_ascii=False,indent=2))
