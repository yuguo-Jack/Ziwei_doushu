"""Persistent local conversations with fresh evidence and authenticated Codex CLI answers."""
import datetime,json,os,re,sqlite3,subprocess,threading,time,uuid
from pathlib import Path
from .common import ROOT,ManagedConnection,read_json
from .chat_context import validate_scope,prepare_context,answer_prompt,scope_label
from .codex_process import cli_command,run_codex

DB=ROOT/'runtime/chat.sqlite'
BUSY=('queued','preparing','generating')
PHASES={'queued':'等待开始','preparing':'正在核对盘面和原文','generating':'Codex正在组织解读','succeeded':'回答完成','failed':'本次未完成','cancelled':'已停止'}
_slots=threading.BoundedSemaphore(max(1,min(4,read_json(ROOT/'config/codex-chat.json').get('maximum_parallel_answers',2))))
_auth_lock=threading.Lock();_auth_cache=None

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def identifier(value):
    if not isinstance(value,str) or not re.fullmatch('[a-f0-9]{32}',value):raise ValueError('对话或消息不存在。')
    return value

def connection():
    DB.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(DB,timeout=10,factory=ManagedConnection);conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON');conn.execute('PRAGMA journal_mode=WAL')
    conn.executescript('''CREATE TABLE IF NOT EXISTS conversations(
        id TEXT PRIMARY KEY,title TEXT NOT NULL,scope TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS turns(
        id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        request_id TEXT UNIQUE NOT NULL,question TEXT NOT NULL,answer TEXT NOT NULL DEFAULT '',
        memory TEXT NOT NULL DEFAULT '',sources TEXT NOT NULL DEFAULT '[]',citations TEXT NOT NULL DEFAULT '[]',
        follow_ups TEXT NOT NULL DEFAULT '[]',effective_scope TEXT NOT NULL,status TEXT NOT NULL,
        error TEXT NOT NULL DEFAULT '',worker_pid INTEGER,metadata TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
      CREATE UNIQUE INDEX IF NOT EXISTS one_active_turn ON turns(conversation_id) WHERE status IN ('queued','preparing','generating');
      CREATE INDEX IF NOT EXISTS turn_order ON turns(conversation_id,created_at,id);''')
    if 'execution_id' not in {row[1] for row in conn.execute('PRAGMA table_info(turns)')}:
        try:conn.execute("ALTER TABLE turns ADD COLUMN execution_id TEXT NOT NULL DEFAULT ''")
        except sqlite3.OperationalError as error:
            if 'duplicate column' not in str(error):raise
    return conn

def process_alive(pid):
    if not pid:return False
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes as w
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];kernel.OpenProcess.restype=w.HANDLE
        kernel.GetExitCodeProcess.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)];kernel.CloseHandle.argtypes=[w.HANDLE]
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:return False
        try:
            code=w.DWORD();return bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
        finally:kernel.CloseHandle(handle)
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False
    except PermissionError:return True

def recover_orphans(conn):
    rows=conn.execute("SELECT id,worker_pid,execution_id FROM turns WHERE status IN ('queued','preparing','generating')").fetchall()
    for row in rows:
        if not process_alive(row['worker_pid']):conn.execute("UPDATE turns SET status='failed',error=?,updated_at=? WHERE id=? AND execution_id=? AND worker_pid IS ? AND status IN ('queued','preparing','generating')",('服务已重启，这次回答没有完成；问题已保留，可以重试。',now(),row['id'],row['execution_id'],row['worker_pid']))
    conn.commit()

