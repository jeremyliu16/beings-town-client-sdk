#!/usr/bin/env python3
"""本地反代：静态托管 examples/，把 /api/* 反代到 https://beings.town/api/*
让 reference-client.html 在 localhost 同源下跑起来（绕开 CORS）。
用法: python3 proxy.py [port]

⚠️ 限制：urllib 不支持流式转发，/api/client/stream（SSE）会挂起——
仅用于本地实测「配对流程 + REST API（hear/messages/speak）」，
SSE 实时流请直连 beings.town（或浏览器直接访问官方 /client）。
"""
import http.server, socketserver, urllib.request, urllib.error, sys

UPSTREAM = "https://beings.town"
DOCROOT = "/Users/d5/workspace/beings-town-client-sdk/examples"
SKIP_REQ = ("host", "content-length", "connection", "accept-encoding")
SKIP_RESP = ("transfer-encoding", "connection", "content-length")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DOCROOT, **kw)

    def _proxy(self):
        url = UPSTREAM + self.path
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else None
        req = urllib.request.Request(url, data=body, method=self.command)
        for k, v in self.headers.items():
            if k.lower() in SKIP_REQ:
                continue
            req.add_header(k, v)
        try:
            resp = urllib.request.urlopen(req, timeout=90)
        except urllib.error.HTTPError as e:
            resp = e
        data = resp.read()
        self.send_response(resp.status)
        for k, v in resp.headers.items():
            if k.lower() in SKIP_RESP:
                continue
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _api(self):
        if self.path.startswith("/api/"):
            self._proxy()
            return True
        return False

    def do_GET(self):
        if not self._api():
            super().do_GET()
    def do_POST(self):
        if not self._api():
            self.send_error(404)
    def do_PUT(self):
        if not self._api():
            self.send_error(404)
    def do_DELETE(self):
        if not self._api():
            self.send_error(404)
    def do_PATCH(self):
        if not self._api():
            self.send_error(404)
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8642
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), Handler) as httpd:
        httpd.daemon_threads = True
        print(f"proxy serving on http://127.0.0.1:{port}", flush=True)
        httpd.serve_forever()
