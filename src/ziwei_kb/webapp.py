"""Loopback-only workbench. The embedding model retrieves; Codex remains the answerer."""
import json,mimetypes,re,urllib.parse
from http.server import BaseHTTPRequestHandler
from .local_http import LocalHTTPServer
from .common import ROOT,TOPICS

def dispatch(data):
    result=_dispatch(data)
    if isinstance(result,dict):
        from .presentation import source_view
        evidence=result.get('evidence',result)
        for hit in evidence.get('hits',[]):
            hit['view']=source_view({'id':hit['evidence_id'],'title':hit['title'],'text':hit.get('text',''),'kind':hit.get('kind'),'locator':hit.get('locator'),'notes':hit.get('notes')})
    return result

def _dispatch(data):
    from .engine import chart,context,compare,calendar,liuren,period_context
    from .reports import chart_svg,export_report
    from .retrieval import search,source_record
    from .geography import city_search
    from .library import catalog,browse,personal
    from .cases import lookup
    action=data.get('action');payload=data.get('payload',{})
    if not isinstance(payload,dict):raise ValueError('payload应为对象。')
    question=data.get('question','');topic=data.get('topic','overview')
    if not isinstance(question,str) or len(question)>3000:raise ValueError('问题不超过3000字符。')
    if topic not in TOPICS:raise ValueError('未知主题。')
    limit=data.get('limit',6)
    if type(limit) is not int or not 1<=limit<=20:raise ValueError('limit范围1–20。')
    if isinstance(action,str) and action.startswith('chat-'):
        from . import codex_chat
        if action=='chat-status':return codex_chat.status()
        if action=='chat-list':return codex_chat.list_conversations(data.get('offset',0),limit)
        if action=='chat-get':
            try:return codex_chat.get_conversation(data.get('session_id'))
            except codex_chat.ConversationNotFound:return {'found':False,'message':'之前的研读记录不在当前工作区，可新建研读或选择已有记录。'}
        if action=='chat-send':return codex_chat.submit(question,data.get('scope'),data.get('session_id'),data.get('request_id'))
        if action=='chat-cancel':return codex_chat.cancel(data.get('turn_id'))
        if action=='chat-retry':return codex_chat.retry(data.get('turn_id'))
        if action=='chat-delete':return codex_chat.delete(data.get('session_id'))
        if action=='chat-export':return codex_chat.export(data.get('session_id'))
        raise ValueError('研读操作不支持。')
    if action in ['chart','period']:
        result=chart(payload,action);result['svg']=chart_svg(result,data.get('hide_birth',False),data.get('mode','sanhe'),result.get('period'));return result
    if action=='context':
        result=context(payload,question,topic)
        raw=result.get('archived_case',{}).get('topics',{}).get(topic,{}).get('text')
        if raw:
            from .presentation import markdown_html
            result['archived_case_view']=markdown_html(raw)
        return result
    if action=='period-context':return period_context(payload,question,topic)
    if action=='calendar':return calendar(payload)
    if action=='liuren':return liuren(payload)
    if action=='time-candidates':
        from .engine import time_candidates
        return time_candidates(payload)
    if action=='search':return search(question,limit,data.get('namespace'),data.get('mode','hybrid'),data.get('include_candidates',False))
    if action=='city':return city_search(question)
    if action=='source':
        id=data.get('id','')
        source=source_record(id,20000,2)
        from .presentation import source_view
        source['view']=source_view(source)
        return source
    if action=='case':return lookup(data['key'],topic,100000)
    if action=='compare':return compare(payload,data['second'],question,data.get('relation','love'))
    if action=='twins':
        from .twins import twins
        return twins(payload,limit)
    if action=='report':return export_report(payload,data.get('hide_birth',False),data.get('mode','sanhe'))
    if action=='catalog':return catalog()
    if action=='browse':return browse(data['id'],data.get('offset',0),limit,question)
    if action=='personal':
        if data.get('operation')=='backup':raise ValueError('记录备份请用本地CLI personal backup，备份文件不通过网页公开。')
        return personal(data['operation'],data.get('kind'),data.get('id'),data.get('title'),payload,data.get('offset',0),limit,question)
    raise ValueError('不支持该操作。')

