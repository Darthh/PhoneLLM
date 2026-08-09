"""Serves index.html and proxies /api/* to Ollama on localhost.

The proxy exists because the Ollama desktop app pins its listener to 127.0.0.1
regardless of OLLAMA_HOST. Proxying also means no CORS config and only one
firewall rule.
"""
import urllib.request, urllib.error
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from pathlib import Path

OLLAMA = "http://127.0.0.1:11434"
PORT = 8080


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.proxy() if self.path.startswith("/api/") else super().do_GET()

    def do_POST(self):
        self.proxy()

    def proxy(self):
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0)) or None
        req = urllib.request.Request(
            OLLAMA + self.path, data=body, method=self.command,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as up:
                self.send_response(up.status)
                self.send_header("Content-Type", up.headers.get("Content-Type", "application/json"))
                self.end_headers()
                # read1, not read: returns whatever has arrived instead of waiting
                # for a full buffer, so tokens reach the phone as they generate.
                for chunk in iter(partial(up.read1, 8192), b""):
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())
        except OSError as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"cannot reach Ollama at {OLLAMA}: {e}".encode())

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    import socket
    ip = socket.gethostbyname_ex(socket.gethostname())[2][-1]
    print(f"On your phone, open:  http://{ip}:{PORT}")
    handler = partial(Handler, directory=str(Path(__file__).parent))
    ThreadingHTTPServer(("0.0.0.0", PORT), handler).serve_forever()
