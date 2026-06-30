# ⚡ AutoSpec — AI Agent That Writes Its Own Spec, Builds, and Tests

## AWS Kiro Hackathon · Challenge 8 (Stretch)

---

## 🎯 The Problem

**Priya** is a Product Manager. She describes what she wants in 2-3 sentences.
She needs back: documented requirements, working code, and passing tests — same day.

> "I just want to type what I need and get back something that works."

---

## 💡 Solution: AutoSpec

4 AI agents in a relay. One input → all artifacts. No human in the loop.

```
Brief → [Spec Agent] → [Build Agent] → [Test Agent] → [Review Agent] → Done
                              ↑                              │
                              └── Self-Correcting Loop ──────┘
```

---

## 🏗️ The 4 Agents

| # | Agent | Input → Output |
|---|-------|---------------|
| 1 | **Spec Agent** | Brief → Numbered requirements + Given/When/Then criteria + edge cases |
| 2 | **Build Agent** | Spec → Single Python module (pure functions, documented) |
| 3 | **Test Agent** | Spec + Code → pytest suite (1 test per criterion) — **executed for real** |
| 4 | **Review Agent** | All artifacts → ALIGNED / NOT ALIGNED + exact gaps |

---

## 🔄 Innovation: Self-Correcting Loop

When Review finds gaps → feeds them back to Build → retries up to 3x automatically.

**The pipeline doesn't just report failure — it fixes itself.**

---

## 🖥️ Live Demo

`python3 app.py` → http://localhost:5000

1. Brief pre-loaded → Click **Run Pipeline**
2. Watch agents light up in sequence (real-time SSE streaming)
3. **Tests run for real** — actual pytest subprocess with coverage
4. Result: 8/8 passed, 100% coverage, ALIGNED

Then: **Self-Correction Demo** → NOT ALIGNED → retry → ALIGNED

---

## 📊 Sample Run Results

| Metric | Value |
|--------|-------|
| Requirements | 6 |
| Acceptance criteria | 6 (Given/When/Then) |
| Edge cases | 6 |
| Tests | 8 passed / 0 failed |
| Coverage | **100%** |
| Verdict | **✅ ALIGNED** |

---

## 🛠️ Built With Kiro

- `requirements.md` — 13 EARS-format requirements
- `design.md` — Architecture + 26 correctness properties
- `tasks.md` — Implementation plan with dependency graph

> "We used Kiro to build a tool that does what Kiro does."

---

## ✅ Deliverables

- [x] Live end-to-end pipeline demo (web UI)
- [x] Generated spec document (artifacts/spec_document.md)
- [x] Agent handoff diagram (animated in UI + mermaid in design.md)
- [x] Kiro spec + orchestration design (.kiro/specs/)
- [x] Generated code + **real** passing test results
- [x] This pitch

---

## 🏆 Scoring

| Criterion | Evidence |
|-----------|----------|
| Spec quality (25%) | 13 requirements, Given/When/Then, glossary, traceability |
| Working demo (30%) | Web UI, real pytest, 100% coverage, downloadable artifacts |
| Innovation (20%) | Self-correcting loop, live SSE streaming, web dashboard |
| Pitch (25%) | You're watching the demo right now |

---

## ⏱️ 3-Min Script

**[0:00-0:30]** "What if a PM types 3 sentences and gets back spec + code + tests?"

**[0:30-1:00]** "4 agents: Spec, Build, Test, Review. If something's wrong, it fixes itself."

**[1:00-2:20]** *[Live demo: Run → show relay → show Self-Correction]*

**[2:20-3:00]** "Built with Kiro's spec workflow. A spec-driven tool built with spec-driven development. That's AutoSpec."

---

**Team:** [Your Name] · **Stack:** Python · Flask · pytest · Kiro
