from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json, time, uuid

HOST = "0.0.0.0"
PORT = 8088

class Handler(BaseHTTPRequestHandler):
    def _json(self, code, data):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/health":
            self._json(200, {"status":"ok", "service":"ai-api-mock", "timestamp":int(time.time()*1000)})
        else:
            self._json(404, {"error":"not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            payload = {}

        if self.path == "/api/chat":
            time.sleep(0.18)
            text = payload.get("message", "Hello from AI API Performance Lab")
            self._json(200, {"id":str(uuid.uuid4()), "object":"chat.completion", "message":"Mock answer: "+str(text), "usage":{"prompt_tokens":20,"completion_tokens":30}})
            return

        if self.path == "/api/chat/stream":
            text = str(payload.get("message", "Hello from AI API Performance Lab"))
            answer = "Mock streaming answer: " + text
            chunks = [answer[i:i+12] for i in range(0, len(answer), 12)] or ["OK"]
            time.sleep(0.18)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            for chunk in chunks:
                event = {"id":str(uuid.uuid4()), "delta":chunk}
                self.wfile.write(("data: "+json.dumps(event, ensure_ascii=False)+"\n\n").encode("utf-8"))
                self.wfile.flush()
                time.sleep(0.03)
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            return

        self._json(404, {"error":"not found"})

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

if __name__ == "__main__":
    print(f"AI API Mock Server: http://127.0.0.1:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
