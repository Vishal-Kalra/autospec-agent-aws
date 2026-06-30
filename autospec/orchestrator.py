"""Orchestrator — coordinates the 4-agent pipeline with self-correcting retry loop."""
from __future__ import annotations

import json
import os
import time
from typing import Callable, Dict, List, Optional

from autospec.models import (
    AgentError, AlignmentVerdict, Brief, Gap, RunConfig,
    SpecDocument, TestReport,
)
from autospec.agents import SpecAgent, BuildAgent, TestAgent, ReviewAgent

Emit = Callable[[str, Dict], None]
RETRY_LIMIT = 3


class Orchestrator:
    """Runs the full AutoSpec pipeline: validate → Spec → Build → Test → Review."""

    def __init__(
        self,
        artifact_dir: str,
        emit: Optional[Emit] = None,
        retry_limit: int = RETRY_LIMIT,
        demo_retry: bool = False,
    ) -> None:
        self.artifact_dir = artifact_dir
        self.emit = emit or (lambda t, d: None)
        self.retry_limit = retry_limit
        self.demo_retry = demo_retry
        os.makedirs(artifact_dir, exist_ok=True)

    def run(self, brief: Optional[Brief], config: Optional[RunConfig]) -> Dict:
        """Execute the full pipeline end-to-end. Returns result dict."""
        self.emit("pipeline_start", {"artifact_dir": self.artifact_dir})

        # ─── Pre-flight validation ────────────────────────────────────────
        if brief is None:
            return self._fail("Missing product brief.")
        if config is None:
            return self._fail("Missing run configuration.")
        errors = config.validate()
        if errors:
            return self._fail("Config invalid: " + "; ".join(errors))

        try:
            return self._execute(brief, config)
        except AgentError as exc:
            return self._fail(str(exc), agent=exc.stage)
        except Exception as exc:
            return self._fail(f"Unexpected error: {exc}")

    def _execute(self, brief: Brief, config: RunConfig) -> Dict:
        spec_agent = SpecAgent()
        build_agent = BuildAgent()
        test_agent = TestAgent()
        review_agent = ReviewAgent(force_fail_first=self.demo_retry)

        # ─── Stage 1: Spec Agent ──────────────────────────────────────────
        self.emit("agent_start", {"agent": spec_agent.name})
        spec = spec_agent.run(brief)
        spec_text = self._format_spec(spec)
        self.emit("agent_output", {
            "agent": spec_agent.name,
            "summary": f"{len(spec.requirements)} requirements, "
                       f"{len(spec.all_criteria())} acceptance criteria, "
                       f"{len(spec.edge_cases)} edge cases",
            "content": spec_text,
        })
        self._save("spec_document.md", spec_text)
        self.emit("handoff", {"from": spec_agent.name, "to": build_agent.name})

        # ─── Stages 2-4: Build → Test → Review (with retry loop) ─────────
        gaps: List[Gap] = []
        attempt = 0
        verdict = None
        report = None

        while True:
            # Build
            self.emit("agent_start", {"agent": build_agent.name})
            code = build_agent.run(spec, gaps)
            self.emit("agent_output", {
                "agent": build_agent.name,
                "summary": f"Generated {code.module_name}.py ({code.source.count(chr(10))+1} lines)",
                "content": code.source,
                "language": "python",
            })
            self._save("generated_code.py", code.source)
            self.emit("handoff", {"from": build_agent.name, "to": test_agent.name})

            # Test (REAL execution)
            self.emit("agent_start", {"agent": test_agent.name})
            suite, report = test_agent.run(spec, code)
            self.emit("agent_output", {
                "agent": test_agent.name,
                "summary": f"{report.passed} passed, {report.failed} failed, "
                           f"coverage {report.coverage_percentage or 0:.0f}%",
                "content": suite.source,
                "language": "python",
                "test_results": [
                    {"id": r.criterion_id, "name": r.name, "status": r.status}
                    for r in report.results
                ],
            })
            self._save("test_suite.py", suite.source)
            self._save("test_report.json", json.dumps({
                "passed": report.passed,
                "failed": report.failed,
                "coverage": report.coverage_percentage,
                "results": [{"id": r.criterion_id, "name": r.name, "status": r.status} for r in report.results],
            }, indent=2))
            self.emit("handoff", {"from": test_agent.name, "to": review_agent.name})

            # Quality gate
            gate_status = "met" if (
                report.coverage_percentage is not None
                and report.coverage_percentage >= config.quality_threshold
            ) else "not met"

            # Review
            self.emit("agent_start", {"agent": review_agent.name})
            verdict = review_agent.run(spec, code, report)
            self.emit("verdict", {
                "verdict": verdict.verdict,
                "coverage": report.coverage_percentage,
                "quality_gate": gate_status,
                "passed": report.passed,
                "failed": report.failed,
                "attempt": attempt,
                "gaps": [{"id": g.criterion_id, "desc": g.discrepancy} for g in verdict.gaps],
            })
            self._save("alignment_verdict.json", json.dumps({
                "verdict": verdict.verdict,
                "coverage": report.coverage_percentage,
                "quality_gate": gate_status,
                "gaps": [{"id": g.criterion_id, "discrepancy": g.discrepancy} for g in verdict.gaps],
            }, indent=2))

            # ─── Loop decision ────────────────────────────────────────────
            if verdict.aligned or attempt >= self.retry_limit:
                break

            attempt += 1
            gaps = list(verdict.gaps)
            self.emit("reattempt", {
                "attempt": attempt,
                "limit": self.retry_limit,
                "gaps": [{"id": g.criterion_id, "desc": g.discrepancy} for g in gaps],
            })
            self.emit("handoff", {"from": review_agent.name, "to": build_agent.name})

        # ─── Done ─────────────────────────────────────────────────────────
        result = {
            "status": "completed" if verdict.aligned else "failed",
            "verdict": verdict.verdict,
            "reattempts": attempt,
            "coverage": report.coverage_percentage if report else None,
            "passed": report.passed if report else 0,
            "failed": report.failed if report else 0,
            "quality_gate": gate_status,
        }
        self.emit("pipeline_done", result)
        return result

    def _save(self, filename: str, content: str) -> None:
        """Persist an artifact to disk."""
        path = os.path.join(self.artifact_dir, filename)
        try:
            with open(path, "w") as f:
                f.write(content)
            self.emit("artifact_saved", {"name": filename, "path": path})
        except OSError as exc:
            self.emit("error", {"agent": "ArtifactStore", "message": str(exc)})

    def _fail(self, message: str, agent: str = "Pipeline") -> Dict:
        self.emit("error", {"agent": agent, "message": message})
        self.emit("pipeline_done", {"status": "failed", "error": message})
        return {"status": "failed", "error": message}

    @staticmethod
    def _format_spec(spec: SpecDocument) -> str:
        lines = ["# Generated Specification", ""]
        for req in spec.requirements:
            lines.append(f"## Requirement {req.number}: {req.title}")
            for c in req.criteria:
                lines.append(f"- **[{c.id}]** GIVEN {c.given} WHEN {c.when} THEN {c.then}")
            lines.append("")
        lines.append("## Edge Cases")
        for ec in spec.edge_cases:
            lines.append(f"- {ec}")
        return "\n".join(lines)
