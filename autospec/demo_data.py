"""Deterministic demo data — curated outputs for the tip-calculator sample run.

This guarantees the live demo always works regardless of network/LLM availability.
"""
from __future__ import annotations

from autospec.models import (
    AcceptanceCriterion, AlignmentVerdict, GeneratedCode, Gap,
    Requirement, SpecDocument, TestReport, TestResult, TestSuite,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SPEC AGENT OUTPUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEMO_SPEC = SpecDocument(
    requirements=(
        Requirement(
            number=1,
            title="Calculate tip amount",
            criteria=(
                AcceptanceCriterion(
                    id="1.1",
                    given="a valid bill total and tip percentage",
                    when="the calculator is invoked",
                    then="it returns tip_amount = bill * percentage / 100, rounded to 2 decimal places",
                ),
            ),
        ),
        Requirement(
            number=2,
            title="Calculate total with tip",
            criteria=(
                AcceptanceCriterion(
                    id="2.1",
                    given="a bill total and computed tip amount",
                    when="the calculator is invoked",
                    then="it returns total_with_tip = bill + tip_amount, rounded to 2 decimal places",
                ),
            ),
        ),
        Requirement(
            number=3,
            title="Split evenly per person",
            criteria=(
                AcceptanceCriterion(
                    id="3.1",
                    given="a total_with_tip and number of people >= 1",
                    when="the calculator is invoked",
                    then="it returns per_person = total_with_tip / people, rounded to 2 decimal places",
                ),
            ),
        ),
        Requirement(
            number=4,
            title="Zero tip allowed",
            criteria=(
                AcceptanceCriterion(
                    id="4.1",
                    given="a tip percentage of 0",
                    when="the calculator is invoked",
                    then="it returns tip_amount=0.00 and total_with_tip equals the bill total",
                ),
            ),
        ),
        Requirement(
            number=5,
            title="Reject invalid people count",
            criteria=(
                AcceptanceCriterion(
                    id="5.1",
                    given="a number of people less than 1 or not an integer",
                    when="the calculator is invoked",
                    then="it raises ValueError indicating people must be an integer >= 1",
                ),
            ),
        ),
        Requirement(
            number=6,
            title="Reject negative inputs",
            criteria=(
                AcceptanceCriterion(
                    id="6.1",
                    given="a bill total < 0 or tip percentage < 0",
                    when="the calculator is invoked",
                    then="it raises ValueError indicating the value is out of allowed range",
                ),
            ),
        ),
    ),
    edge_cases=(
        "Bill of exactly 0.00 with any valid tip",
        "Tip percentage of 100% (doubles the bill)",
        "Very large bill (999,999,999.99)",
        "Single person (per_person equals total)",
        "Fractional splits requiring rounding",
        "Tip of 0% with multiple people",
    ),
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BUILD AGENT OUTPUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEMO_CODE_SOURCE = '''"""Tip Calculator — pure-function implementation.

Computes tip amounts, totals with tip, and per-person splits
using precise Decimal arithmetic with round-half-up rounding.
"""
from decimal import Decimal, ROUND_HALF_UP


def calculate_tip(bill_total: float, tip_percentage: float, num_people: int) -> dict:
    """Calculate tip, total with tip, and per-person amount.

    Args:
        bill_total: The bill amount (>= 0).
        tip_percentage: Tip percentage (>= 0, e.g. 15 means 15%).
        num_people: Number of people splitting (integer >= 1).

    Returns:
        Dict with keys: tip_amount, total_with_tip, per_person_amount (all float).

    Raises:
        ValueError: If any input is invalid.
    """
    if not isinstance(num_people, int) or num_people < 1:
        raise ValueError("Number of people must be an integer >= 1.")
    if bill_total < 0:
        raise ValueError("Bill total must be >= 0.")
    if tip_percentage < 0:
        raise ValueError("Tip percentage must be >= 0.")

    bill = Decimal(str(bill_total))
    pct = Decimal(str(tip_percentage))
    people = Decimal(str(num_people))

    tip_amount = (bill * pct / Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    total_with_tip = (bill + tip_amount).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    per_person = (total_with_tip / people).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    return {
        "tip_amount": float(tip_amount),
        "total_with_tip": float(total_with_tip),
        "per_person_amount": float(per_person),
    }
'''

DEMO_CODE = GeneratedCode(module_name="tip_calculator", source=DEMO_CODE_SOURCE)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST AGENT OUTPUT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEMO_TEST_SOURCE = '''"""Tests for Tip Calculator — one test per acceptance criterion."""
import pytest
from tip_calculator import calculate_tip


def test_1_1_calculates_tip_amount():
    """AC 1.1: tip = bill * pct / 100, rounded to 2dp."""
    result = calculate_tip(100.00, 18, 2)
    assert result["tip_amount"] == 18.00


def test_2_1_calculates_total_with_tip():
    """AC 2.1: total = bill + tip, rounded to 2dp."""
    result = calculate_tip(100.00, 18, 2)
    assert result["total_with_tip"] == 118.00


def test_3_1_splits_per_person():
    """AC 3.1: per_person = total / people, rounded to 2dp."""
    result = calculate_tip(100.00, 18, 4)
    assert result["per_person_amount"] == 29.50


def test_4_1_zero_tip_allowed():
    """AC 4.1: 0% tip returns tip=0, total=bill."""
    result = calculate_tip(75.50, 0, 3)
    assert result["tip_amount"] == 0.00
    assert result["total_with_tip"] == 75.50


def test_5_1_rejects_people_less_than_one():
    """AC 5.1: people < 1 raises ValueError."""
    with pytest.raises(ValueError, match="integer >= 1"):
        calculate_tip(50.00, 15, 0)


def test_5_1b_rejects_non_integer_people():
    """AC 5.1: non-integer people raises ValueError."""
    with pytest.raises(ValueError, match="integer >= 1"):
        calculate_tip(50.00, 15, 2.5)


def test_6_1_rejects_negative_bill():
    """AC 6.1: negative bill raises ValueError."""
    with pytest.raises(ValueError, match=">= 0"):
        calculate_tip(-10.00, 15, 1)


def test_6_1b_rejects_negative_tip():
    """AC 6.1: negative tip raises ValueError."""
    with pytest.raises(ValueError, match=">= 0"):
        calculate_tip(100.00, -5, 1)
'''

DEMO_TEST_SUITE = TestSuite(
    source=DEMO_TEST_SOURCE,
    criterion_ids=("1.1", "2.1", "3.1", "4.1", "5.1", "5.1", "6.1", "6.1"),
)
