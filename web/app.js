// AutoSpec front-end: drives the live SSE pipeline run and renders artifacts.

const $ = (sel) => document.querySelector(sel);
const logEl = $("#log");
const tabBody = $("#tabBody");
const artifacts = { spec: "", code: "", tests: "", report: null, verdict: null };
let activeTab = "spec";
let source = null;

function log(text, cls) {
  if (logEl.querySelector(".empty")) logEl.innerHTML = "";
  const line = document.createElement("div");
  line.className = "line " + (cls || "");
  line.textContent = text;
  logEl.appendChild(line);
  logEl.scrollTop = logEl.scrollHeight;
}

function nodes() { return Array.from(document.querySelectorAll(".node")); }
function nodeFor(agent) { return nodes().find((n) => n.dataset.agent === agent); }

function setNode(agent, cls, stateText) {
  const n = nodeFor(agent);
  if (!n) return;
  n.classList.remove("active");
  if (cls) n.classList.add(cls);
  if (stateText !== undefined) n.querySelector(".state").textContent = stateText;
}

function resetUI() {
  logEl.innerHTML = "";
  nodes().forEach((n) => {
    n.classList.remove("active", "done", "failed");
    n.querySelector(".state").textContent = "";
  });
  $("#reattempt").classList.remove("show");
  $("#verdict").classList.remove("show", "aligned", "notaligned");
  artifacts.spec = artifacts.code = artifacts.tests = "";
  artifacts.report = null;
  artifacts.verdict = null;
  renderTab(activeTab);
}

function renderTab(tab) {
  activeTab = tab;
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.tab === tab)
  );
  if (tab === "report") {
    const r = artifacts.report;
    if (!r) { tabBody.innerHTML = '<span class="empty">No test results yet.</span>'; return; }
    const grid = document.createElement("div");
    grid.className = "results-grid";
    r.results.forEach((t) => {
      const chip = document.createElement("div");
      chip.className = "test-chip " + (t.status === "passed" ? "pass" : "fail");
      chip.innerHTML =
        '<span class="dot"></span><span>' + t.name + '</span>' +
        '<span class="cid">· criterion ' + t.criterion_id + '</span>' +
        (t.detail ? '<span class="detail">' + t.detail + '</span>' : '');
      grid.appendChild(chip);
    });
    tabBody.innerHTML = "";
    tabBody.appendChild(grid);
    return;
  }
  let content = "";
  if (tab === "spec") content = artifacts.spec;
  else if (tab === "code") content = artifacts.code;
  else if (tab === "tests") content = artifacts.tests;
  else if (tab === "verdict") content = artifacts.verdict ? JSON.stringify(artifacts.verdict, null, 2) : "";
  if (!content) { tabBody.innerHTML = '<span class="empty">Not generated yet.</span>'; return; }
  const pre = document.createElement("pre");
  pre.textContent = content;
  tabBody.innerHTML = "";
  tabBody.appendChild(pre);
}

document.querySelectorAll(".tab").forEach((t) =>
  t.addEventListener("click", () => renderTab(t.dataset.tab))
);

