"""Build an offline dense index from eligible canonical source chunks."""
import argparse,os,sys,json,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from ziwei_kb.common import connect,read_json,write_json,model_path
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--rebuild',action='store_true');args=parser.parse_args()
    import numpy as np,torch
    from sentence_transformers import SentenceTransformer
    model_spec=read_json(ROOT/'manifests/embedding-model.json')
    with connect() as conn:rows=[dict(r) for r in conn.execute('SELECT id,stable_id,title,text,namespace,evidence_kind,content_sha256 FROM chunks WHERE eligible=1 ORDER BY id')]
    fingerprint=hashlib.sha256(json.dumps([(r['stable_id'],r['title'],r['content_sha256']) for r in rows]).encode()).hexdigest()
    contract={k:model_spec[k] for k in ['revision','dimensions','max_seq_length','normalized','query_prompt']}
    generation_hash=hashlib.sha256(json.dumps([fingerprint,contract],sort_keys=True).encode()).hexdigest()
    generation=f"qwen3-{model_spec['revision'][:8]}-{generation_hash[:10]}";out=ROOT/'indexes'/generation;out.mkdir(exist_ok=True)
    if args.rebuild or not all((out/name).is_file() for name in ['manifest.json','vectors.npy','rows.json']):
        device='cuda' if torch.cuda.is_available() else 'cpu';torch.set_num_threads(4)
        model=SentenceTransformer(str(model_path(model_spec)),device=device,local_files_only=True,
            model_kwargs={'dtype':torch.float16} if device=='cuda' else {})
        model.max_seq_length=model_spec['max_seq_length']
        started=time.perf_counter()
        documents=[r['title']+'\n'+r['text'] for r in rows];lengths=[]
        for at in range(0,len(documents),128):lengths.extend(len(x) for x in model.tokenizer(documents[at:at+128],truncation=False)['input_ids'])
        oversized=[{'id':rows[i]['stable_id'],'tokens':n} for i,n in enumerate(lengths) if n>model_spec['max_seq_length']]
        length_audit={'documents':len(documents),'max_document_tokens':max(lengths),'configured_max_seq_length':model_spec['max_seq_length'],'oversized_documents':oversized,'input':'Exact title + newline + document text passed to model.encode'}
        write_json(ROOT/'manifests/embedding-token-lengths.json',length_audit)
        assert not oversized,'Source chunks exceed embedding length; increase the supported length or split chunks before indexing.'
        vectors=model.encode(documents,batch_size=16,show_progress_bar=True,normalize_embeddings=True,convert_to_numpy=True)
        assert vectors.shape==(len(rows),1024) and np.isfinite(vectors).all()
        vectors=vectors.astype('float32');assert np.allclose(np.linalg.norm(vectors,axis=1),1,atol=.003)
        np.save(out/'vectors.npy',vectors,allow_pickle=False)
        write_json(out/'rows.json',[{k:r[k] for k in ['id','stable_id','namespace','evidence_kind']} for r in rows])
        manifest={'generation':generation,'rows':len(rows),'dimensions':1024,'fingerprint':fingerprint,'model':model_spec,
            'vector_file':'vectors.npy','row_map':'rows.json','seconds':round(time.perf_counter()-started,2),'device':device,
            'vectors_sha256':hashlib.sha256((out/'vectors.npy').read_bytes()).hexdigest(),'token_length_audit':length_audit}
        write_json(out/'manifest.json',manifest)
    else:
        manifest=read_json(out/'manifest.json')
        write_json(ROOT/'manifests/embedding-token-lengths.json',manifest['token_length_audit'])
    write_json(ROOT/'indexes/current.json',{'generation':generation,'manifest_path':str((out/'manifest.json').relative_to(ROOT))})
    print(json.dumps({k:v for k,v in manifest.items() if k!='model'},ensure_ascii=False),flush=True)
