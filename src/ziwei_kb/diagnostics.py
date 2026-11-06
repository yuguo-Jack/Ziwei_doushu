import hashlib,json,sqlite3,shutil,sys,importlib.metadata,subprocess
from .common import ROOT,read_json,model_path,connect,installation

def doctor(deep=False):
    checks=[]
    def check(name,fn):
        try:value=fn();checks.append({'name':name,'passed':True,'detail':value})
        except Exception as exc:checks.append({'name':name,'passed':False,'detail':str(exc)})
    spec=read_json(ROOT/'manifests/embedding-model.json');snapshot=model_path(spec)
    prepared=installation();full=prepared.get('profile','full')=='full';semantic=prepared.get('semantic',True)
    def model():
        if not semantic:return {'installed':False,'required':False,'reason':'Explicit lexical-only installation; semantic model not requested.'}
        assert snapshot.resolve().is_relative_to((ROOT/'models').resolve()),'Model is outside durable workspace models/'
        for row in read_json(ROOT/'manifests/model-checksums.json')['files']:
            p=snapshot/row['path'];assert p.is_file() and not p.is_symlink() and p.stat().st_size==row['bytes'],str(p)
            if deep:assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],str(p)
        return str(snapshot)
    check('workspace_model_regular_files',model)
    for file in ['knowledge/knowledge.sqlite','knowledge/reference-materials.sqlite','knowledge/geography.sqlite']:
        def database(file=file):
            path=ROOT/file;assert path.is_file(),str(path)
            with connect(path) as c:
                assert c.execute('PRAGMA integrity_check' if deep else 'PRAGMA quick_check').fetchone()[0]=='ok'
            return path.stat().st_size
        if file=='knowledge/reference-materials.sqlite' and not full and not (ROOT/file).exists():
            check(file,lambda:{'installed':False,'required':False,'enable':'python -X utf8 scripts/bootstrap.py --profile full'})
        else:check(file,database)
    def personal_records():
        path=ROOT/'runtime/personal.sqlite'
        if not path.exists():return {'available':False,'required_before_first_save':False}
        with connect(path) as c:
            assert c.execute('PRAGMA integrity_check' if deep else 'PRAGMA quick_check').fetchone()[0]=='ok','Personal database integrity check failed'
            columns={r['name'] for r in c.execute('PRAGMA table_info(items)')}
            assert {'id','kind','title','data','created_at','updated_at'}<=columns,'Personal records schema is incomplete'
            assert c.execute('SELECT count(*) FROM items WHERE NOT json_valid(data)').fetchone()[0]==0,'Personal record contains invalid JSON; preserve the original before repair'
        return {'available':True,'schema_and_json_checked':True}
    check('personal_records_optional',personal_records)
    def cases():
        if not full and not (ROOT/'manifests/cases.json').exists():return {'installed':False,'required':False,'enable':'python -X utf8 scripts/bootstrap.py --profile full'}
        info=read_json(ROOT/'manifests/cases.json');assert info['complete'] and len(info['files'])==77
        for row in info['files']:assert (ROOT/row['path']).stat().st_size==row['sqlite_bytes'],row['path']
        return {'years':77,'charts':info['charts'],'readings':info['readings']}
    check('case_coverage',cases)
    def index():
        if not semantic:return {'installed':False,'required':False,'retrieval':'lexical'}
        from .retrieval import dense_index
        rows,vectors=dense_index()
        if deep:
            import numpy as np
            current=read_json(ROOT/'indexes/current.json');manifest_path=ROOT/current['manifest_path'];manifest=read_json(manifest_path)
            vector_path=manifest_path.parent/manifest['vector_file']
            assert hashlib.sha256(vector_path.read_bytes()).hexdigest()==manifest['vectors_sha256'],'Vector file checksum mismatch'
            assert vectors.dtype==np.float32 and np.isfinite(vectors).all(),'Vector values are invalid'
            assert np.allclose(np.linalg.norm(vectors,axis=1),1,atol=.003),'Vector normalization mismatch'
        return {'rows':len(rows),'dimensions':vectors.shape[1],'row_map_checked':True,'vector_sha_checked':deep}
    check('vector_source_contract',index)
    def token_budget():
        if not semantic:return {'installed':False,'required':False,'reason':'No embedding index requested.'}
        audit=read_json(ROOT/'manifests/embedding-token-lengths.json')
        assert not audit['oversized_documents'] and audit['max_document_tokens']<=spec['max_seq_length']
        assert audit['configured_max_seq_length']==spec['max_seq_length']
        return audit
    check('embedding_document_token_budget',token_budget)
    def auxiliary():
        geography=read_json(ROOT/'manifests/geography.json');twins_path=ROOT/'manifests/twins.json'
        twins=read_json(twins_path) if twins_path.exists() else None
        if full:assert twins,'Full installation needs a twins index.'
        rows=geography['sources']+(twins['files']+[twins['runtime_verifier']] if twins else [])
        for row in rows:
            path=ROOT/row['path'];assert path.stat().st_size==row['bytes'],row['path']
            if deep:assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],row['path']
        return {'geography_cities':geography['cities'],'twins_rows':twins['rows'] if twins else 0,'twins_installed':bool(twins),'checked_files':len(rows)}
    check('geography_and_twins_assets',auxiliary)
    def node_runtime():
        node=shutil.which('node');assert node,'Node not on PATH'
        result=subprocess.run([node,'--input-type=module','-e',"import {registerHooks} from 'node:module'; if(typeof registerHooks!=='function')process.exit(2);process.stdout.write(process.version)"],capture_output=True,text=True,encoding='utf-8',timeout=15)
        assert result.returncode==0,'Node requires node:module.registerHooks; '+result.stderr[-500:]
        return {'path':node,'version':result.stdout}
    check('node_runtime',node_runtime)
    def chart_dependencies():
        for name in ['tsx/dist/loader.mjs','iztro/package.json','lunar-javascript/package.json']:assert (ROOT/'repo/node_modules'/name).is_file(),name
        return {name:read_json(ROOT/'repo/node_modules'/name/'package.json')['version'] for name in ['iztro','lunar-javascript']}
    check('chart_dependencies',chart_dependencies)
    def reports():
        import cairosvg,reportlab,markdown_it
        from .report_formats import report_font
        font=report_font()
        return {'cairo':cairosvg.cairo_version_string() if hasattr(cairosvg,'cairo_version_string') else 'imported','font':str(font)}
    check('report_runtime',reports)
    check('web_build_optional',lambda:{'available':(ROOT/'web/dist/index.html').is_file(),'required_for_cli':False})
    check('model_gitignore',lambda:True if '/models/' in (ROOT/'.gitignore').read_text(encoding='utf-8') else (_ for _ in ()).throw(RuntimeError('models/ is not ignored')))
    return {'passed':all(c['passed'] for c in checks),'deep':deep,'workspace':str(ROOT),'installation':prepared,'checks':checks,'python':sys.executable}
