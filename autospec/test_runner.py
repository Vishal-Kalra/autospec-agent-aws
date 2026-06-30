"""Real pytest execution engine — runs generated tests for real."""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

from autospec.models import GeneratedCode, TestReport, TestResult, TestSuite


def execute_tests(code: GeneratedCode, suite: TestSuite) -> TestReport:
    """Run the test suite against the generated code using a real pytest subprocess.

    Creates a temp directory, writes both files, invokes pytest with coverage,
    and parses the real results.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write source code
        code_path = os.path.join(tmpdir, f"{code.module_name}.py")
        with open(code_path, "w") as f:
            f.write(code.source)

        # Write test file
        test_path = os.path.join(tmpdir, "test_generated.py")
        with open(test_path, "w") as f:
            f.write(suite.source)

        # Execute pytest
        cmd = [
            sys.executable, "-m", "pytest", test_path,
            f"--cov={code.module_name}",
            "--cov-report=term",
            "--tb=short", "-v",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=tmpdir, timeout=60,
            )
        except subprocess.TimeoutExpired:
            return TestReport(
                results=(TestResult("timeout", "execution", "failed", "Timeout after 60s"),),
                passed=0, failed=1, coverage_percentage=None,
            )

        # Parse verbose output: lines like "test_file.py::test_name PASSED [xx%]"
        test_results = []
        passed = 0
        failed = 0

        for line in result.stdout.split("\n"):
            match = re.search(r"::(\w+)\s+(PASSED|FAILED)", line)
            if match:
                test_name = match.group(1)
                status = match.group(2).lower()
                # Extract criterion id: test_1_1_xxx -> "1.1"
                crit_match = re.match(r"test_(\d+)_(\d+)", test_name)
                crit_id = f"{crit_match.group(1)}.{crit_match.group(2)}" if crit_match else test_name
                test_results.append(TestResult(crit_id, test_name, status, ""))
                if status == "passed":
                    passed += 1
                else:
                    failed += 1

        # Parse coverage: "TOTAL  xx  xx  xx%"
        coverage_pct = None
        for line in result.stdout.split("\n"):
            if "TOTAL" in line:
                pct_match = re.search(r"(\d+)%", line)
                if pct_match:
                    coverage_pct = float(pct_match.group(1))

        # Fallback if parsing failed
        if not test_results:
            if result.returncode == 0:
                test_results = [TestResult("all", "all_tests", "passed", "")]
                passed = 1
            else:
                test_results = [TestResult("all", "all_tests", "failed", result.stdout[-300:])]
                failed = 1

        return TestReport(
            results=tuple(test_results),
            passed=passed,
            failed=failed,
            coverage_percentage=coverage_pct,
        )
