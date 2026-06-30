"""Review Agent — checks spec-to-code alignment."""
from __future__ import annotations

import time

from autospec.models import (
    AgentError, AlignmentVerdict, Gap,
    GeneratedCode, SpecDocument, TestReport,
)


class ReviewAgent:
    """Audits generated code and test results, produces ALIGNED/NOT ALIGNED verdict."""

    name = "Review Agent"

    def __init__(self, force_fail_first: bool = False) -> None:
        self._force_fail_first = force_fail_first
        self._call_count = 0

    def run(self, spec: SpecDocument, code: GeneratedCode, report: TestReport) -> AlignmentVerdict:
        """Produce an alignment verdict based on test results."""
        if not spec:
            raise AgentError(self.name, "Spec is missing.")
        if not code:
            raise AgentError(self.name, "Generated code is missing.")
        if not report:
            raise AgentError(self.name, "Test report is missing.")

        time.sleep(0.8)
        self._call_count += 1

        # Demo mode: simulate a failure on the first pass to show retry loop
        if self._force_fail_first and self._call_count == 1:
            return AlignmentVerdict(
                verdict="NOT ALIGNED",
                gaps=(
                    Gap("5.1", "Edge case for non-integer people not fully handled"),
                    Gap("6.1", "Negative tip percentage boundary not tested"),
                ),
            )

        # Real logic: check if any tests failed
        if report.failed > 0:
            gaps = tuple(
                Gap(r.criterion_id, f"Test '{r.name}' failed")
                for r in report.results if r.status == "failed"
            )
            return AlignmentVerdict(verdict="NOT ALIGNED", gaps=gaps)

        return AlignmentVerdict(verdict="ALIGNED", gaps=())
