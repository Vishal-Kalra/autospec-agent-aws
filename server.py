"""Zero-dependency web server for AutoSpec.

Serves a single-page UI and streams the live pipeline run over Server-Sent
Events (SSE). Uses only the Python standard library so it runs anywhere with
no pip install.

Run:  python3 server.py   then open http://localhost:8000
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from autospec.demo import DEMO_BRIEF
from autospec.models import Brief, RunConfig
from autospec.orchestrator import Orchestrator

ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(ROOT, "web")
PORT = int(os.environ.get("PORT", "8000"))


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # quiet console
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            return self._serve_file("index.html", "text/html; charset=utf-8")
        if parsed.path == "/app.js":
            return self._serve_file("app.js", "application/javascript; charset=utf-8")
        if parsed.path == "/styles.css":
            return self._serve_file("styles.css", "text/css; charset=utf-8")
        if parsed.path == "/run":
            return self._run_pipeline(urllib.parse.parse_qs(parsed.query))
        self.send_error(404, "Not found")

    # -- static files ------------------------------------------------------
    def _serve_file(self, name: str, content_type: str):
        path = os.path.join(WEB_DIR, name)
        try:
            with open(path, "rb") as fh:
                body = fh.read()
        except OSError:
            return self.send_error(404, "Not found")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # -- SSE pipeline run --------------------------------------------------
    def _run_pipeline(self, params):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        brief_text = (params.get("brief", [DEMO_BRIEF.text])[0] or "").strip()
        stack = params.get("stack", ["Python"])[0]
        try:
            threshold = float(params.get("threshold", ["90"])[0])
        except ValueError:
            threshold = 90.0

        def emit(etype, data):
            try:
                payload = "event: %s\ndata: %s\n\n" % (etype, json.dumps(data))
                self.wfile.write(payload.encode("utf-8"))
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                raise

        run_id = time.strftime("%Y%m%d-%H%M%S")
        artifact_dir = os.path.join(ROOT, "artifacts", run_id)
        brief = Brief(text=brief_text) if brief_text else None
        config = RunConfig(tech_stack_preference=stack, quality_threshold=threshold)

        try:
            Orchestrator(
                artifact_dir=artifact_dir, emit=emit, step_delay=0.6
            ).run(brief, config)
        except (BrokenPipeError, ConnectionResetError):
            pass  # client navigated away


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("AutoSpec running at http://localhost:%d  (Ctrl+C to stop)" % PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping AutoSpec.")
        server.shutdown()


if __name__ == "__main__":
    main()
