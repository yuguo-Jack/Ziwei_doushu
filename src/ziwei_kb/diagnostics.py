import hashlib,json,os,sqlite3,shutil,sys,subprocess,time
from html.parser import HTMLParser
from pathlib import Path
from .common import ROOT,read_json,model_path,connect,installation

def web_assets():
    folder=ROOT/'web/dist';index=folder/'index.html'
    assert index.is_file(),'网页未构建；重新运行scripts/bootstrap.py。'
    class Assets(HTMLParser):
        def __init__(self):super().__init__();self.paths=[]
        def handle_starttag(self,tag,attrs):
            for key,value in attrs:
                if key in ['src','href'] and value and not value.startswith(('http:','https:','data:','#')):self.paths.append(value)
    parser=Assets();parser.feed(index.read_text(encoding='utf-8'))
    assert any(path.endswith('.js') for path in parser.paths),'网页脚本缺失；用--rebuild重新准备。'
    for relative in [*parser.paths,'/fonts/ziwei-serif.woff2']:
        path=(folder/relative.lstrip('/').split('?')[0]).resolve()
        assert path.is_relative_to(folder.resolve()) and path.is_file(),'网页资源缺失：'+relative+'；用--rebuild重新准备。'
    return {'available':True,'checked_assets':len(parser.paths)+1}

def report_runtime():
    import cairosvg,reportlab,markdown_it
    from .report_formats import report_font
    from reportlab.pdfbase.ttfonts import TTFont
    font=report_font();loaded=TTFont('ZiweiDoctor',str(font),subfontIndex=0)
    assert all(ord(char) in loaded.face.charWidths for char in '紫微研习'),'报告字体缺少中文字符。'
    return {'cairo':'imported','font':str(font)}

def doctor(deep=False,experience=False,progress=None):
    checks=[]
    def check(name,fn):
        if progress:progress(name)
        started=time.monotonic()
        try:value=fn();checks.append({'name':name,'passed':True,'detail':value})
        except Exception as exc:checks.append({'name':name,'passed':False,'detail':str(exc)})
        checks[-1]['seconds']=round(time.monotonic()-started,3)
    spec=read_json(ROOT/'config/embedding-model.json');snapshot=model_path(spec)
    prepared=installation();full=prepared.get('profile','full')=='full';semantic=prepared.get('semantic',True)
    def model():
        if not semantic:return {'installed':False,'required':False,'reason':'Explicit lexical-only installation; semantic model not requested.'}
        actual=read_json(ROOT/'manifests/embedding-model.json')
        fields=['model_id','revision','snapshot_path','dimensions','max_seq_length','normalized','query_prompt']
        assert all(actual.get(key)==spec.get(key) for key in fields),'模型清单与当前固定配置不同；请重新运行安装器。'
        expected=read_json(ROOT/'config/model-checksums.json')
        recorded=read_json(ROOT/'manifests/model-checksums.json')
        def checksum_rows(value):return {r['path'].replace('\\','/'):(r['bytes'],r['sha256']) for r in value['files']}
        assert recorded['revision']==expected['revision'] and checksum_rows(recorded)==checksum_rows(expected),'模型校验清单已过时；请重新运行安装器。'
        assert snapshot.resolve().is_relative_to((ROOT/'models').resolve()),'Model is outside durable workspace models/'
        for row in expected['files']:
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
    check('report_runtime',report_runtime)
    if experience or prepared.get('web'):check('web_build',web_assets)
    else:check('web_build_optional',lambda:{'available':(ROOT/'web/dist/index.html').is_file(),'required_for_cli':False})
    check('model_gitignore',lambda:True if '/models/' in (ROOT/'.gitignore').read_text(encoding='utf-8') else (_ for _ in ()).throw(RuntimeError('models/ is not ignored')))
    if experience:
        def complete_scope():
            assert full and semantic,'完整体验需要--profile full且不加--lexical-only；请重新运行安装器。'
            return {'profile':'full','semantic':True}
        check('experience_scope',complete_scope)
        def live_retrieval():
            from .retrieval import search,source_record
            result=search('三方四正是什么意思',limit=3)
            assert result['mode']=='hybrid' and not result['degraded_to_lexical'],result['degraded_to_lexical'] or '未启用语义检索。'
            assert result['hits'],'检索未返回原文。'
            for hit in result['hits']:
                source=source_record(hit['evidence_id'],100000)
                assert hit['text'] in source['text'],'检索片段与原文不一致。'
            return {'hits':len(result['hits']),'semantic_encoder_called':True,'source_roundtrip':True}
        check('live_semantic_retrieval',live_retrieval)
        def sample_tools():
            from .engine import chart
            from .cases import lookup
            from .twins import twins
            payload=read_json(ROOT/'examples/fictional-first.json');calculated=chart(payload)
            assert calculated['normalized_birth']['hour']==4,'钟表时刻换算异常。'
            archive=lookup(calculated['birth_key'],'all',100000)
            assert archive.get('found') and len(archive['topics'])==13 and all(x['hash_verified'] for x in archive['topics'].values()),'精确案例的十三主题或哈希有误。'
            result=twins(payload,limit=1)
            assert result['indexed_date_branch_rows']==337488,'同盘索引范围不完整。'
            return {'fictional_example':True,'chart':True,'archived_topics':13,'twins':True}
        check('live_chart_case_twins',sample_tools)
        def skill():
            folder=Path(os.environ.get('CODEX_HOME',Path.home()/'.codex'))/'skills/ziwei-knowledge-search'
            binding=read_json(folder/'scripts/workspace.json')
            assert Path(binding['root']).resolve()==ROOT,'技能绑定其它目录；用scripts/install_skill.py --replace切换。'
            for name in ['SKILL.md','scripts/query.py','references/usage.md','references/workflows.md']:
                assert (folder/name).read_bytes()==(ROOT/'skill/ziwei-knowledge-search'/name).read_bytes(),'技能模板已更新；请重跑scripts/install_skill.py。'
            return {'installed':True,'workspace_matches':True,'template_current':True}
        check('installed_skill',skill)
        def codex():
            from .codex_chat import status
            result=status();assert result['ready'],result['message']
            return {**result,'model_answer_tested':False}
        check('codex_connection',codex)
    return {'passed':all(c['passed'] for c in checks),'deep':deep,'experience':experience,'workspace':str(ROOT),'installation':prepared,'checks':checks,'python':sys.executable}
