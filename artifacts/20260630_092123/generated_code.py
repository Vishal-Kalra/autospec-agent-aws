"""Tip Calculator — pure-function implementation.

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
