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


def validate_entities(entities: dict) -> list[str]:
    """
    Run all constraint rules against the structured entity dict.

    Args:
        entities: Structured dict produced by rule_engine.py. Expected keys:
                    parties          (list[str])
                    effective_date   (str | None, ISO 8601)
                    termination_date (str | None, ISO 8601)
                    total_amount     (str | None, e.g. '$5,000,000.00')
                    jurisdiction     (str | None)

    Returns:
        List of warning strings. Empty list means all constraints passed.
    """
    warnings = []

    # TODO (Krutika): Implement these 4 constraint rules:
    #
    # Rule 1 — Termination before Effective date
    #   if termination_date < effective_date: append CONSTRAINT_VIOLATION warning
    #
    # Rule 2 — Effective date far in the future (> 10 years from today)
    #   if (effective_date - today).days > 3650: append SUSPECT_DATE warning
    #
    # Rule 3 — Amount must be positive
    #   parse total_amount to float; if <= 0: append INVALID_AMOUNT warning
    #
    # Rule 4 — At least 2 parties required
    #   if len(parties) < 2: append INCOMPLETE_CONTRACT warning

    return warnings