function run() {
  if (source) source.close();
  resetUI();
  const btn = $("#runBtn");
  btn.disabled = true;
  btn.textContent = "● Running…";

  const params = new URLSearchParams({
    brief: $("#brief").value,
    stack: $("#stack").value,
    threshold: $("#threshold").value,
  });
  source = new EventSource("/run?" + params.toString());

  source.addEventListener("run_start", () => log("AutoSpec pipeline started.", "l-stage"));

  source.addEventListener("stage_start", (e) => {
    const d = JSON.parse(e.data);
    nodes().forEach((n) => n.classList.remove("active"));
    setNode(d.agent, "active", "working…");
    log("[" + d.agent + "] working…", "l-stage");
  });

  source.addEventListener("stage_output", (e) => {
    const d = JSON.parse(e.data);
    setNode(d.agent, "done", "done");
    log("  → " + d.title, "l-out");
    if (d.agent === "Spec Agent") { artifacts.spec = d.content; if (activeTab === "spec") renderTab("spec"); }
    if (d.agent === "Build Agent") { artifacts.code = d.content; if (activeTab === "code") renderTab("code"); }
    if (d.agent === "Test Agent") {
      artifacts.tests = d.content;
      if (d.results) {
        artifacts.report = { results: d.results };
        d.results.forEach((t) =>
          log("    " + (t.status === "passed" ? "✓" : "✗") + " " + t.name +
              (t.detail ? "  (" + t.detail + ")" : ""),
              t.status === "passed" ? "l-pass" : "l-fail")
        );
      }
      if (activeTab === "tests" || activeTab === "report") renderTab(activeTab);
    }
  });

  source.addEventListener("handoff", (e) => {
    const d = JSON.parse(e.data);
    log("  ──── handoff: " + d.from + " → " + d.to + " ────", "l-handoff");
  });

  source.addEventListener("reattempt", (e) => {
    const d = JSON.parse(e.data);
    const gaps = d.gaps.map((g) => "[" + g.id + "] " + g.discrepancy).join("  ·  ");
    const toast = $("#reattempt");
    toast.textContent = "↻ Self-correcting — re-attempt " + d.attempt + "/" + d.limit + ". Gaps: " + gaps;
    toast.classList.remove("show");
    void toast.offsetWidth; // restart animation
    toast.classList.add("show");
    setNode("Build Agent", "active", "retrying…");
    log("↻ RE-ATTEMPT " + d.attempt + "/" + d.limit + " — " + gaps, "l-reattempt");
  });

  source.addEventListener("verdict", (e) => {
    const d = JSON.parse(e.data);
    artifacts.verdict = d;
    const aligned = d.verdict === "ALIGNED";
    setNode("Review Agent", "done", aligned ? "ALIGNED" : "gaps found");
    const banner = $("#verdict");
    banner.classList.add("show", aligned ? "aligned" : "notaligned");
    banner.classList.remove(aligned ? "notaligned" : "aligned");
    $("#verdictText").textContent = aligned ? "✓ ALIGNED" : "⚠ NOT ALIGNED";
    $("#verdictSub").textContent = aligned
      ? d.passed + "/" + (d.passed + d.failed) + " criteria met"
      : d.gaps.length + " gap(s) to fix";
    $("#covRing").innerHTML = "coverage <b>" + (d.coverage != null ? d.coverage + "%" : "—") +
      "</b> · gate " + (d.gate || "—");
    log("VERDICT: " + d.verdict + " · coverage " + d.coverage + "% (gate: " + d.gate + ")", "l-verdict");
    if (activeTab === "verdict") renderTab("verdict");
  });

  source.addEventListener("artifact_saved", (e) => {
    const d = JSON.parse(e.data);
    log("  💾 saved " + d.name, "l-out");
  });

  source.addEventListener("error", (e) => {
    if (e.data) {
      const d = JSON.parse(e.data);
      log("!! ERROR [" + d.agent + "]: " + d.message, "l-fail");
      nodes().forEach((n) => { if (n.classList.contains("active")) setNode(n.dataset.agent, "failed", "failed"); });
    }
  });

  source.addEventListener("done", (e) => {
    const d = JSON.parse(e.data);
    log("Pipeline " + d.status + (d.reattempts ? " after " + d.reattempts + " re-attempt(s)" : "") + ".", "l-stage");
    source.close();
    source = null;
    btn.disabled = false;
    btn.textContent = "▶ Run AutoSpec pipeline";
  });

  source.onerror = () => {
    // SSE closes after the run; only re-enable if still disabled.
    if (btn.disabled) { btn.disabled = false; btn.textContent = "▶ Run AutoSpec pipeline"; }
  };
}

$("#runBtn").addEventListener("click", run);
renderTab("spec");
