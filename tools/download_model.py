"""Pin, download and check the selected local embedding model."""
import os
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
    revision=saved['revision'] if saved and saved.get('model_id')==repo else HfApi().model_info(repo).sha
    print('Pinned model revision:',revision,flush=True)
    snapshot=snapshot_download(repo_id=repo,revision=revision,local_dir=ROOT/'models/Qwen3-Embedding-0.6B'/revision,cache_dir=CACHE/'hub',
        allow_patterns=['*.json','*.safetensors','*.txt','*.model','*.jinja','README.md','1_Pooling/*'],max_workers=3)
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
        'files':[{'name':str(p.relative_to(snapshot)),'bytes':p.stat().st_size} for p in Path(snapshot).rglob('*') if p.is_file()]}
    # Explicitly prove that the prepared snapshot loads without network access.
    offline=SentenceTransformer(snapshot,device='cpu',local_files_only=True)
    assert offline.get_embedding_dimension()==1024
    result['offline_load_verified']=True
    (ROOT/'manifests/embedding-model.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='files'},ensure_ascii=False),flush=True)
