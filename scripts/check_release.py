"""Audit tracked publication files for local state, oversized blobs and credential patterns."""
import argparse,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRIVATE={'runtime','logs','exports','models','indexes','cases','evaluations','repo','node_modules','.cache','.git'}
SECRETS=[re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),re.compile(rb'github_pat_[A-Za-z0-9_]{40,}'),re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]

def audit(paths,root=ROOT):
    problems=[];total=0
    for name in paths:
        path=Path(name);file=root/path
        if path.is_absolute() or '..' in path.parts or any(part in PRIVATE for part in path.parts):problems.append({'file':name,'reason':'private or generated path'});continue
        if path.suffix.lower() in ['.sqlite','.db','.pem','.key'] or path.name in ['auth.json','credentials.json','workspace.json']:
            problems.append({'file':name,'reason':'local data/credential filename'});continue
        if not file.is_file() or file.is_symlink():problems.append({'file':name,'reason':'not a regular publication file'});continue
        data=file.read_bytes();total+=len(data)
        if len(data)>10*1024*1024:problems.append({'file':name,'reason':'blob exceeds 10 MiB; distribute through a download recipe'});continue
        if any(pattern.search(data) for pattern in SECRETS):problems.append({'file':name,'reason':'credential-shaped content; value intentionally hidden'})
        if file.suffix in ['.md','.json','.py','.ts','.js','.jsx','.ps1','.yml','.toml']:
            if re.search(rb'(?:E:[/\\]Wishspace|C:[/\\]Users[/\\]Administrator)',data):problems.append({'file':name,'reason':'machine-specific workspace/user path'})
    return {'passed':not problems,'files':len(paths),'bytes':total,'problems':problems,'scope':'Static publication guard; not an exhaustive secret scanner.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--files-json',type=Path);args=p.parse_args()
    paths=json.loads(args.files_json.read_text(encoding='utf8')) if args.files_json else subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf8').rstrip('\0').split('\0')
    result=audit([x for x in paths if x]);print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