def status():
    global _auth_cache
    with _auth_lock:
        if _auth_cache and _auth_cache[1]['ready'] and time.monotonic()-_auth_cache[0]<30:return dict(_auth_cache[1])
        try:
            command=cli_command();result=subprocess.run(command+['login','status'],capture_output=True,text=True,encoding='utf-8',timeout=8,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            ready=result.returncode==0
            response={'available':True,'ready':ready,'message':'已连接当前登录的Codex' if ready else '请先在本机完成Codex登录，再重试。'}
        except (OSError,RuntimeError,subprocess.TimeoutExpired):response={'available':False,'ready':False,'message':'尚未连接Codex，请检查本机安装和登录。'}
        _auth_cache=(time.monotonic(),response);return dict(response)

def list_conversations(offset=0,limit=20):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=50:raise ValueError('对话分页范围无效。')
    with connection() as conn:
        recover_orphans(conn)
        rows=conn.execute('SELECT * FROM conversations ORDER BY updated_at DESC,id LIMIT ? OFFSET ?',(limit+1,offset)).fetchall()
        return {'items':[{'id':r['id'],'title':r['title'],'scope_label':scope_label(json.loads(r['scope'])),'updated_at':r['updated_at']} for r in rows[:limit]],'has_more':len(rows)>limit,'offset':offset}

def answer_html(text):
    from markdown_it import MarkdownIt
    parser=MarkdownIt('commonmark',{'html':False,'breaks':True}).enable('table').disable('image')
    original=parser.renderer.rules.get('link_open')
    def link(tokens,idx,options,env):
        tokens[idx].attrSet('target','_blank');tokens[idx].attrSet('rel','noreferrer noopener')
        return original(tokens,idx,options,env) if original else parser.renderer.renderToken(tokens,idx,options,env)
    parser.renderer.rules['link_open']=link
    return parser.render(text)

def get_conversation(session_id):
    identifier(session_id)
    with connection() as conn:
        recover_orphans(conn)
        session=conn.execute('SELECT * FROM conversations WHERE id=?',(session_id,)).fetchone()
        if not session:raise ValueError('这段对话不存在，可能已被删除。')
        rows=conn.execute('SELECT * FROM turns WHERE conversation_id=? ORDER BY rowid',(session_id,)).fetchall()
    messages=[]
    for row in rows:
        sources=json.loads(row['sources']);citations=json.loads(row['citations']);scope=json.loads(row['effective_scope'])
        messages.append({'id':row['id'],'request_id':row['request_id'],'question':row['question'],'answer':row['answer'],'answer_html':answer_html(row['answer']),
          'status':row['status'],'phase':PHASES[row['status']],'error':row['error'],'scope_label':scope_label(scope),
          'sources':[{k:s.get(k,'') for k in ['number','evidence_id','title','category','location','source_url']} for s in sources if s['number'] in citations],
          'follow_ups':json.loads(row['follow_ups']),'created_at':row['created_at']})
    return {'id':session['id'],'title':session['title'],'scope':json.loads(session['scope']),'current_scope':json.loads(rows[-1]['effective_scope'] if rows else session['scope']),'scope_label':scope_label(json.loads(session['scope'])),'messages':messages,'updated_at':session['updated_at']}

def submit(question,scope=None,session_id=None,request_id=None):
    if not isinstance(question,str) or not question.strip() or len(question)>3000:raise ValueError('请填写问题，最多3000字。')
    question=question.strip();request_id=identifier(request_id) if request_id else uuid.uuid4().hex
    if session_id:identifier(session_id)
    with connection() as conn:
        recover_orphans(conn);conn.execute('BEGIN IMMEDIATE')
        duplicate=conn.execute('SELECT id,conversation_id,question FROM turns WHERE request_id=?',(request_id,)).fetchone()
        if duplicate:
            stored_scope=json.loads(conn.execute('SELECT scope FROM conversations WHERE id=?',(duplicate['conversation_id'],)).fetchone()[0])
            if question!=duplicate['question'] or (session_id and session_id!=duplicate['conversation_id']) or (scope is not None and validate_scope(scope)!=stored_scope):raise ValueError('这次重试与原问题不一致，请重新发送。')
            return {'session_id':duplicate['conversation_id'],'turn_id':duplicate['id']}
        if conn.execute("SELECT count(*) FROM turns WHERE status IN ('queued','preparing','generating')").fetchone()[0]>=8:raise ValueError('当前研读较多，请等待已有回答完成。')
        stamp=now()
        if session_id:
            session=conn.execute('SELECT * FROM conversations WHERE id=?',(session_id,)).fetchone()
            if not session:raise ValueError('这段对话不存在，请新建研读。')
            stored=json.loads(session['scope'])
            if scope is not None and validate_scope(scope)!=stored:raise ValueError('这段对话的研读对象已固定；更换命盘请新建研读。')
            scope=stored
            previous=conn.execute('SELECT effective_scope FROM turns WHERE conversation_id=? ORDER BY rowid DESC LIMIT 1',(session_id,)).fetchone()
            initial_scope=json.loads(previous['effective_scope']) if previous else scope
            if conn.execute('SELECT count(*) FROM turns WHERE conversation_id=?',(session_id,)).fetchone()[0]>=200:raise ValueError('这段对话已较长，请导出后新建研读。')
        else:
            scope=validate_scope(scope);session_id=uuid.uuid4().hex
            initial_scope=scope
            conn.execute('INSERT INTO conversations VALUES(?,?,?,?,?)',(session_id,question[:45],json.dumps(scope,ensure_ascii=False),stamp,stamp))
        turn_id=uuid.uuid4().hex;execution_id=uuid.uuid4().hex
        try:conn.execute('INSERT INTO turns(id,conversation_id,request_id,question,effective_scope,status,worker_pid,created_at,updated_at,execution_id) VALUES(?,?,?,?,?,?,?,?,?,?)',(turn_id,session_id,request_id,question,json.dumps(initial_scope,ensure_ascii=False),'queued',os.getpid(),stamp,stamp,execution_id))
        except sqlite3.IntegrityError:raise ValueError('上一条回答仍在进行，请先等待或停止它。')
        conn.execute('UPDATE conversations SET updated_at=? WHERE id=?',(stamp,session_id));conn.commit()
    threading.Thread(target=_answer,args=(turn_id,execution_id),daemon=True).start()
    return {'session_id':session_id,'turn_id':turn_id}

def _active(turn_id,execution_id):
    with connection() as conn:row=conn.execute('SELECT status FROM turns WHERE id=? AND execution_id=?',(turn_id,execution_id)).fetchone()
    return bool(row and row['status'] in BUSY)

def _update(turn_id,execution_id,**values):
    values['updated_at']=now()
    with connection() as conn:
        conn.execute('UPDATE turns SET '+','.join(key+'=?' for key in values)+' WHERE id=? AND execution_id=? AND status IN (\'queued\',\'preparing\',\'generating\')',(*values.values(),turn_id,execution_id));conn.commit()

def _answer(turn_id,execution_id):
    try:
        while not _slots.acquire(timeout=.2):
            if not _active(turn_id,execution_id):return
        try:
            if not _active(turn_id,execution_id):return
            _update(turn_id,execution_id,status='preparing')
            with connection() as conn:
                turn=dict(conn.execute('SELECT * FROM turns WHERE id=?',(turn_id,)).fetchone())
                session=dict(conn.execute('SELECT * FROM conversations WHERE id=?',(turn['conversation_id'],)).fetchone())
                history=[dict(r) for r in conn.execute('SELECT * FROM turns WHERE conversation_id=? AND rowid<(SELECT rowid FROM turns WHERE id=?) ORDER BY rowid',(turn['conversation_id'],turn_id))]
            for row in history:
                row['effective_scope']=json.loads(row['effective_scope']);row['sources']=json.loads(row['sources'])
            settings=read_json(ROOT/'config/codex-chat.json');settings['timeout_seconds']=max(30,min(600,int(settings.get('timeout_seconds',300))))
            history=history[-max(1,min(20,int(settings.get('history_turns',10)))):]
            prepared=prepare_context(turn['question'],json.loads(session['scope']),history)
            _update(turn_id,execution_id,effective_scope=json.dumps(prepared['scope'],ensure_ascii=False),sources=json.dumps(prepared['sources'],ensure_ascii=False))
            if not _active(turn_id,execution_id):return
            _update(turn_id,execution_id,status='generating')
            value,metadata=run_codex(answer_prompt(turn['question'],prepared,history),settings,lambda:not _active(turn_id,execution_id))
            if not isinstance(value,dict) or not isinstance(value.get('answer'),str) or not 1<=len(value['answer'].strip())<=50000:raise RuntimeError('这次未取得完整的可读回答，请重试。')
            value['answer']=value['answer'].strip()
            citations=value.get('citations',[]);available={s['number'] for s in prepared['sources']}
            if not isinstance(citations,list) or any(type(number) is not int or number not in available for number in citations):raise RuntimeError('这次回答的出处未能核对，请重试。')
            mentioned={int(number) for number in re.findall(r'\[(\d{1,3})\]',value['answer'])}
            if not mentioned<=set(citations):raise RuntimeError('这次回答的引文标号未能核对，请重试。')
            suggestions=value.get('follow_ups',[])
            if not isinstance(suggestions,list) or any(not isinstance(item,str) for item in suggestions):suggestions=[]
            suggestions=list(dict.fromkeys(item.strip()[:180] for item in suggestions if item.strip()))[:3]
            memory=value.get('memory','');memory=memory[:4000] if isinstance(memory,str) else ''
            _update(turn_id,execution_id,status='succeeded',answer=value['answer'],citations=json.dumps(list(dict.fromkeys(citations))),follow_ups=json.dumps(suggestions,ensure_ascii=False),memory=memory,metadata=json.dumps(metadata))
            with connection() as conn:conn.execute('UPDATE conversations SET updated_at=? WHERE id=?',(now(),turn['conversation_id']));conn.commit()
        finally:_slots.release()
    except (ValueError,RuntimeError,TimeoutError,InterruptedError) as error:_update(turn_id,execution_id,status='failed',error=str(error))
    except Exception:_update(turn_id,execution_id,status='failed',error='本次研读未能完成，问题已保留，请重试。')

def cancel(turn_id):
    identifier(turn_id)
    with connection() as conn:
        row=conn.execute('SELECT conversation_id FROM turns WHERE id=?',(turn_id,)).fetchone()
        if not row:raise ValueError('消息不存在。')
        changed=conn.execute("UPDATE turns SET status='cancelled',error='本次研读已停止。',updated_at=? WHERE id=? AND status IN ('queued','preparing','generating')",(now(),turn_id)).rowcount;conn.commit()
    return {'session_id':row['conversation_id'],'cancelled':bool(changed)}

def retry(turn_id):
    identifier(turn_id)
    with connection() as conn:
        recover_orphans(conn);conn.execute('BEGIN IMMEDIATE')
        row=conn.execute('SELECT * FROM turns WHERE id=?',(turn_id,)).fetchone()
        if not row:raise ValueError('消息不存在。')
        latest=conn.execute('SELECT id FROM turns WHERE conversation_id=? ORDER BY rowid DESC LIMIT 1',(row['conversation_id'],)).fetchone()
        if latest['id']!=turn_id or row['status'] not in ['failed','cancelled']:raise ValueError('请在当前对话继续提问，或等待已有回答完成。')
        if conn.execute("SELECT count(*) FROM turns WHERE status IN ('queued','preparing','generating')").fetchone()[0]>=8:raise ValueError('当前研读较多，请等待已有回答完成。')
        execution_id=uuid.uuid4().hex
        try:conn.execute("UPDATE turns SET status='queued',error='',worker_pid=?,updated_at=?,execution_id=? WHERE id=? AND status IN ('failed','cancelled')",(os.getpid(),now(),execution_id,turn_id));conn.commit()
        except sqlite3.IntegrityError:raise ValueError('当前仍有回答进行中。')
    threading.Thread(target=_answer,args=(turn_id,execution_id),daemon=True).start();return {'session_id':row['conversation_id'],'turn_id':turn_id}

def delete(session_id):
    identifier(session_id)
    with connection() as conn:
        conn.execute('DELETE FROM conversations WHERE id=?',(session_id,));conn.commit()
    return {'deleted':True}

def export(session_id):
    session=get_conversation(session_id);folder=ROOT/'exports';folder.mkdir(exist_ok=True)
    lines=['# '+session['title'],session['scope_label']]
    for turn in session['messages']:
        lines+=['\n## 提问',turn['question'],'\n## 研读',turn['answer'] or turn['error'] or turn['phase']]
        for source in turn['sources']:
            label=f'[{source["number"]}] {source["title"]}'+(' · '+source['location'] if source['location'] else '')
            url=source['source_url'];lines.append(label+(' — '+url if url.startswith('https://') else ''))
    name='conversation-'+session_id+'.md';(folder/name).write_text('\n\n'.join(lines),encoding='utf-8')
    return {'path':str(folder/name),'url':'/exports/'+name,'file_name':name}

def backup():
    folder=ROOT/'exports';folder.mkdir(exist_ok=True)
    path=folder/('chat-backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.sqlite')
    with connection() as source,sqlite3.connect(path,factory=ManagedConnection) as destination:source.backup(destination)
    return {'path':str(path),'scope':'仅问答研读的会话、引文与所选资料；不包含个人记录、全部知识库和模型。'}

def wait_for_turn(session_id,turn_id,timeout=720):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        session=get_conversation(session_id);turn=next((t for t in session['messages'] if t['id']==turn_id),None)
        if turn and turn['status'] not in BUSY:return {'session':session,'turn':turn,'passed':turn['status']=='succeeded'}
        time.sleep(.3)
    cancel(turn_id);raise TimeoutError('等待研读超时，已停止本次请求。')
