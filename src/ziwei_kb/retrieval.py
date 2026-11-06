import json,os,subprocess,sys,time,urllib.request,urllib.error,hashlib
from functools import lru_cache
import numpy as np
from .common import ROOT,connect,tokenize,infer_namespace,read_json,normalize,model_path,embedding_contract,installation

def service_health():
    try:
        with urllib.request.urlopen('http://127.0.0.1:8788/health',timeout=.5) as r:result=json.load(r)
        return result if result.get('service')=='ziwei-query-encoder' and result.get('workspace')==str(ROOT) else None
    except Exception:return None

def query_vectors(queries):
    (ROOT/'logs').mkdir(parents=True,exist_ok=True)
    health=service_health()
    spec=read_json(ROOT/'manifests/embedding-model.json');expected_contract=embedding_contract(spec)
    if health and health.get('contract')!=expected_contract:
        raise RuntimeError('查询编码器仍使用旧模型路径或配置；等待5分钟闲置退出，或按维护文档重启本工作区编码器。')
    if not health:
        log=(ROOT/'logs/query-encoder.log').open('a',encoding='utf-8')
        flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src');env['PYTHONUTF8']='1'
        subprocess.Popen([sys.executable,'-X','utf8','-m','ziwei_kb.embedding_service'],cwd=ROOT,env=env,
            stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=flags);log.close()
        for _ in range(80):
            if service_health():break
            time.sleep(.1)
        else:raise RuntimeError('本地查询编码器未能启动；检查 logs/query-encoder.log 或端口8788。')
    request=urllib.request.Request('http://127.0.0.1:8788/encode',data=json.dumps({'queries':queries},ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=90) as r:result=json.load(r)
    except urllib.error.HTTPError as exc:
        try:message=json.loads(exc.read().decode('utf-8')).get('error',str(exc))
        except Exception:message=str(exc)
        raise RuntimeError('查询编码器：'+message) from exc
    if result.get('revision')!=spec['revision'] or result.get('contract')!=expected_contract:raise RuntimeError('查询编码器版本或配置与索引不一致。')
    vectors=np.asarray(result['vectors'],dtype='float32')
    if vectors.shape!=(len(queries),1024) or not np.isfinite(vectors).all():raise RuntimeError('查询编码器返回的向量维度或数值非法。')
    return vectors

def dense_index():
    current=read_json(ROOT/'indexes/current.json')
    return _dense_index(current['generation'],(ROOT/'knowledge/knowledge.sqlite').stat().st_mtime_ns,embedding_contract(read_json(ROOT/'manifests/embedding-model.json')))

@lru_cache(maxsize=2)
def _dense_index(generation,source_mtime,contract):
    current=read_json(ROOT/'indexes/current.json');manifest=read_json(ROOT/current['manifest_path']);path=ROOT/'indexes'/current['generation']
    if manifest['model']['revision']!=read_json(ROOT/'manifests/embedding-model.json')['revision']:raise RuntimeError('向量索引与当前嵌入模型版本不同，请重建索引。')
    rows=read_json(path/manifest['row_map']);vectors=np.load(path/manifest['vector_file'],mmap_mode='r',allow_pickle=False)
    if len(rows)!=vectors.shape[0] or vectors.shape[1]!=1024:raise RuntimeError('向量索引元数据不一致。')
    with connect() as conn:
        source_rows=[dict(r) for r in conn.execute('SELECT id,stable_id,namespace,evidence_kind,title,content_sha256 FROM chunks WHERE eligible=1 ORDER BY id')]
    expected_map=[{k:r[k] for k in ['id','stable_id','namespace','evidence_kind']} for r in source_rows]
    if rows!=expected_map:raise RuntimeError('向量行映射与来源ID不一致，请重建索引；未使用可能错配的引文。')
    fingerprint=hashlib.sha256(json.dumps([(r['stable_id'],r['title'],r['content_sha256']) for r in source_rows]).encode()).hexdigest()
    if fingerprint!=manifest['fingerprint']:raise RuntimeError('原文库已变化，向量索引未更新；请运行tools/build_embeddings.py。')
    spec=read_json(ROOT/'manifests/embedding-model.json')
    if any(manifest['model'].get(k)!=spec.get(k) for k in ['dimensions','max_seq_length','normalized','query_prompt']):raise RuntimeError('嵌入配置与索引不一致，请重新构建。')
    return rows,vectors

def source_record(id,max_chars=6000,neighbors=0):
    if not isinstance(id,str) or not id:raise ValueError('来源ID不能为空。')
    if type(max_chars) is not int or not 1<=max_chars<=100000:raise ValueError('max_chars范围1–100000。')
    if type(neighbors) is not int or not 0<=neighbors<=5:raise ValueError('neighbors范围0–5。')
    if id.startswith('CASE:'):
        from .cases import lookup
        parts=id.split(':')
        if len(parts)!=4 or parts[1]!='v4.0-13d':raise ValueError('案例来源标识无效。')
        case=lookup(parts[2],parts[3],max_chars)
        if not case.get('found'):raise ValueError(case.get('reason','精确案例不存在。'))
        item=case['topics'][parts[3]]
        return {'id':id,'title':'旧版本命案例 · '+item['label'],'text':item['text'],'total_chars':item['total_chars'],'truncated':item['truncated'],
          'artifact_kind':'archived_case','kind':'archived_case','canonical_url':case['source_url'],'source_url':case['source_url'],
          'revision':case['content_version'],'locator':{'birth_key':case['birth_key'],'topic':parts[3]},'conditions':[],
          'conditions_status':'archived_natal_only','notes':'精确出生配置的旧版存档；须与当前排盘口径分别核对，不作为流年专用原文。',
          'verification':{'hash_verified':item['hash_verified'],'sha256':item['sha256'],'archive_sha256':case['archive_sha256']},'license':case['license'],'profile':case['profile']}
    databases=[ROOT/'knowledge/knowledge.sqlite',ROOT/'knowledge/reference-materials.sqlite']
    for database in databases:
      if not database.exists():continue
      with connect(database) as c:
        row=c.execute('''SELECT u.*,s.canonical_url,s.revision,s.license_json,s.kind AS artifact_kind FROM source_units u JOIN sources s ON s.id=u.source_id WHERE u.id=?''',(id,)).fetchone()
        if row is None:continue
        result=dict(row);result['text']=result.pop('raw_text');result.pop('normalized_text',None)
        chunk=c.execute('SELECT title,metadata_json FROM chunks WHERE source_unit_id=? ORDER BY id LIMIT 1',(id,)).fetchone()
        if chunk:
            meta=json.loads(chunk['metadata_json']);result['metadata']=meta;result['title']=chunk['title'];result['source_url']=meta.get('source_url',result['canonical_url']);result['conditions']=meta.get('conditions_verbatim',[]);result['conditions_status']=meta.get('conditions_status')
        for key in ['locator_json','verification_json','license_json']:result[key.removesuffix('_json')]=json.loads(result.pop(key))
        result['total_chars']=len(result['text']);result['truncated']=len(result['text'])>max_chars;result['text']=result['text'][:max_chars]
        if neighbors and result['locator'].get('bvid'):
            loc=result['locator']
            group=[dict(r) for r in c.execute('''SELECT id,raw_text,locator_json,notes FROM source_units WHERE source_id=?
                AND json_extract(locator_json,'$.bvid')=? AND json_extract(locator_json,'$.part')=?
                AND json_extract(locator_json,'$.section')=? ORDER BY json_extract(locator_json,'$.seconds')''',
                (result['source_id'],loc['bvid'],loc['part'],loc['section']))]
            index=next((i for i,r in enumerate(group) if r['id']==id),0);near=[]
            for r in group[max(0,index-neighbors):index+neighbors+1]:
                if r['id']==id:continue
                where=json.loads(r['locator_json']);near.append({'evidence_id':r['id'],'text':r['raw_text'][:1200],'locator':where,'notes':r['notes'],
                    'source_url':f"https://www.bilibili.com/video/{where['bvid']}?p={where['part']}&t={where['seconds']}"})
            result['neighboring_source_passages']=near;result['context_note']='Adjacent available quotations in the same recorded semantic section; not a full transcript or substitute for the video board.'
        elif neighbors and result['locator'].get('paragraph') is not None:
            n=result['locator']['paragraph']
            near=[]
            for row in c.execute("SELECT id,raw_text,locator_json,notes FROM source_units WHERE source_id=? AND json_extract(locator_json,'$.paragraph') BETWEEN ? AND ? AND id!=? ORDER BY json_extract(locator_json,'$.paragraph')",(result['source_id'],n-neighbors,n+neighbors,id)):
                loc=json.loads(row['locator_json']);near.append({'evidence_id':row['id'],'text':row['raw_text'][:2000],'locator':loc,'notes':row['notes'],'source_url':result['canonical_url']+'#'+loc.get('anchor','')})
            result['neighboring_source_passages']=near;result['context_note']='Adjacent original paragraphs; headings and clauses can establish conditions missing from a single retrieved paragraph.'
        return result
    raise ValueError('没有该来源 ID。')

def search(query,limit=6,namespace=None,mode='hybrid',include_candidates=False,query_vector=None,_database=None):
    if not isinstance(query,str) or not query.strip() or len(query)>3000:raise ValueError('问题应为1–3000字符。')
    if type(limit) is not int or not 1<=limit<=50:raise ValueError('limit范围1–50。')
    if mode not in ['hybrid','lexical']:raise ValueError('mode只能为hybrid或lexical。')
    if namespace is not None and namespace not in ['ziwei','yijing','fengshui','tieban','tianji','historical_ziwei','renji','all']:raise ValueError('namespace不支持。')
    if type(include_candidates) is not bool:raise ValueError('include_candidates必须明确为布尔值。')
    if include_candidates and _database is None:
        started=time.perf_counter()
        primary=search(query,limit,namespace,mode,True,query_vector,ROOT/'knowledge/knowledge.sqlite')
        primary['quarantined_materials_included']=True
        ref=ROOT/'knowledge/reference-materials.sqlite'
        if ref.exists():
            candidate=search(query,limit,namespace,'lexical',True,None,ref)
            joined=[]
            for i in range(max(len(primary['hits']),len(candidate['hits']))):
                if i<len(primary['hits']):joined.append(primary['hits'][i])
                if i<len(candidate['hits']):joined.append(candidate['hits'][i])
            primary['hits']=joined[:limit];primary['candidate_materials_included']=True;primary['candidate_usage']='Candidates retain source cases and unresolved conditions; not validated universal rules.'
        primary['seconds']=round(time.perf_counter()-started,4)
        return primary
    started=time.perf_counter();namespace=namespace or infer_namespace(query);tokens=tokenize(query,query=True)
    params=[];where=[]
    if namespace!='all':where.append('c.namespace=?');params.append(namespace)
    if not include_candidates:where.append('c.eligible=1')
    clause=' AND '+' AND '.join(where) if where else ''
    if mode=='hybrid' and installation().get('semantic') is False:mode='lexical'
    lexical=[];dense=[];degraded=None
    with connect(_database) as conn:
        if tokens:
            expression=' OR '.join('"'+x.replace('"','""')+'"' for x in tokens)
            lexical=[r[0] for r in conn.execute('SELECT c.id FROM chunks_fts JOIN chunks c ON c.id=chunks_fts.rowid WHERE chunks_fts MATCH ?'+clause+' ORDER BY bm25(chunks_fts,3.0,1.0) LIMIT 60',[expression,*params])]
        if mode=='hybrid':
            try:
                rows,vectors=dense_index();v=query_vector if query_vector is not None else query_vectors([query])[0]
                scores=vectors@v
                allowed=np.array([namespace=='all' or r['namespace']==namespace for r in rows]);scores=np.where(allowed,scores,-np.inf)
                n=min(60,int(allowed.sum()))
                if n:
                    ids=np.argpartition(scores,-n)[-n:];ids=ids[np.argsort(scores[ids])[::-1]];dense=[rows[int(i)]['id'] for i in ids]
            except Exception as exc:degraded=str(exc)
        merged={}
        for ids,weight in [(lexical,1.0),(dense,1.0)]:
            for rank,id in enumerate(ids,1):merged[id]=merged.get(id,0)+weight/(60+rank)
        # Literal domain terms in titles improve exact proper-name retrieval.
        shortlist=sorted(merged,key=merged.get,reverse=True)[:100]
        records=[]
        for id in shortlist:
            row=conn.execute('''SELECT c.*,u.notes,u.locator_json,u.verification_json,s.canonical_url,s.revision,s.license_json
                FROM chunks c JOIN source_units u ON u.id=c.source_unit_id JOIN sources s ON s.id=u.source_id WHERE c.id=?''',(id,)).fetchone()
            if not row:continue
            row=dict(row);score=merged[id]
            exact_terms=[t for t in tokens if len(t)>=3 and t in normalize(row['title'])]
            if exact_terms:score*=1.15
            if row['evidence_kind']=='project_guide':score*=1.12
            records.append((score,row))
        records.sort(key=lambda x:x[0],reverse=True);hits=[];seen=set()
        for score,row in records:
            dedup=(row['source_unit_id'],row['content_sha256'])
            if dedup in seen:continue
            seen.add(dedup);meta=json.loads(row['metadata_json'])
            hits.append({'evidence_id':row['source_unit_id'],'chunk_id':row['stable_id'],'title':row['title'],'text':row['text'],
                'kind':row['evidence_kind'],'namespace':row['namespace'],'source_url':meta.get('source_url',row['canonical_url']),
                'revision':row['revision'],'locator':json.loads(row['locator_json']),'license':json.loads(row['license_json']),
                'conditions':meta.get('conditions_verbatim',[]),'conditions_status':meta.get('conditions_status'),
                'notes':row['notes'],'verification':json.loads(row['verification_json']),'score':round(score,6)})
            if len(hits)>=limit:break
    return {'query':query,'namespace':namespace,'mode':mode,'degraded_to_lexical':degraded,'hits':hits,'seconds':round(time.perf_counter()-started,4),
        'usage':'Direct quotes require exact source text. Source-qualified statements are not universal executable rules.'}
