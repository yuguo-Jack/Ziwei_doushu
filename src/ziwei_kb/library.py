import json,sqlite3,uuid,datetime
from .common import ROOT,connect,ManagedConnection,normalize

KINDS=['profile','note','bookmark','session','liuren']
def like_pattern(text):return '%'+text.replace('!','!!').replace('%','!%').replace('_','!_')+'%'

def profile_record(reference):
    """Resolve an exact ID first, then an unambiguous exact profile title."""
    if not isinstance(reference,str) or not reference.strip() or len(reference)>200:raise ValueError('命盘ID或名称应为1–200字符。')
    try:record=personal('get',id=reference)
    except ValueError:
        with sqlite3.connect(ROOT/'runtime/personal.sqlite',factory=ManagedConnection) as conn:
            matches=conn.execute("SELECT id FROM items WHERE kind='profile' AND title=? ORDER BY id LIMIT 2",(reference,)).fetchall()
        if not matches:raise ValueError('没有这个命盘ID或名称，请先personal list --kind profile --query查询。')
        if len(matches)>1:raise ValueError('命盘名称重复，请明确使用ID：'+', '.join(r[0] for r in matches))
        record=personal('get',id=matches[0][0])
    if record['kind']!='profile':raise ValueError('该ID不是命盘记录。')
    return record

def catalog():
    with connect() as c:
        rows=[dict(r) for r in c.execute('SELECT s.id,s.kind,s.canonical_url,s.revision,count(u.id) AS units FROM sources s LEFT JOIN source_units u ON u.source_id=s.id GROUP BY s.id ORDER BY s.id')]
        names={'tianji-462faa4':'天纪 · 易经、紫微、风水等课程','renji-fdafae1':'人纪 · 六部课程原文','wikisource-1':'紫微斗数全书 · 卷一','wikisource-2':'紫微斗数全书 · 卷二','wikisource-3':'紫微斗数全书 · 卷三','wikisource-4':'续道藏本紫微斗数 · 历史文献'}
        for row in rows:row['display_name']=names.get(row['id'],row['id'])
        books=[dict(r) for r in c.execute("SELECT json_extract(c.metadata_json,'$.book') AS book,count(DISTINCT u.id) AS units FROM source_units u JOIN chunks c ON c.source_unit_id=u.id WHERE u.source_id='tianji-462faa4' GROUP BY book")]
    return {'sources':rows,'course_books':books,'note':'source IDs support browse; exact excerpts support source. Source text is not automatically an independently verified doctrine.'}

def browse(source_id,offset=0,limit=20,filter_text=''):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=50:raise ValueError('offset>=0，limit范围1–50。')
    if not isinstance(filter_text,str) or len(filter_text)>3000:raise ValueError('筛选文字最多3000字符。')
    with connect() as c:
        source=c.execute('SELECT id,kind,canonical_url,revision,license_json FROM sources WHERE id=?',(source_id,)).fetchone()
        if source is None:raise ValueError('来源不存在，请先查看catalog。')
        title_cache={}
        def normalized_title(value):
            if value not in title_cache:title_cache[value]=normalize(value)
            return title_cache[value]
        c.create_function('normalized_title',1,normalized_title)
        sql='SELECT u.id,u.raw_text,u.locator_json,u.notes,c.title,c.metadata_json FROM source_units u JOIN chunks c ON c.source_unit_id=u.id WHERE u.source_id=?'
        params=[source_id]
        if filter_text:sql+=" AND (normalized_title(c.title) LIKE ? ESCAPE '!' OR u.normalized_text LIKE ? ESCAPE '!')";params.extend([like_pattern(normalize(filter_text))]*2)
        sql+=' GROUP BY u.id ORDER BY min(c.id) LIMIT ? OFFSET ?';params.extend([limit+1,offset])
        rows=c.execute(sql,params).fetchall();more=len(rows)>limit;items=[]
        for row in rows[:limit]:
            meta=json.loads(row['metadata_json']);items.append({'evidence_id':row['id'],'title':row['title'],'text':row['raw_text'],'locator':json.loads(row['locator_json']),'notes':row['notes'],'source_url':meta.get('source_url',source['canonical_url'])})
        return {'source':{**dict(source),'license':json.loads(source['license_json'])},'offset':offset,'has_more':more,'items':items}

