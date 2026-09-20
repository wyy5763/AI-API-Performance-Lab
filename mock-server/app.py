from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import time
import uuid
from urllib.parse import urlparse, parse_qs

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

    def _query(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    @staticmethod
    def _int_param(params, name, default):
        try:
            return int(params.get(name, [default])[0])
        except (TypeError, ValueError):
            return default

    def do_GET(self):
        path, params = self._query()
        if path == "/api/health":
            self._json(
                200,
                {
                    "status": "ok",
                    "service": "ai-api-mock",
                    "timestamp": int(time.time() * 1000),
                },
            )
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        path, params = self._query()
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            payload = {}

        status = self._int_param(params, "status", 200)
        delay_ms = self._int_param(params, "delay_ms", 0)

        if path == "/api/chat":
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
            if status != 200:
                self._json(status, {"error": "mock status", "status": status})
                return

            text = payload.get("message", "Hello from AI API Performance Lab")
            self._json(
                200,
                {
                    "id": str(uuid.uuid4()),
                    "object": "chat.completion",
                    "message": "Mock answer: " + str(text),
                    "usage": {"prompt_tokens": 20, "completion_tokens": 30},
                },
            )
            return

        if path == "/api/chat/stream":
            if status != 200:
                self._json(status, {"error": "mock status", "status": status})
                return

            text = str(payload.get("message", "Hello from AI API Performance Lab"))
            answer = "Mock streaming answer: " + text
            chunks = [answer[i : i + 12] for i in range(0, len(answer), 12)] or ["OK"]
            first_delay_ms = self._int_param(params, "ttft_ms", 180)
            interval_ms = self._int_param(params, "interval_ms", 30)
            mode = params.get("mode", ["normal"])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            if first_delay_ms > 0:
                time.sleep(first_delay_ms / 1000)

            if mode == "empty":
                self.wfile.flush()
                return

            for chunk in chunks:
                event = {"id": str(uuid.uuid4()), "delta": chunk}
                self.wfile.write(
                    ("data: " + json.dumps(event, ensure_ascii=False) + "\n\n").encode("utf-8")
                )
                self.wfile.flush()
                if interval_ms > 0:
                    time.sleep(interval_ms / 1000)

            if mode != "incomplete":
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            return

        self._json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


if __name__ == "__main__":
    print(f"AI API Mock Server: http://127.0.0.1:{PORT}")
    print("Failure simulation: ?status=500, ?delay_ms=35000, ?mode=empty, ?mode=incomplete")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
