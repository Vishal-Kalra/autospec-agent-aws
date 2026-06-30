"""Build Agent — generates code from a specification."""
from __future__ import annotations

import time
from typing import List

from autospec.models import AgentError, Gap, GeneratedCode, SpecDocument
from autospec.demo_data import DEMO_CODE


class BuildAgent:
    """Produces a single Python module implementing the spec requirements."""

    name = "Build Agent"

    def run(self, spec: SpecDocument, gaps: List[Gap] = ()) -> GeneratedCode:
        """Generate code. On retries, gaps from the review are provided."""
        if not spec or not spec.requirements:
            raise AgentError(self.name, "Spec has no requirements.")
        time.sleep(1.2)  # Visual pacing for demo
        return DEMO_CODE
