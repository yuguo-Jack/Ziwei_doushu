"""Pin, download and check the selected local embedding model."""
import hashlib,os
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'models/.download-state'
os.environ['HF_HOME']=str(CACHE)
os.environ['HF_HUB_CACHE']=str(CACHE/'hub')
os.environ['HF_XET_CACHE']=str(CACHE/'xet')
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
from huggingface_hub import snapshot_download

def verified(path,row):
    if not path.is_file() or path.is_symlink() or path.stat().st_size!=row['bytes']:return False
    digest=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda:file.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()==row['sha256']

if __name__=='__main__':
    saved=json.loads((ROOT/'config/embedding-model.json').read_text(encoding='utf-8'))
    expected=json.loads((ROOT/'config/model-checksums.json').read_text(encoding='utf8'))
    repo=saved['model_id'];revision=saved['revision']
    if expected['revision']!=revision:raise RuntimeError('模型校验清单与固定revision不同。')
    target=(ROOT/saved['snapshot_path']).resolve()
    if not target.is_relative_to((ROOT/'models').resolve()):raise RuntimeError('固定模型必须保存在工作区models/内。')
    (ROOT/'manifests').mkdir(parents=True,exist_ok=True)
    print('Pinned model revision:',revision,flush=True)
    valid=[verified(target/row['path'],row) for row in expected['files']]
    if all(valid):snapshot=str(target)
    else:
        snapshot=snapshot_download(repo_id=repo,revision=revision,local_dir=target,cache_dir=CACHE/'hub',
            allow_patterns=[row['path'] for row in expected['files']],max_workers=3,
            force_download=any((target/row['path']).exists() and not ok for row,ok in zip(expected['files'],valid)))
    for row in expected['files']:
        path=Path(snapshot)/row['path'].replace('\\','/')
        if not verified(path,row):raise RuntimeError('模型文件缺失或SHA-256错误：'+row['path'])
    import torch
    from sentence_transformers import SentenceTransformer
    model=SentenceTransformer(snapshot,device='cuda' if torch.cuda.is_available() else 'cpu',
        model_kwargs={'dtype':torch.float16} if torch.cuda.is_available() else {})
    model.max_seq_length=saved['max_seq_length']
    example=model.encode(['紫微斗数三方四正的含义','命宫、财帛、官禄、迁移的相互关系'],normalize_embeddings=True)
    assert example.shape==(2,saved['dimensions'])
    result={**saved,'snapshot_path':Path(snapshot).relative_to(ROOT).as_posix(),'inference_dtype':'float16' if torch.cuda.is_available() else 'float32',
        'device':'cuda' if torch.cuda.is_available() else 'cpu','offline_load_verified':False,
        'files':[{'name':p.relative_to(snapshot).as_posix(),'bytes':p.stat().st_size} for p in Path(snapshot).rglob('*') if p.is_file() and '.cache' not in p.relative_to(snapshot).parts]}
    # Explicitly prove that the prepared snapshot loads without network access.
    del model
    offline=SentenceTransformer(snapshot,device='cpu',local_files_only=True)
    assert offline.get_embedding_dimension()==saved['dimensions']
    result['offline_load_verified']=True
    for name,value in [('model-checksums.json',expected),('embedding-model.json',result)]:
        path=ROOT/'manifests'/name;stage=path.with_suffix('.tmp')
        stage.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');stage.replace(path)
    print(json.dumps({k:v for k,v in result.items() if k!='files'},ensure_ascii=False),flush=True)
