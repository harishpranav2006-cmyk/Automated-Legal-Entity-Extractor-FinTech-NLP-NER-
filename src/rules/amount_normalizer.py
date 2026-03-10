"""
amount_normalizer.py
Owner: Krutika
Task 3, Week 2–3 — Rule-Based Layer

Normalizes monetary value strings to a standard format: '$5,000,000.00'

Formats to handle:
    $5,000,000.00       → $5,000,000.00  (pass through)
    USD 5,000,000       → $5,000,000.00
    5,000,000 dollars   → $5,000,000.00
    5 million           → $5,000,000.00
    2.5M                → $2,500,000.00
"""


def normalize_amount(raw_amount: str) -> str | None:
    """
    Parse a raw monetary string and return standardized format '$X,XXX,XXX.XX'.

    Args:
        raw_amount: Raw amount string extracted by the NER model.

    Returns:
        Standardized amount string, or None if the string cannot be parsed.
    """
    # TODO (Krutika):
    # 1. Detect and expand word-form multipliers: "million" → 1_000_000, "billion" → 1_000_000_000
    # 2. Strip currency symbols and non-numeric chars (except decimal point)
    # 3. Parse to a float value
    # 4. Format output as f"${value:,.2f}"
    # 5. Return None if parsing fails
    pass
