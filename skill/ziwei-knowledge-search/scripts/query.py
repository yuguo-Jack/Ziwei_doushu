"""Launch the local Ziwei tools from any chat working directory."""
import json,os,runpy,sys
from pathlib import Path
binding=Path(__file__).with_name('workspace.json')
configured=os.environ.get('ZIWEI_KB_ROOT')
if not configured and binding.exists():configured=json.loads(binding.read_text(encoding='utf8'))['root']
root=Path(configured).expanduser().resolve() if configured else Path(__file__).resolve().parents[3]
entry=root/'ziwei.py'
if not entry.is_file():raise SystemExit('紫微知识库入口不存在：'+str(entry)+'；请运行项目 scripts/install_skill.py，或设置 ZIWEI_KB_ROOT 指向项目目录。')
sys.path.insert(0,str(root/'src'));sys.argv[0]=str(entry)
runpy.run_path(str(entry),run_name='__main__')
