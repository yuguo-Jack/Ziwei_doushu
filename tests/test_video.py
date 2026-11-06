"""Exercise actual HTTP byte ranges used by the in-browser product player."""
import sys,tempfile,threading,unittest,urllib.error,urllib.request
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from ziwei_kb import webapp
from ziwei_kb.local_http import LocalHTTPServer

class VideoHTTPTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'runtime').mkdir(exist_ok=True)
        self.folder=tempfile.TemporaryDirectory(dir=ROOT/'runtime');self.root=Path(self.folder.name)
        dist=self.root/'web/dist';(dist/'media').mkdir(parents=True)
        self.data=bytes(range(256))*4;(dist/'media/film.mp4').write_bytes(self.data)
        (dist/'media/film.vtt').write_text('WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n紫微研习\n',encoding='utf8')
        self.binding=patch.object(webapp,'ROOT',self.root);self.binding.start()
        self.server=LocalHTTPServer(('127.0.0.1',0),webapp.Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
        self.client=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.binding.stop();self.folder.cleanup()
    def get(self,path='/media/film.mp4',headers=None,method='GET'):
        return self.client.open(urllib.request.Request(self.base+path,headers=headers or {},method=method))
    def test_media_head_and_single_ranges(self):
        with self.get(method='HEAD') as response:
            self.assertEqual(response.status,200);self.assertEqual(response.read(),b'')
            self.assertEqual(response.headers['Content-Length'],str(len(self.data)))
            self.assertEqual(response.headers['Content-Type'],'video/mp4');self.assertEqual(response.headers['Accept-Ranges'],'bytes')
        for value,start,end in [('bytes=0-31',0,31),('bytes=1000-',1000,1023),('bytes=-16',1008,1023),('bytes=1000-9999',1000,1023)]:
            with self.subTest(value=value),self.get(headers={'Range':value}) as response:
                self.assertEqual(response.status,206);self.assertEqual(response.read(),self.data[start:end+1])
                self.assertEqual(response.headers['Content-Range'],f'bytes {start}-{end}/1024')
        with self.get() as response:self.assertEqual(response.read(),self.data)
        with self.get('/media/film.vtt') as response:
            self.assertTrue(response.headers['Content-Type'].startswith('text/vtt'))
            self.assertIn('紫微研习',response.read().decode('utf8'))
    def test_invalid_ranges_and_path_escape_remain_rejected(self):
        for value in ['bytes=1024-','bytes=5-3','bytes=-0','bytes=','bytes=0-1,3-4','other=0-1']:
            with self.subTest(value=value),self.assertRaises(urllib.error.HTTPError) as error:self.get(headers={'Range':value})
            self.assertEqual(error.exception.code,416);self.assertEqual(error.exception.headers['Content-Range'],'bytes */1024')
            self.assertEqual(error.exception.read(),b'')
        for path in ['/media/%2e%2e/%2e%2e/%2e%2e/private.mp4','/media/missing.mp4']:
            with self.assertRaises(urllib.error.HTTPError) as error:self.get(path)
            self.assertEqual(error.exception.code,404)
        with self.assertRaises(urllib.error.HTTPError) as error:self.get(headers={'Host':'untrusted.example'})
        self.assertEqual(error.exception.code,403)

if __name__=='__main__':unittest.main()
