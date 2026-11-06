"""Publication/migration contracts; no network, real model or user records."""
import argparse,hashlib,importlib.util,json,os,re,sqlite3,subprocess,sys,tempfile,tomllib,unittest
import threading
from http.server import BaseHTTPRequestHandler
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):(ROOT/'runtime').mkdir(exist_ok=True)

    def test_bundled_snapshots_match_exact_hashes(self):module('bootstrap').verify_assets()

    def test_python_install_recipes_match_package_metadata(self):
        def pins(entries):
            result={}
            for entry in entries:
                self.assertRegex(entry,r'^[A-Za-z0-9_.-]+==[^\s;*,<>=!]+$')
                name,version=entry.split('==');name=re.sub(r'[-_.]+','-',name).lower()
                self.assertNotIn(name,result,'Duplicate dependency: '+name);result[name]=version
            return result
        def requirements(name):
            entries=[]
            for line in (ROOT/name).read_text(encoding='utf8').splitlines():
                line=line.strip()
                if line and not line.startswith('#'):
                    entries.extend(requirements(line[3:].strip()) if line.startswith('-r ') else [line])
            return entries
        project=tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf8'))['project']
        core=project['dependencies'];optional=project['optional-dependencies']
        for recipe,declared in [('core',core),('runtime',core+optional['semantic']),('dev',core+optional['dev'])]:
            with self.subTest(recipe=recipe):
                self.assertEqual(pins(requirements('requirements-'+recipe+'.txt')),pins(declared))

    def test_cpu_install_follows_changed_torch_declaration(self):
        bootstrap=module('bootstrap')
        args=argparse.Namespace(skip_python_deps=False,skip_node_deps=True,lexical_only=False,device='cpu',
                                profile='core',model_directory='fixture',rebuild=False)
        with tempfile.TemporaryDirectory(dir=ROOT/'runtime') as folder:
            root=Path(folder);(root/'config').mkdir()
            (root/'config/model-checksums.json').write_text('{"files":[]}',encoding='utf8')
            metadata=root/'pyproject.toml'
            metadata.write_text('[project.optional-dependencies]\nsemantic = ["torch==9.8.7"]\n',encoding='utf8')
            with patch.object(bootstrap,'ROOT',root):
                steps={step['name']:step for step in bootstrap.plan(args)}
                command=steps['pytorch-cpu']['command'];self.assertIn('torch==9.8.7',command)
                self.assertEqual(command[-2:],['--index-url','https://download.pytorch.org/whl/cpu'])
                args.lexical_only=True;self.assertNotIn('pytorch-cpu',{step['name'] for step in bootstrap.plan(args)})
                metadata.write_text('[project.optional-dependencies]\nsemantic = ["torch>=9.8.7"]\n',encoding='utf8')
                with self.assertRaisesRegex(ValueError,'torch'):bootstrap.cpu_torch_requirement()

    def test_web_runtime_pair_and_lock_match(self):
        package=json.loads((ROOT/'web/package.json').read_text(encoding='utf8'))
        lock=json.loads((ROOT/'web/package-lock.json').read_text(encoding='utf8'));locked=lock['packages']['']
        for field in ['name','version','dependencies','devDependencies']:
            self.assertEqual(package[field],locked[field],field)
        self.assertEqual(package['dependencies']['react'],package['dependencies']['react-dom'])
        for name in ['react','react-dom']:
            self.assertEqual(package['dependencies'][name],lock['packages']['node_modules/'+name]['version'])

    def test_pins_stay_inside_project_and_are_exact(self):
        pins=json.loads((ROOT/'config/sources.lock.json').read_text())['repositories']
        self.assertEqual({x['name'] for x in pins},{'engine','tianji','renji'})
        for pin in pins:
            self.assertRegex(pin['revision'],r'^[a-f0-9]{40}$');self.assertTrue((ROOT/pin['directory']).resolve().is_relative_to(ROOT))

    def test_dry_run_has_correct_profiles_and_no_install_side_effect(self):
        marker=ROOT/'runtime/installation.json';before=marker.read_bytes() if marker.exists() else None
        for profile,extra in [('core',['--lexical-only']),('full',[])]:
            r=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/bootstrap.py'),'--profile',profile,'--skip-python-deps','--dry-run',*extra],capture_output=True,text=True,encoding='utf8',check=True)
            names={x['name'] for x in json.loads(r.stdout)['steps']}
            self.assertEqual('case-shards' in names,profile=='full');self.assertEqual('embedding-index' in names,profile=='full')
        self.assertEqual(marker.read_bytes() if marker.exists() else None,before)

    def test_installed_skill_works_from_unrelated_directory(self):
        runtime=ROOT/'runtime';runtime.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as folder:
            target=Path(folder)/'skills/ziwei-knowledge-search';module('install_skill').install(target)
            env=os.environ.copy();env.pop('ZIWEI_KB_ROOT',None)
            r=subprocess.run([sys.executable,'-X','utf8',str(target/'scripts/query.py'),'--help'],cwd=folder,env=env,capture_output=True,text=True,encoding='utf8')
            self.assertEqual(r.returncode,0,r.stderr);self.assertIn('chat',r.stdout)
            binding=target/'scripts/workspace.json';binding.write_text(json.dumps({'root':str(Path(folder)/'other')}),encoding='utf8')
            with self.assertRaisesRegex(ValueError,'another checkout'):module('install_skill').install(target)

    def test_invalid_explicit_skill_root_is_not_ignored(self):
        env=os.environ.copy();env['ZIWEI_KB_ROOT']=str(ROOT/'runtime/nonexistent-qa-root')
        r=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'skill/ziwei-knowledge-search/scripts/query.py'),'--help'],env=env,capture_output=True,text=True,encoding='utf8')
        self.assertNotEqual(r.returncode,0);self.assertIn('入口不存在',r.stderr)

    def test_console_entry_is_utf8_under_legacy_windows_encoding(self):
        env=os.environ.copy();env['PYTHONIOENCODING']='cp936'
        r=subprocess.run([sys.executable,str(ROOT/'ziwei.py'),'--help'],env=env,capture_output=True)
        self.assertEqual(r.returncode,0);self.assertIn('通过本机',r.stdout.decode('utf8'))

    def test_publication_guard_rejects_credentials_and_local_data(self):
        runtime=ROOT/'runtime';runtime.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as folder:
            root=Path(folder);(root/'good.py').write_text('print(1)',encoding='utf8')
            (root/'secret.txt').write_text('ghp_'+'x'*36,encoding='utf8')
            result=module('check_release').audit(['good.py','secret.txt','runtime/chat.sqlite'],root)
            self.assertFalse(result['passed']);self.assertEqual(len(result['problems']),2)
            self.assertNotIn('x'*36,json.dumps(result))

    def test_core_manifest_keeps_reused_candidate_database_totals(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'runtime') as folder:
            root=Path(folder);(root/'knowledge').mkdir();(root/'manifests').mkdir()
            conn=sqlite3.connect(root/'knowledge/reference-materials.sqlite')
            conn.executescript('CREATE TABLE source_units(id); CREATE TABLE chunks(id); INSERT INTO source_units VALUES(1),(2); INSERT INTO chunks VALUES(1),(2),(3);');conn.close()
            path=root/'manifests/knowledge.json';path.write_text(json.dumps({'source_units':100,'chunks':120}),encoding='utf8')
            module('bootstrap').refresh_candidate_stats(root);value=json.loads(path.read_text())
            self.assertEqual((value['source_units_total'],value['chunks_total']),(102,123))

    def test_memory_and_rebuild_options_reach_candidate_workers(self):
        r=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/bootstrap.py'),'--workers','1','--rebuild','--dry-run'],capture_output=True,text=True,encoding='utf8',check=True)
        steps={x['name']:x for x in json.loads(r.stdout)['steps']}
        for name in ['case-shards','candidate-extraction']:
            command=steps[name]['command'];self.assertEqual(command[command.index('--workers')+1],'1')
        self.assertIn('--rebuild',steps['candidate-extraction']['command'])
        self.assertIn('manifests/embedding-model.json',steps['embedding-model']['outputs'])

    def test_web_readiness_rejects_missing_compiled_asset(self):
        sys.path.insert(0,str(ROOT/'src'))
        from ziwei_kb import diagnostics
        with tempfile.TemporaryDirectory(dir=ROOT/'runtime') as folder:
            root=Path(folder);dist=root/'web/dist';(dist/'fonts').mkdir(parents=True)
            (dist/'index.html').write_text('<script src="/assets/main.js"></script>',encoding='utf8')
            (dist/'fonts/ziwei-serif.woff2').write_bytes(b'fixture')
            with patch.object(diagnostics,'ROOT',root):
                with self.assertRaisesRegex(AssertionError,'main.js'):diagnostics.web_assets()
                (dist/'assets').mkdir();(dist/'assets/main.js').write_text('fixture',encoding='utf8')
                self.assertTrue(diagnostics.web_assets()['available'])

    def test_clean_lexical_doctor_needs_no_fake_model_manifest(self):
        sys.path.insert(0,str(ROOT/'src'))
        from ziwei_kb import diagnostics
        with tempfile.TemporaryDirectory(dir=ROOT/'runtime') as folder:
            root=Path(folder);(root/'config').mkdir();(root/'config/embedding-model.json').write_bytes((ROOT/'config/embedding-model.json').read_bytes())
            with patch.object(diagnostics,'ROOT',root),patch.object(diagnostics,'installation',return_value={'profile':'core','semantic':False,'web':True}):
                result=diagnostics.doctor()
            checks={x['name']:x for x in result['checks']}
            self.assertTrue(checks['workspace_model_regular_files']['passed'])
            self.assertFalse(checks['web_build']['passed']);self.assertFalse(result['passed'])

    def test_old_codex_is_not_reported_as_connected(self):
        sys.path.insert(0,str(ROOT/'src'))
        from ziwei_kb import codex_chat
        old=subprocess.CompletedProcess(['fixture'],0,stdout='old help',stderr='private diagnostic')
        with patch.object(codex_chat,'_auth_cache',None),patch.object(codex_chat,'cli_command',return_value=['fixture']),patch('ziwei_kb.codex_process.subprocess.run',return_value=old):
            result=codex_chat.status()
        self.assertFalse(result['ready']);self.assertIn('版本',result['message']);self.assertNotIn('private',json.dumps(result))

    def test_legacy_model_checksum_path_separator_is_compatible(self):
        sys.path.insert(0,str(ROOT/'src'))
        from ziwei_kb import diagnostics
        with tempfile.TemporaryDirectory(dir=ROOT/'runtime') as folder:
            root=Path(folder);snapshot=root/'models/test';(snapshot/'1_Pooling').mkdir(parents=True)
            data=b'fixture';(snapshot/'1_Pooling/config.json').write_bytes(data)
            spec=json.loads((ROOT/'config/embedding-model.json').read_text(encoding='utf8'));spec['snapshot_path']='models/test'
            row={'path':'1_Pooling/config.json','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
            expected={'revision':spec['revision'],'files':[row]}
            legacy={'revision':spec['revision'],'files':[{**row,'path':'1_Pooling\\config.json'}]}
            for name,value in [('config/embedding-model.json',spec),('manifests/embedding-model.json',spec),('config/model-checksums.json',expected),('manifests/model-checksums.json',legacy)]:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value),encoding='utf8')
            with patch.object(diagnostics,'ROOT',root),patch.object(diagnostics,'model_path',return_value=snapshot),patch.object(diagnostics,'installation',return_value={'profile':'core','semantic':True}):
                result=diagnostics.doctor()
            self.assertTrue(next(x for x in result['checks'] if x['name']=='workspace_model_regular_files')['passed'])

    def test_codex_native_executable_in_hoisted_npm_layout(self):
        sys.path.insert(0,str(ROOT/'src'))
        from ziwei_kb import codex_process
        with tempfile.TemporaryDirectory(dir=ROOT/'runtime') as folder:
            root=Path(folder);wrapper=root/'codex.cmd';wrapper.write_text('fixture',encoding='utf8')
            native=root/'node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe'
            native.parent.mkdir(parents=True);native.write_bytes(b'fixture')
            with patch.dict(os.environ,{'ZIWEI_CODEX_CLI':''}),patch.object(codex_process.shutil,'which',side_effect=lambda name:str(wrapper) if name=='codex.cmd' else None):
                self.assertEqual(codex_process.cli_command(),[str(native)])

    def test_frozen_retrieval_fixture_is_published_unchanged(self):
        path=ROOT/'tests/fixtures/retrieval-questions.json'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),'73270adb2422f9533c968366d39f2339d39906d7a00d19db4234dac4c37838df')
        rows=json.loads(path.read_text(encoding='utf8'))
        self.assertEqual(len(rows),60);self.assertEqual(sum(x['type']=='retrieval' for x in rows),50)

    def test_loopback_port_is_exclusive_and_ignores_external_proxy(self):
        sys.path.insert(0,str(ROOT/'src'))
        from ziwei_kb.local_http import LocalHTTPServer,open_local
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                self.send_response(200);self.end_headers();self.wfile.write(b'local-only')
        server=LocalHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with self.assertRaises(OSError):LocalHTTPServer(server.server_address,Handler)
            with patch.dict(os.environ,{'http_proxy':'http://127.0.0.1:1','HTTP_PROXY':'http://127.0.0.1:1','no_proxy':'','NO_PROXY':''}):
                with open_local('http://127.0.0.1:'+str(server.server_port),timeout=2) as response:self.assertEqual(response.read(),b'local-only')
        finally:server.shutdown();server.server_close();thread.join(timeout=2)

    def test_foreign_encoder_is_rejected_without_spawning_another(self):
        sys.path.insert(0,str(ROOT/'src'))
        from ziwei_kb import retrieval
        spec=json.loads((ROOT/'config/embedding-model.json').read_text(encoding='utf8'))
        with patch.object(retrieval,'service_health',return_value={'workspace':str(ROOT.parent),'contract':'foreign'}),patch.object(retrieval,'read_json',return_value=spec),patch.object(retrieval.subprocess,'Popen') as spawn:
            with self.assertRaisesRegex(RuntimeError,'另一个工作区'):retrieval.query_vectors(['三方四正'])
            spawn.assert_not_called()

    def test_missing_browser_conversation_has_a_recoverable_response(self):
        sys.path.insert(0,str(ROOT/'src'))
        from ziwei_kb import codex_chat,webapp
        with tempfile.TemporaryDirectory(dir=ROOT/'runtime') as folder,patch.object(codex_chat,'DB',Path(folder)/'chat.sqlite'):
            result=webapp.dispatch({'action':'chat-get','session_id':'0'*32})
            self.assertFalse(result['found']);self.assertIn('当前工作区',result['message'])
            with self.assertRaises(codex_chat.ConversationNotFound):codex_chat.get_conversation('0'*32)

if __name__=='__main__':unittest.main(verbosity=2)
