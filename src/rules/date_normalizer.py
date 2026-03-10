"""
date_normalizer.py
Owner: Krutika
Task 3, Week 2–3 — Rule-Based Layer

Normalizes all legal date format variants to ISO 8601 (YYYY-MM-DD).

Formats to handle:
    01/15/2024           → 2024-01-15
    January 15, 2024     → 2024-01-15
    15th of January 2024 → 2024-01-15
    2024-01-15           → 2024-01-15  (already ISO, pass through)
"""

# TODO (Krutika): pip install python-dateutil


def normalize_date(raw_date_str: str) -> str | None:
    """
    Parse a raw date string and return ISO 8601 format (YYYY-MM-DD).

    Args:
        raw_date_str: Raw date string extracted by the NER model.

    Returns:
        ISO 8601 date string, or None if the string cannot be parsed.
    """
    # TODO (Krutika):
    # 1. Try parsing with dateutil.parser.parse(raw_date_str, dayfirst=False)
    # 2. Handle ordinal suffixes (1st, 2nd, 3rd, 4th → strip suffix before parsing)
    # 3. Return dt.strftime('%Y-%m-%d') on success
    # 4. Return None on ValueError or OverflowError
    pass
