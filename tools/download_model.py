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
from huggingface_hub import HfApi,snapshot_download

if __name__=='__main__':
    repo='Qwen/Qwen3-Embedding-0.6B'
    manifest=ROOT/'manifests/embedding-model.json'
    saved=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else None
    if not saved or saved.get('model_id')!=repo:raise RuntimeError('请先用安装器初始化固定模型清单，或从config复制对应模型与校验清单；不自动选择未知最新版本。')
    revision=saved['revision']
    print('Pinned model revision:',revision,flush=True)
    snapshot=snapshot_download(repo_id=repo,revision=revision,local_dir=ROOT/'models/Qwen3-Embedding-0.6B'/revision,cache_dir=CACHE/'hub',
        allow_patterns=['*.json','*.safetensors','*.txt','*.model','*.jinja','README.md','1_Pooling/*'],max_workers=3)
    expected=json.loads((ROOT/'manifests/model-checksums.json').read_text(encoding='utf8'))
    if expected['revision']!=revision:raise RuntimeError('模型校验清单与固定revision不同。')
    for row in expected['files']:
        path=Path(snapshot)/row['path'].replace('\\','/')
        if not path.is_file() or path.stat().st_size!=row['bytes']:raise RuntimeError('模型文件缺失或大小错误：'+row['path'])
        digest=hashlib.sha256()
        with path.open('rb') as file:
            for block in iter(lambda:file.read(1024*1024),b''):digest.update(block)
        if digest.hexdigest()!=row['sha256']:raise RuntimeError('模型SHA-256错误：'+row['path'])
    import torch
    from sentence_transformers import SentenceTransformer
    model=SentenceTransformer(snapshot,device='cuda' if torch.cuda.is_available() else 'cpu',
        model_kwargs={'dtype':torch.float16} if torch.cuda.is_available() else {})
    model.max_seq_length=2048
    example=model.encode(['紫微斗数三方四正的含义','命宫、财帛、官禄、迁移的相互关系'],normalize_embeddings=True)
    assert example.shape==(2,1024)
    result={'model_id':repo,'revision':revision,'snapshot_path':Path(snapshot).relative_to(ROOT).as_posix(),'storage':'workspace-owned regular files; independent of shared Hugging Face cache','dimensions':1024,
        'max_seq_length':2048,'normalized':True,'dtype':'float32','inference_dtype':'float16' if torch.cuda.is_available() else 'float32',
        'query_prompt':'Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: ',
        'device':'cuda' if torch.cuda.is_available() else 'cpu','offline_load_verified':False,
        'files':[{'name':p.relative_to(snapshot).as_posix(),'bytes':p.stat().st_size} for p in Path(snapshot).rglob('*') if p.is_file() and '.cache' not in p.relative_to(snapshot).parts]}
    # Explicitly prove that the prepared snapshot loads without network access.
    offline=SentenceTransformer(snapshot,device='cpu',local_files_only=True)
    assert offline.get_embedding_dimension()==1024
    result['offline_load_verified']=True
    (ROOT/'manifests/embedding-model.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='files'},ensure_ascii=False),flush=True)
