"""Publication/migration contracts; no network, real model or user records."""
import hashlib,importlib.util,json,os,sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'));value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

class ReleaseTests(unittest.TestCase):
    def test_bundled_snapshots_match_exact_hashes(self):module('bootstrap').verify_assets()

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

if __name__=='__main__':unittest.main(verbosity=2)
