"""AutoSpec Web Application — Real-time streaming pipeline dashboard."""
from __future__ import annotations

import io
import json
import os
import zipfile
from datetime import datetime
from queue import Queue, Empty
from threading import Thread

from flask import Flask, render_template, request, Response, jsonify, send_file

from autospec.models import Brief, RunConfig
from autospec.orchestrator import Orchestrator

app = Flask(__name__)

# Built-in demo brief
DEMO_BRIEF_TEXT = (
    "Build a tip calculator that takes a bill total, a tip percentage, and a number of "
    "people, and returns the tip amount, the total with tip, and the amount each person "
    "owes. Round money to 2 decimal places. The grand total is split evenly between people. "
    "0% tip is allowed (tip = 0). Number of people must be at least 1; reject 0 or negative."
)

run_history: list = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
def start_run():
    """Run the pipeline and stream events via SSE."""
    data = request.get_json() or {}
    brief_text = data.get("brief", "").strip() or DEMO_BRIEF_TEXT
    tech_stack = data.get("tech_stack", "Python")
    quality_threshold = float(data.get("quality_threshold", 90))
    demo_retry = bool(data.get("demo_retry", False))

    brief = Brief(text=brief_text)
    config = RunConfig(tech_stack=tech_stack, quality_threshold=quality_threshold)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    artifact_dir = os.path.join(os.getcwd(), "artifacts", run_id)
    event_queue: Queue = Queue()

    def emit(event_type: str, data: dict) -> None:
        event_queue.put({"type": event_type, "data": data, "ts": datetime.now().isoformat()})

    def pipeline_thread():
        orch = Orchestrator(artifact_dir=artifact_dir, emit=emit, demo_retry=demo_retry)
        result = orch.run(brief, config)
        run_history.append({"id": run_id, "brief": brief_text[:60], "status": result.get("status", "?"), "ts": datetime.now().isoformat()})
        event_queue.put(None)

    Thread(target=pipeline_thread, daemon=True).start()

    def generate():
        while True:
            try:
                ev = event_queue.get(timeout=120)
                if ev is None:
                    break
                yield f"data: {json.dumps(ev)}\n\n"
            except Empty:
                yield f"data: {json.dumps({'type':'keepalive','data':{}})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/demo-brief")
def demo_brief():
    return jsonify({"brief": DEMO_BRIEF_TEXT, "tech_stack": "Python", "quality_threshold": 90})


@app.route("/api/history")
def history():
    return jsonify(run_history)


@app.route("/api/artifacts/<run_id>")
def download_artifacts(run_id):
    d = os.path.join(os.getcwd(), "artifacts", run_id)
    if not os.path.isdir(d):
        return jsonify({"error": "not found"}), 404
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in os.listdir(d):
            zf.write(os.path.join(d, f), f)
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True,
                     download_name=f"autospec_{run_id}.zip")


if __name__ == "__main__":
    print("\n⚡ AutoSpec → http://127.0.0.1:5000\n")
    app.run(debug=False, port=5000, threaded=True)
