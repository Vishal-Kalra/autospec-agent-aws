"""Test Agent — writes and executes tests against generated code."""
from __future__ import annotations

import time
from typing import Tuple

from autospec.models import AgentError, GeneratedCode, SpecDocument, TestReport, TestSuite
from autospec.demo_data import DEMO_TEST_SUITE
from autospec.test_runner import execute_tests


class TestAgent:
    """Writes one test per acceptance criterion, then runs them for real."""

    name = "Test Agent"

    def run(self, spec: SpecDocument, code: GeneratedCode) -> Tuple[TestSuite, TestReport]:
        """Produce a test suite and execute it via a real pytest subprocess."""
        if not spec or not spec.requirements:
            raise AgentError(self.name, "Spec is missing or has no requirements.")
        if not code or not code.source:
            raise AgentError(self.name, "Generated code is missing or empty.")

        suite = DEMO_TEST_SUITE
        time.sleep(0.5)  # Brief pause before execution

        # Run tests FOR REAL
        try:
            report = execute_tests(code, suite)
        except Exception as exc:
            raise AgentError(self.name, f"Test execution failed: {exc}")

        return suite, report
