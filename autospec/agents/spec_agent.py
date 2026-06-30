"""Spec Agent — converts a plain-English brief into structured requirements."""
from __future__ import annotations

import time

from autospec.models import AgentError, Brief, SpecDocument
from autospec.demo_data import DEMO_SPEC


class SpecAgent:
    """Produces numbered requirements with Given/When/Then acceptance criteria."""

    name = "Spec Agent"

    def run(self, brief: Brief) -> SpecDocument:
        """Convert brief into a SpecDocument. No code produced."""
        if not brief or not brief.text.strip():
            raise AgentError(self.name, "Brief is empty or non-actionable.")
        time.sleep(1.0)  # Visual pacing for demo
        return DEMO_SPEC
