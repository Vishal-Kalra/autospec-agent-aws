"""Immutable data models for the AutoSpec pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


class AgentError(Exception):
    """Raised when an agent cannot complete its stage."""

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(f"[{stage}] {message}")
        self.stage = stage
        self.message = message


@dataclass(frozen=True)
class Brief:
    """A plain-English product brief."""
    text: str


@dataclass(frozen=True)
class RunConfig:
    """Pipeline run configuration."""
    tech_stack: str       # "Python" or "Node"
    quality_threshold: float  # 0-100

    def validate(self) -> List[str]:
        """Return list of validation errors. Empty = valid."""
        errors: List[str] = []
        if self.tech_stack not in ("Python", "Node"):
            errors.append(f"tech_stack must be 'Python' or 'Node', got '{self.tech_stack}'")
        try:
            val = float(self.quality_threshold)
            if val < 0 or val > 100:
                errors.append(f"quality_threshold must be 0-100, got {val}")
        except (TypeError, ValueError):
            errors.append(f"quality_threshold must be numeric, got '{self.quality_threshold}'")
        return errors


@dataclass(frozen=True)
class AcceptanceCriterion:
    """A Given/When/Then acceptance criterion."""
    id: str
    given: str
    when: str
    then: str

    def text(self) -> str:
        return f"GIVEN {self.given} WHEN {self.when} THEN {self.then}"


@dataclass(frozen=True)
class Requirement:
    """A numbered requirement with criteria."""
    number: int
    title: str
    criteria: Tuple[AcceptanceCriterion, ...]


@dataclass(frozen=True)
class SpecDocument:
    """Structured specification."""
    requirements: Tuple[Requirement, ...]
    edge_cases: Tuple[str, ...]

    def all_criteria(self) -> Tuple[AcceptanceCriterion, ...]:
        result: List[AcceptanceCriterion] = []
        for req in self.requirements:
            result.extend(req.criteria)
        return tuple(result)


@dataclass(frozen=True)
class GeneratedCode:
    """Generated source code module."""
    module_name: str
    source: str


@dataclass(frozen=True)
class TestSuite:
    """Generated test file."""
    source: str
    criterion_ids: Tuple[str, ...]


@dataclass(frozen=True)
class TestResult:
    """One test outcome."""
    criterion_id: str
    name: str
    status: str  # "passed" | "failed"
    detail: str = ""


@dataclass(frozen=True)
class TestReport:
    """Test execution report."""
    results: Tuple[TestResult, ...]
    passed: int
    failed: int
    coverage_percentage: Optional[float]
    quality_gate_status: Optional[str] = None


@dataclass(frozen=True)
class Gap:
    """An unmet acceptance criterion."""
    criterion_id: str
    discrepancy: str


@dataclass(frozen=True)
class AlignmentVerdict:
    """Review Agent's verdict."""
    verdict: str  # "ALIGNED" | "NOT ALIGNED"
    gaps: Tuple[Gap, ...] = ()

    @property
    def aligned(self) -> bool:
        return self.verdict == "ALIGNED"
