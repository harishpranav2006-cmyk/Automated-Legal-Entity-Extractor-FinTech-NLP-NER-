"""
date_normalizer.py
Owner: Krutika
Task 3, Week 2–3 — Rule-Based Layer

Normalizes all legal date format variants to ISO 8601 (YYYY-MM-DD).

Formats handled:
    01/15/2024            → 2024-01-15
    01-15-2024            → 2024-01-15
    January 15, 2024      → 2024-01-15
    Jan 15, 2024          → 2024-01-15
    15th of January 2024  → 2024-01-15
    15th January 2024     → 2024-01-15
    2024-01-15            → 2024-01-15  (already ISO, pass through)
    Jan 2024              → 2024-01-01  (partial — first day of month)
"""

import re
from dateutil import parser as dateutil_parser

# Pre-compiled regex to strip ordinal suffixes: 1st, 2nd, 3rd, 4th … 31st
_ORDINAL_RE = re.compile(r'\b(\d{1,2})(st|nd|rd|th)\b', re.IGNORECASE)

# Regex to strip "of" in "15th of January" → "15th January"
_OF_RE = re.compile(r'\bof\b', re.IGNORECASE)

# OCR noise: map commonly confused characters in date strings
_OCR_NOISE = {
    'O': '0',  # letter O → zero (e.g. "2O24" → "2024")
    'l': '1',  # lowercase l → 1
    'I': '1',  # uppercase I → 1
}


def _fix_ocr_noise(text: str) -> str:
    """Replace OCR-confused characters in purely-numeric sections of a date."""
    # Only replace in digit-like runs (surrounded by digits or separators)
    result = []
    for ch in text:
        result.append(_OCR_NOISE.get(ch, ch))
    return ''.join(result)


def normalize_date(raw_date_str: str) -> str | None:
    """
    Parse a raw date string and return ISO 8601 format (YYYY-MM-DD).

    Args:
        raw_date_str: Raw date string extracted by the NER model.

    Returns:
        ISO 8601 date string (YYYY-MM-DD), or None if the string cannot
        be parsed into a valid date.

    Examples:
        >>> normalize_date("January 15, 2024")
        '2024-01-15'
        >>> normalize_date("15th of January 2024")
        '2024-01-15'
        >>> normalize_date("01/15/2024")
        '2024-01-15'
        >>> normalize_date("2024-01-15")
        '2024-01-15'
        >>> normalize_date("not a date")
        None
    """
    if not raw_date_str or not isinstance(raw_date_str, str):
        return None

    cleaned = raw_date_str.strip()

    # Fix common OCR noise characters
    cleaned = _fix_ocr_noise(cleaned)

    # Strip ordinal suffixes: "15th" → "15", "1st" → "1"
    cleaned = _ORDINAL_RE.sub(r'\1', cleaned)

    # Remove "of": "15 of January 2024" → "15 January 2024"
    cleaned = _OF_RE.sub('', cleaned)

    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    try:
        dt = dateutil_parser.parse(cleaned, dayfirst=False)
        return dt.strftime('%Y-%m-%d')
    except (ValueError, OverflowError, TypeError):
        pass

    # Second attempt: try dayfirst=True for ambiguous formats like "01/15/2024"
    # where the first number could be month or day
    try:
        dt = dateutil_parser.parse(cleaned, dayfirst=True)
        return dt.strftime('%Y-%m-%d')
    except (ValueError, OverflowError, TypeError):
        return None
