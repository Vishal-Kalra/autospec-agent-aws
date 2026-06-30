"""Tests for Tip Calculator — one test per acceptance criterion."""
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
