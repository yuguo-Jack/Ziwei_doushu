import hashlib,json,os,re,sqlite3,unicodedata
from pathlib import Path
from functools import lru_cache
from opencc import OpenCC

ROOT=Path(os.environ.get('ZIWEI_KB_ROOT') or Path(__file__).resolve().parents[2]).expanduser().resolve()
DB=ROOT/'knowledge/knowledge.sqlite'
TOPICS={'overview':'命格总览','personality':'性格','love':'感情婚姻','career':'事业职业','wealth':'财富财运','health':'健康疾厄','family':'兄弟合伙','children':'子女','move':'迁移','friends':'人际交友','home':'田宅','spirit':'福德','parents':'父母'}
CC=OpenCC('t2s')
BASE_TERMS=['三方四正','对宫','三合','夹宫','排盘','命盘','四化','化禄','化权','化科','化忌','大限','流年','流月','流日','真太阳时','均时差','夏令时','晚子时','闰月','庙旺','落陷','禄存','擎羊','陀罗','地空','地劫','文昌','文曲','左辅','右弼','天魁','天钺','火星','铃星','杀破狼','机月同梁']
STOP={'什么','怎么','如何','一下','解释','请问','为什么','有没有','根据','资料','这个','那个','哪些','可以','需要','有关','对应','中的','来说','我们','是否','以及'}

def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def installation():
    path=ROOT/'runtime/installation.json'
    return read_json(path) if path.exists() else {'profile':'full','semantic':True,'status':'existing-workspace'}
def write_json(path,obj):Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def model_path(spec):
    path=Path(spec['snapshot_path'])
    return path if path.is_absolute() else ROOT/path

def embedding_contract(spec):
    fields={k:spec[k] for k in ['model_id','revision','dimensions','max_seq_length','normalized','query_prompt']}
    fields['model_path']=str(model_path(spec).resolve())
    return hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()
def sha(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def normalize(text):return re.sub(r'\s+',' ',CC.convert(unicodedata.normalize('NFKC',text))).strip()

@lru_cache(maxsize=1)
def terms_dictionary():
    file=ROOT/'knowledge/concepts.json'
    rows=read_json(file) if file.exists() else []
    return sorted(set(BASE_TERMS+[normalize(x) for row in rows for x in [row['name'],*row.get('aliases',[])] if len(x)>1]),key=len,reverse=True)

def tokenize(text,query=False):
    text=normalize(text);words=[]
    for term in terms_dictionary():
        if term in text:words.append(term)
    for chunk in re.findall(r'[\u3400-\u9fff]+',text):
        words.extend(chunk[i:i+2] for i in range(len(chunk)-1) if chunk[i:i+2] not in STOP)
    words.extend(x.lower() for x in re.findall(r'[A-Za-z][A-Za-z0-9_]+',text))
    if query:return list(dict.fromkeys(words))[:50]
    return ' '.join(words)

class ManagedConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()

def connect(path=None):
    path=Path(path) if path else DB
    if not path.exists():raise RuntimeError('资料库文件尚未生成：'+str(path))
    conn=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,factory=ManagedConnection)
    conn.row_factory=sqlite3.Row
    return conn

def infer_namespace(query):
    if any(x in query for x in ['续道藏','續道藏','历史紫微']):return 'historical_ziwei'
    if any(x in query for x in ['易经','易經','爻','乾卦','坤卦','六十四卦','序卦']):return 'yijing'
    if any(x in query for x in ['风水','風水','阳宅','陽宅','堪舆','堪輿']):return 'fengshui'
    if any(x in query for x in ['铁板神数','鐵板神數']):return 'tieban'
    return 'ziwei'
