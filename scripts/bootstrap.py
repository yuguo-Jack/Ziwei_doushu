"""Prepare a source checkout using pinned sources and project-local generated assets."""
import argparse,datetime,hashlib,json,os,shutil,sqlite3,subprocess,sys,tomllib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PROFILES={'core':'原典/课程、排盘、运限、合盘、工具、网页；不含旧版案例/候选库和同盘索引',
          'full':'core全部能力，加1950–2026旧版案例、候选资料和同盘索引'}

def fingerprint(paths):
    digest=hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode());digest.update(path.read_bytes())
    return digest.hexdigest()

def npm_command():
    found=shutil.which('npm')
    if not found:return ['npm']
    path=Path(found)
    if path.suffix.lower() in ['.cmd','.bat','.ps1']:
        entry=path.parent/'node_modules/npm/bin/npm-cli.js'
        if not entry.is_file():raise RuntimeError('找不到npm-cli.js；请使用包含npm的标准Node.js安装。')
        return [shutil.which('node') or 'node',str(entry)]
    return [found]

def cpu_torch_requirement():
    with (ROOT/'pyproject.toml').open('rb') as stream:
        semantic=tomllib.load(stream)['project']['optional-dependencies']['semantic']
    pins=[entry for entry in semantic if entry.startswith('torch==')]
    if len(pins)!=1:raise ValueError('pyproject.toml semantic依赖必须声明唯一的torch精确版本。')
    return pins[0]

