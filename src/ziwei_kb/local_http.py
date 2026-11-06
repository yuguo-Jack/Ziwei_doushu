"""Loopback services must own their port and bypass external HTTP proxies."""
import os,socket,urllib.request
from http.server import ThreadingHTTPServer

class LocalHTTPServer(ThreadingHTTPServer):
    allow_reuse_address=os.name!='nt'

    def server_bind(self):
        if os.name=='nt':self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        super().server_bind()

open_local=urllib.request.build_opener(urllib.request.ProxyHandler({})).open
