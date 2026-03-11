"""
constraint_validator.py
Owner: Krutika
Task 3, Week 2–3 — Rule-Based Layer

Applies logical business rules to the extracted and normalized entities.
Returns a list of validation warning strings (empty list = all rules passed).

Rules:
    1. Termination date must NOT precede effective date
    2. Effective date should not be more than 10 years in the future
    3. Total amount must be a positive value
    4. A valid contract must have at least 2 distinct parties
"""

import re
from datetime import date, datetime

# Maximum days in the future an effective date may reasonably fall
_MAX_FUTURE_DAYS = 3650  # 10 years


def _parse_iso_date(date_str: str | None) -> date | None:
    """
    Parse an ISO 8601 date string (YYYY-MM-DD) into a datetime.date object.

    Args:
        date_str: ISO 8601 string e.g. '2024-01-15', or None.

    Returns:
        datetime.date, or None if the string is None or unparseable.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def _parse_amount_value(amount_str: str | None) -> float | None:
    """
    Extract the numeric value from a standardized amount string like '$5,000,000.00'.

    Args:
        amount_str: Standardized amount string, or None.

    Returns:
        Float value, or None if the string is None or unparseable.
    """
    if not amount_str or not isinstance(amount_str, str):
        return None
    # Strip everything except digits, decimal point, and minus sign
    num_str = re.sub(r'[^\d\.\-]', '', amount_str)
    if not num_str:
        return None
    try:
        return float(num_str)
    except ValueError:
        return None


def validate_entities(entities: dict) -> list[str]:
    """
    Run all constraint rules against the structured entity dict.

    Args:
        entities: Structured dict produced by rule_engine.py. Expected keys:
                    parties          (list[str])
                    effective_date   (str | None, ISO 8601 YYYY-MM-DD)
                    termination_date (str | None, ISO 8601 YYYY-MM-DD)
                    total_amount     (str | None, e.g. '$5,000,000.00')
                    jurisdiction     (str | None)

    Returns:
        List of warning strings. Empty list means all constraints passed.

    Examples:
        >>> validate_entities({
        ...     "parties": ["A Corp", "B Ltd"],
        ...     "effective_date": "2024-01-15",
        ...     "termination_date": "2024-01-10",  # before effective!
        ...     "total_amount": "$5,000,000.00",
        ... })
        ['CONSTRAINT_VIOLATION: termination_date (2024-01-10) precedes effective_date (2024-01-15)']
    """
    warnings: list[str] = []

    eff_str  = entities.get("effective_date")
    term_str = entities.get("termination_date")
    eff      = _parse_iso_date(eff_str)
    term     = _parse_iso_date(term_str)

    # ── Rule 1: Termination date must NOT precede effective date ──────────────
    if eff is not None and term is not None:
        if term < eff:
            warnings.append(
                f"CONSTRAINT_VIOLATION: termination_date ({term_str}) "
                f"precedes effective_date ({eff_str})"
            )

    # ── Rule 2: Effective date not more than 10 years in the future ───────────
    if eff is not None:
        days_ahead = (eff - date.today()).days
        if days_ahead > _MAX_FUTURE_DAYS:
            warnings.append(
                f"SUSPECT_DATE: effective_date ({eff_str}) is "
                f"{days_ahead} days (>{_MAX_FUTURE_DAYS}) in the future"
            )

    # ── Rule 3: Amount must be positive ──────────────────────────────────────
    amount_str = entities.get("total_amount")
    if amount_str is not None:
        amount_val = _parse_amount_value(amount_str)
        if amount_val is None or amount_val <= 0:
            warnings.append(
                f"INVALID_AMOUNT: total_amount must be positive, got '{amount_str}'"
            )

    # ── Rule 4: At least 2 parties required for a valid contract ─────────────
    parties = entities.get("parties", [])
    if not isinstance(parties, list):
        parties = []
    # De-duplicate for the count check (same party listed twice shouldn't count)
    unique_parties = list({p.strip().lower() for p in parties if p and p.strip()})
    if len(unique_parties) < 2:
        warnings.append(
            f"INCOMPLETE_CONTRACT: fewer than 2 distinct parties identified "
            f"({parties})"
        )

    return warnings