def plan(args):
    steps=[]
    def add(name,command,cwd=ROOT,outputs=(),inputs=()):
        steps.append({'name':name,'command':[str(x) for x in command],'cwd':str(cwd),
                      'outputs':list(outputs),'inputs':list(inputs)})
    py=[sys.executable,'-X','utf8']
    if not args.skip_python_deps:
        if not args.lexical_only and args.device=='cpu':
            add('pytorch-cpu',py+['-m','pip','install',cpu_torch_requirement(),'--index-url','https://download.pytorch.org/whl/cpu'])
        add('python-dependencies',py+['-m','pip','install','-r','requirements-core.txt' if args.lexical_only else 'requirements-runtime.txt'])
        add('editable-package',py+['-m','pip','install','--no-deps','-e','.'])
    add('native-report-check',py+['-c',"import sys;sys.path.insert(0,'src');from ziwei_kb.diagnostics import report_runtime;print(report_runtime())"])
    add('pinned-sources',py+['scripts/fetch_sources.py'])
    if not args.skip_node_deps:
        for folder in ['repo','web']:
            add(folder+'-node-dependencies',npm_command()+['ci','--ignore-scripts','--no-audit','--no-fund','--cache',args.npm_cache],ROOT/folder,
                [folder+'/node_modules/.package-lock.json'],[folder+'/package.json',folder+'/package-lock.json'])
    add('extract-engine',['node','--import','./node_modules/tsx/dist/loader.mjs','../tools/extract_engine.ts'],ROOT/'repo',
        ['sources/supplementary/engine-knowledge.json'],['tools/extract_engine.ts','config/sources.lock.json'])
    core_inputs=['tools/build_knowledge.py','tools/import_renji.py','tools/chart_engine.ts','tools/feature_engine.ts','src/ziwei_kb/common.py','design/knowledge-schema.sql','config/sources.lock.json',
                 'sources/supplementary/engine-knowledge.json','sources/tianji-462faa4/data/entries.jsonl','sources/renji/data/entries.jsonl']
    core_inputs += [p.relative_to(ROOT).as_posix() for p in (ROOT/'sources/classics').glob('wikisource-*.json')]
    add('knowledge',py+['tools/build_knowledge.py'],outputs=['knowledge/knowledge.sqlite','knowledge/concepts.json','manifests/knowledge.json'],inputs=core_inputs)
    add('geography',py+['tools/collect_geography.py'],outputs=['knowledge/geography.sqlite','manifests/geography.json'],inputs=['tools/collect_geography.py','config/source-assets.lock.json'])
    if not args.lexical_only:
        model_files=json.loads((ROOT/'config/model-checksums.json').read_text(encoding='utf8'))['files']
        add('embedding-model',py+['tools/download_model.py'],outputs=['manifests/embedding-model.json','manifests/model-checksums.json']+['models/'+args.model_directory+'/'+row['path'] for row in model_files],inputs=['config/embedding-model.json','config/model-checksums.json','tools/download_model.py'])
        add('embedding-index',py+['tools/build_embeddings.py']+(['--rebuild'] if args.rebuild else []),outputs=['indexes/current.json','manifests/embedding-token-lengths.json'],inputs=core_inputs+['tools/build_embeddings.py','config/embedding-model.json','manifests/embedding-model.json'])
    if args.profile=='full':
        years=[row['year'] for row in json.loads((ROOT/'data/MANIFEST.json').read_text(encoding='utf8'))['files']]
        add('case-downloads',py+['tools/download_assets.py'],outputs=['manifests/v4-downloads.json']+[f'sources/v4.0-13d/year-{year}.jsonl.zst' for year in years],inputs=['data/MANIFEST.json','tools/download_assets.py'])
        add('case-shards',py+['tools/build_cases.py','--workers',str(args.workers)],outputs=['manifests/cases.json']+[f'cases/v4.0-13d/year-{year}.sqlite' for year in years],inputs=['tools/build_cases.py','design/case-shard-schema.sql','data/MANIFEST.json'])
        add('candidate-extraction',py+['tools/extract_dataset_references.py','--workers',str(args.workers)]+(['--rebuild'] if args.rebuild else []),outputs=['sources/supplementary/v4-reference-materials.jsonl','manifests/dataset-references.json'],inputs=['tools/extract_dataset_references.py','data/MANIFEST.json'])
        add('candidate-database',py+['tools/import_dataset_references.py'],outputs=['knowledge/reference-materials.sqlite'],inputs=['tools/import_dataset_references.py','design/knowledge-schema.sql','tools/extract_dataset_references.py','src/ziwei_kb/common.py','data/MANIFEST.json','manifests/dataset-references.json'])
        add('twins-features',['node','--import','./node_modules/tsx/dist/loader.mjs','../tools/build_twins.ts'],ROOT/'repo',outputs=['indexes/twins-major-split-v1/features.jsonl','indexes/twins-major-split-v1/build.json'],inputs=['tools/build_twins.ts','config/sources.lock.json'])
        add('twins-index',py+['tools/pack_twins.py'],outputs=['manifests/twins.json','indexes/twins-major-split-v1/features.npy','indexes/twins-major-split-v1/dates.npy'],inputs=['tools/pack_twins.py','tools/verify_twins.ts','tools/build_twins.ts'])
    add('web-build',npm_command()+['run','build'],ROOT/'web',outputs=['web/dist/index.html'],inputs=['web/package.json','web/package-lock.json']+[p.relative_to(ROOT).as_posix() for p in (ROOT/'web/src').rglob('*') if p.is_file()]+[p.relative_to(ROOT).as_posix() for p in (ROOT/'web/public').rglob('*') if p.is_file()]+['web/index.html'])
    return steps

def atomic_json(path,value):
    staged=path.with_suffix('.tmp');staged.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8');staged.replace(path)

