import datetime,hashlib,json,re,sqlite3
import zstandard
from .common import ROOT,TOPICS,connect

def lookup(key,topic='overview',max_chars=5000,offset=0):
    if not isinstance(key,str):raise ValueError('出生键必须是字符串。')
    if type(max_chars) is not int or not 1<=max_chars<=100000 or type(offset) is not int or offset<0:raise ValueError('max_chars范围1–100000，offset必须是非负整数。')
    match=re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})-(\d|1[01])-(male|female)',key)
    if not match:raise ValueError('出生键格式为 YYYY-MM-DD-时辰序号0至11-male/female。')
    y,m,d,h,g=match.groups();year=int(y);datetime.date(year,int(m),int(d))
    if topic not in TOPICS and topic!='all':raise ValueError('未知解读主题。')
    if not 1950<=year<=2026:return {'found':False,'birth_key':key,'reason':'v4数据只覆盖公历1950–2026；不以相近生日代替。'}
    path=ROOT/f'cases/v4.0-13d/year-{year}.sqlite'
    if not path.exists():return {'found':False,'birth_key':key,'reason':'该年份分片尚不可用。'}
    with connect(path) as conn:
        row=conn.execute('SELECT * FROM cases WHERE birth_key=?',(key,)).fetchone()
        if row is None:return {'found':False,'birth_key':key,'reason':'精确键不存在。'}
        profile=dict(conn.execute('SELECT * FROM dataset_profile').fetchone());profile['profile']=json.loads(profile.pop('profile_json'))
        result={'found':True,'birth_key':key,'dataset':'v4.0-13d','content_version':profile['content_version'],'profile':profile['profile'],
            'archive_sha256':profile['source_archive_sha256'],'metadata':json.loads(row['metadata_json']),'topics':{},
            'source_url':'https://github.com/Renhuai123/ziwei-doushu/releases/tag/v4.0-13d',
            'source_archive':f'sources/v4.0-13d/year-{year}.jsonl.zst','license':'CC-BY-4.0 with attribution; embedded Ni Haixia quotations retain separate rights',
            'applicability':'Exact archived natal reading only; current engine, brightness and other policies may differ.'}
        decoder=zstandard.ZstdDecompressor()
        for name in TOPICS if topic=='all' else [topic]:
            r=conn.execute('SELECT t.* FROM case_topics c JOIN topic_texts t ON t.id=c.text_id WHERE c.case_id=? AND c.topic=?',(row['id'],name)).fetchone()
            layout=json.loads(decoder.decompress(r['layout_zstd']));ids=list(dict.fromkeys(layout));q=','.join('?' for _ in ids)
            blocks=dict(conn.execute(f'SELECT id,exact_text FROM text_blocks WHERE id IN ({q})',ids).fetchall());text=''.join(blocks[i] for i in layout)
            if hashlib.sha256(text.encode()).digest()!=r['sha256']:raise RuntimeError('案例还原校验失败。')
            piece=text[offset:offset+max_chars]
            result['topics'][name]={'evidence_id':f'CASE:v4.0-13d:{key}:{name}','label':TOPICS[name],'text':piece,'total_chars':len(text),
                'offset':offset,'truncated':offset+len(piece)<len(text),'sha256':r['sha256'].hex(),'hash_verified':True}
        return result