def personal(action,kind=None,id=None,title=None,data=None,offset=0,limit=100,query='',output_file=None):
    if action not in ['save','list','get','delete','backup']:raise ValueError('未知记录操作。')
    if kind is not None and kind not in KINDS:raise ValueError('记录kind不支持。')
    if id is not None and (not isinstance(id,str) or not id.strip() or len(id)>200):raise ValueError('记录ID应为1–200字符。')
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=100:raise ValueError('记录offset>=0，limit范围1–100。')
    if not isinstance(query,str) or len(query)>200:raise ValueError('记录查询不超过200字符。')
    folder=ROOT/'runtime';folder.mkdir(exist_ok=True)
    with sqlite3.connect(folder/'personal.sqlite',factory=ManagedConnection) as conn:
        conn.row_factory=sqlite3.Row
        conn.execute('CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY,kind TEXT NOT NULL,title TEXT NOT NULL,data TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)')
        if action=='backup':
            from pathlib import Path
            output=Path(output_file).expanduser().resolve() if output_file else ROOT/'exports'/('personal-backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.sqlite')
            if output.suffix.lower()!='.sqlite':raise ValueError('记录备份文件必须以.sqlite结尾。')
            output.parent.mkdir(parents=True,exist_ok=True)
            try:output.open('xb').close()
            except FileExistsError:raise ValueError('目标文件已存在，备份不会覆盖已有文件。')
            conn.commit()
            with sqlite3.connect(output,factory=ManagedConnection) as destination:
                conn.backup(destination)
                if destination.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('备份完整性校验失败。')
                records=destination.execute('SELECT count(*) FROM items').fetchone()[0]
            return {'backup_path':str(output),'records':records,'consistent_snapshot':True,'includes_private_data':True}
        if action=='save':
            if kind not in KINDS:raise ValueError('记录kind不支持。')
            if not isinstance(title,str) or not 1<=len(title.strip())<=120:raise ValueError('标题应为1–120字符。')
            if not isinstance(data,dict):raise ValueError('记录应为不超过200KB的JSON对象。')
            encoded=json.dumps(data,ensure_ascii=False,allow_nan=False)
            if len(encoded.encode('utf-8'))>200000:raise ValueError('记录应为不超过200KB的JSON对象。')
            now=datetime.datetime.now(datetime.timezone.utc).isoformat();id=id or uuid.uuid4().hex
            old=conn.execute('SELECT kind FROM items WHERE id=?',(id,)).fetchone()
            if old and old['kind']!=kind:raise ValueError('不能通过更新ID变更记录类型。')
            conn.execute('INSERT INTO items VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,data=excluded.data,updated_at=excluded.updated_at',(id,kind,title.strip(),encoded,now,now));conn.commit()
            return {'saved':True,'id':id,'kind':kind,'storage':'local workspace runtime/personal.sqlite'}
        if action=='list':
            conditions=[];params=[]
            if kind:conditions.append('kind=?');params.append(kind)
            if query:conditions.append("title LIKE ? ESCAPE '!'");params.append(like_pattern(query))
            where=' WHERE '+' AND '.join(conditions) if conditions else ''
            total=conn.execute('SELECT count(*) FROM items'+where,params).fetchone()[0]
            sql='SELECT id,kind,title,updated_at FROM items'+where+' ORDER BY updated_at DESC,id DESC LIMIT ? OFFSET ?'
            items=[dict(r) for r in conn.execute(sql,[*params,limit,offset])]
            return {'items':items,'total':total,'offset':offset,'limit':limit,'has_more':offset+len(items)<total,'query':query}
        row=conn.execute('SELECT * FROM items WHERE id=?',(id,)).fetchone()
        if row is None:raise ValueError('本地记录ID不存在。')
        if action=='get':return {**dict(row),'data':json.loads(row['data'])}
        if action=='delete':conn.execute('DELETE FROM items WHERE id=?',(id,));conn.commit();return {'deleted':True,'id':id}
        raise ValueError('未知记录操作。')