def verify_assets():
    for row in json.loads((ROOT/'config/source-assets.lock.json').read_text(encoding='utf8'))['files']:
        path=ROOT/row['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:
            raise RuntimeError('固定来源快照缺失或有改动：'+row['path'])

def refresh_candidate_stats(root=ROOT):
    database=root/'knowledge/reference-materials.sqlite';manifest=root/'manifests/knowledge.json'
    if not database.exists() or not manifest.exists():return
    conn=sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)
    try:
        units=conn.execute('SELECT count(*) FROM source_units').fetchone()[0]
        chunks=conn.execute('SELECT count(*) FROM chunks').fetchone()[0]
    finally:conn.close()
    stats=json.loads(manifest.read_text(encoding='utf8'))
    stats.update({'dataset_reference_units':units,'source_units_total':stats['source_units']+units,'chunks_total':stats['chunks']+chunks,
                  'reference_database':'knowledge/reference-materials.sqlite','candidate_policy':'Explicit candidate-only lookup; not promoted to validated rules.'})
    atomic_json(manifest,stats)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=PROFILES,default='full');parser.add_argument('--lexical-only',action='store_true')
    parser.add_argument('--device',choices=['auto','cpu'],default='auto');parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--skip-python-deps',action='store_true');parser.add_argument('--skip-node-deps',action='store_true')
    parser.add_argument('--install-skill',action='store_true');parser.add_argument('--rebuild',action='store_true');parser.add_argument('--dry-run',action='store_true')
    default_cache=os.environ.get('npm_config_cache') or ('D:/codex/tools/npm-cache' if Path('D:/codex/tools').exists() else str(ROOT/'.cache/npm'))
    parser.add_argument('--npm-cache',default=default_cache);args=parser.parse_args(argv)
    if not 1<=args.workers<=8:parser.error('--workers must be 1..8')
    spec=json.loads((ROOT/'config/embedding-model.json').read_text(encoding='utf8'))
    args.model_directory=Path(spec['snapshot_path']).relative_to('models').as_posix()
    steps=plan(args)
    if args.dry_run:
        print(json.dumps({'profile':args.profile,'semantic':not args.lexical_only,'steps':steps},ensure_ascii=False,indent=2));return 0
    if sys.version_info[:2] not in [(3,12),(3,13)]:parser.error('Use Python 3.12 (verified) or 3.13; see docs/INSTALLATION.zh-CN.md.')
    for binary in ['git','node','npm']:
        if not shutil.which(binary):parser.error('Missing '+binary+' on PATH; install prerequisites first.')
    node_version=subprocess.check_output(['node','-p','process.versions.node'],text=True).strip()
    if int(node_version.split('.')[0])<24:parser.error('Node.js 24+ is required by the engine loader.')
    for folder in ['runtime','logs','exports','knowledge','manifests','indexes','cases/v4.0-13d','sources/supplementary']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
    verify_assets()
    state_path=ROOT/'runtime/build-state.json';state=json.loads(state_path.read_text(encoding='utf8')) if state_path.exists() else {}
    env=os.environ.copy();env['PYTHONUTF8']='1';env['ZIWEI_KB_ROOT']=str(ROOT)
    if args.device=='cpu':env['CUDA_VISIBLE_DEVICES']=''
    print(PROFILES[args.profile],flush=True)
    try:
        for step in steps:
            signature=fingerprint([ROOT/p for p in step['inputs']]) if step['inputs'] else None
            reusable=signature and not args.rebuild and state.get(step['name'])==signature and all((ROOT/p).exists() for p in step['outputs'])
            if reusable:print('已准备：'+step['name'],flush=True);continue
            print('准备：'+step['name'],flush=True)
            subprocess.run(step['command'],cwd=step['cwd'],env=env,check=True)
            if signature:state[step['name']]=signature;atomic_json(state_path,state)
        refresh_candidate_stats()
        marker={'schema_version':1,'profile':args.profile,'semantic':not args.lexical_only,'web':True,'status':'checking','prepared_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        atomic_json(ROOT/'runtime/installation.json',marker)
        subprocess.run([sys.executable,'-X','utf8','ziwei.py','doctor'],cwd=ROOT,env=env,check=True)
        if args.install_skill:subprocess.run([sys.executable,'-X','utf8','scripts/install_skill.py'],cwd=ROOT,env=env,check=True)
        marker['status']='ready';atomic_json(ROOT/'runtime/installation.json',marker)
        print('本地资料与网页准备完成。自动问答另需安装并登录Codex CLI。',flush=True)
        print('完整体验验收：python -X utf8 ziwei.py doctor --experience（不消耗模型回答额度）。',flush=True)
        print('启动网页：python -X utf8 ziwei.py serve --port 8765；直接提问见 README.md。',flush=True);return 0
    except (OSError,RuntimeError,subprocess.CalledProcessError) as error:
        parser.exit(1,'准备未完成：'+str(error)+'\n已完成阶段会保留。修复原因后重新运行同一命令。\n')

if __name__=='__main__':raise SystemExit(main())