class Handler(BaseHTTPRequestHandler):
    def log_message(self,format,*args):pass
    def allowed_host(self):return self.headers.get('Host') in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']
    def response_headers(self,kind,status,length,extra=()):
        self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(length))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; media-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        for name,value in extra:self.send_header(name,value)
        self.end_headers()
    def send_data(self,body,kind='application/json; charset=utf-8',status=200):
        raw=body if isinstance(body,bytes) else json.dumps(body,ensure_ascii=False).encode('utf-8')
        self.response_headers(kind,status,len(raw))
        if self.command=='HEAD':return
        try:self.wfile.write(raw)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass # Browser reload cancelled this response.
    def send_media(self,path,kind):
        size=path.stat().st_size;start=0;end=size-1;status=200;extra=[('Accept-Ranges','bytes')]
        requested=self.headers.get('Range') if self.command!='HEAD' else None
        if requested:
            match=re.fullmatch(r'bytes=(\d*)-(\d*)',requested.strip())
            try:
                if not match or not any(match.groups()) or not size:raise ValueError()
                first,last=match.groups()
                if first:
                    start=int(first);end=min(int(last),size-1) if last else size-1
                else:
                    suffix=int(last)
                    if not suffix:raise ValueError()
                    start=max(0,size-suffix)
                if start> end or start>=size:raise ValueError()
            except ValueError:
                self.response_headers(kind,416,0,[('Content-Range',f'bytes */{size}'),('Accept-Ranges','bytes')]);return
            status=206;extra.append(('Content-Range',f'bytes {start}-{end}/{size}'))
        remaining=max(0,end-start+1);self.response_headers(kind,status,remaining,extra)
        if self.command=='HEAD':return
        try:
            with path.open('rb') as stream:
                stream.seek(start)
                while remaining:
                    chunk=stream.read(min(65536,remaining))
                    if not chunk:break
                    self.wfile.write(chunk);remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
    def do_HEAD(self):return self.do_GET()
    def do_GET(self):
        if not self.allowed_host():return self.send_data({'error':'Loopback Host required'},status=403)
        route=urllib.parse.urlsplit(self.path).path
        if route=='/favicon.ico':return self.send_data(b'',kind='image/x-icon',status=204)
        if route=='/api/health':return self.send_data({'service':'ziwei-workbench','workspace':str(ROOT)})
        if route=='/api/status':
            from .cli import status
            return self.send_data(status())
        if route.startswith('/exports/'):
            folder=ROOT/'exports';relative=urllib.parse.unquote(route[len('/exports/'):])
        else:
            folder=ROOT/'web/dist';relative=urllib.parse.unquote(route.lstrip('/')) or 'index.html'
        path=(folder/relative).resolve()
        if not path.is_relative_to(folder.resolve()) or not path.is_file():return self.send_data({'error':'Not found'},status=404)
        if path.suffix not in ['.html','.js','.css','.svg','.png','.jpg','.jpeg','.pdf','.ico','.md','.json','.woff2','.mp4','.webm','.vtt']:return self.send_data({'error':'Not served'},status=403)
        mime={'.woff2':'font/woff2','.mp4':'video/mp4','.webm':'video/webm','.vtt':'text/vtt'}.get(path.suffix) or mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        if path.suffix in ['.mp4','.webm']:return self.send_media(path,mime)
        return self.send_data(path.read_bytes(),mime+'; charset=utf-8' if mime.startswith('text/') else mime)
    def do_POST(self):
        if not self.allowed_host():return self.send_data({'error':'Loopback Host required'},status=403)
        origin=self.headers.get('Origin')
        if origin and origin not in [f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}']:return self.send_data({'error':'Cross-origin request rejected'},status=403)
        if self.path!='/api/run':return self.send_data({'error':'Not found'},status=404)
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send_data({'error':'JSON required'},status=415)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=250000:raise ValueError('请求长度超出范围。')
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):raise ValueError('请求应为JSON对象。')
            result=dispatch(data);self.send_data(result)
        except (ValueError,KeyError,TypeError,RuntimeError) as exc:self.send_data({'error':str(exc)},status=400)
        except Exception as exc:self.send_data({'error':str(exc)},status=500)

def serve(port=8765):
    if not 1024<=port<=65535:raise ValueError('port范围1024–65535。')
    if not (ROOT/'web/dist/index.html').exists():raise RuntimeError('本地界面未构建，请在web目录运行npm run build。')
    server=LocalHTTPServer(('127.0.0.1',port),Handler)
    print(f'Ziwei workbench: http://127.0.0.1:{port}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
