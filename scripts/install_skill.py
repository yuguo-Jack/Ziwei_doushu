"""Install the portable skill and bind it to this source checkout."""
import argparse,json,os,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def install(destination=None,replace=False):
    destination=Path(destination) if destination else Path(os.environ.get('CODEX_HOME',Path.home()/'.codex'))/'skills/ziwei-knowledge-search'
    binding=destination/'scripts/workspace.json'
    if binding.exists():
        previous=Path(json.loads(binding.read_text(encoding='utf8'))['root']).resolve()
        if previous!=ROOT and not replace:raise ValueError('Skill is bound to another checkout; use --replace to select this project explicitly.')
    shutil.copytree(ROOT/'skill/ziwei-knowledge-search',destination,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','workspace.json'))
    binding.write_text(json.dumps({'root':str(ROOT),'schema_version':1},ensure_ascii=False,indent=2),encoding='utf8')
    return {'skill_path':str(destination),'workspace':str(ROOT),'next':'Open a new Codex chat and invoke $ziwei-knowledge-search.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--destination',type=Path);p.add_argument('--replace',action='store_true');a=p.parse_args()
    try:print(json.dumps(install(a.destination,a.replace),ensure_ascii=False,indent=2))
    except ValueError as e:p.exit(1,str(e)+'\n')
