"""On-demand localhost-only query encoder, released after idle time."""
import os,json,time,threading,sys
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .common import ROOT,read_json,model_path,embedding_contract
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['HF_HUB_DISABLE_TELEMETRY']='1';os.environ['TOKENIZERS_PARALLELISM']='false'
PORT=8788
last_active=time.monotonic();lock=threading.Lock();model=None
spec=read_json(ROOT/'manifests/embedding-model.json')
contract=embedding_contract(spec)

def encode(queries):
    global model,last_active
    with lock:
        last_active=time.monotonic()
        if model is None:
            import torch
            from sentence_transformers import SentenceTransformer
            torch.set_num_threads(4)
            model=SentenceTransformer(str(model_path(spec)),device='cuda' if torch.cuda.is_available() else 'cpu',local_files_only=True,
                model_kwargs={'dtype':torch.float16} if torch.cuda.is_available() else {})
            model.max_seq_length=spec['max_seq_length']
        lengths=[len(x) for x in model.tokenizer([spec['query_prompt']+q for q in queries],truncation=False)['input_ids']]
        if any(n>spec['max_seq_length'] for n in lengths):raise ValueError('问题超出本地嵌入长度上限，请缩短或拆分问题；未静默截断。')
        vectors=model.encode(queries,prompt=spec['query_prompt'],batch_size=16,normalize_embeddings=True,convert_to_numpy=True)
        last_active=time.monotonic();return vectors.tolist()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def allowed(self):
        hosts=['127.0.0.1:8788','localhost:8788']
        return self.headers.get('Host') in hosts and self.headers.get('Origin') in [None,*['http://'+h for h in hosts]]
    def send(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        if not self.allowed():return self.send({'error':'Loopback origin required'},403)
        if self.path!='/health':return self.send({'error':'not found'},404)
        self.send({'service':'ziwei-query-encoder','workspace':str(ROOT),'revision':spec['revision'],'dimensions':spec['dimensions'],'contract':contract,'model_path':str(model_path(spec)),'loaded':model is not None})
    def do_POST(self):
        if not self.allowed():return self.send({'error':'Loopback origin required'},403)
        if self.path!='/encode':return self.send({'error':'not found'},404)
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send({'error':'JSON required'},415)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=100000:raise ValueError('request size out of bounds')
            body=json.loads(self.rfile.read(length));queries=body['queries']
            if not isinstance(queries,list) or not 1<=len(queries)<=32 or any(not isinstance(q,str) or len(q)>3000 for q in queries):raise ValueError('queries must contain 1–32 short strings')
            self.send({'vectors':encode(queries),'revision':spec['revision'],'contract':contract})
        except Exception as exc:self.send({'error':str(exc)},400)

def main():
    server=ThreadingHTTPServer(('127.0.0.1',PORT),Handler)
    def idle():
        while True:
            time.sleep(15)
            if time.monotonic()-last_active>300 and not lock.locked():server.shutdown();break
    threading.Thread(target=idle,daemon=True).start()
    server.serve_forever(poll_interval=.5);server.server_close()

if __name__=='__main__':main()
