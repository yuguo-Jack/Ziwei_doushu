"""Fetch exact public upstream commits without resetting an existing checkout."""
import argparse,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def git(*args,cwd):
    return subprocess.run(['git',*args],cwd=cwd,check=True,text=True,encoding='utf8',capture_output=True).stdout.strip()

def fetch_repository(spec,root=ROOT):
    target=(root/spec['directory']).resolve()
    if not target.is_relative_to(root.resolve()):raise ValueError('Source checkout must stay inside the project.')
    if target.exists():
        if not (target/'.git').exists():raise RuntimeError(f'{target}: existing directory is not a Git checkout; preserve it and resolve manually.')
        try:actual=git('rev-parse','HEAD',cwd=target)
        except subprocess.CalledProcessError:
            # A task-owned git init may remain after a failed first network fetch.
            if any(p.name!='.git' for p in target.iterdir()) or git('remote','get-url','origin',cwd=target)!=spec['url']:raise
            git('fetch','--depth=1','origin',spec['revision'],cwd=target);git('checkout','--detach',spec['revision'],cwd=target)
            actual=git('rev-parse','HEAD',cwd=target)
        if actual!=spec['revision'] or git('status','--porcelain','--untracked-files=no',cwd=target):
            raise RuntimeError(f'{target}: revision differs or tracked files changed. No reset was performed; expected {spec["revision"]}.')
        return {'name':spec['name'],'revision':actual,'existing':True}
    target.parent.mkdir(parents=True,exist_ok=True);target.mkdir()
    git('init',cwd=target);git('remote','add','origin',spec['url'],cwd=target)
    git('fetch','--depth=1','origin',spec['revision'],cwd=target)
    git('checkout','--detach',spec['revision'],cwd=target)
    assert git('rev-parse','HEAD',cwd=target)==spec['revision']
    return {'name':spec['name'],'revision':spec['revision'],'existing':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--only',choices=['engine','tianji','renji'],nargs='+');args=parser.parse_args()
    lock=json.loads((ROOT/'config/sources.lock.json').read_text(encoding='utf8'))
    try:
        for spec in lock['repositories']:
            if not args.only or spec['name'] in args.only:print(json.dumps(fetch_repository(spec)),flush=True)
    except (RuntimeError,subprocess.CalledProcessError) as error:parser.exit(1,str(error)+'\n')

if __name__=='__main__':main()
