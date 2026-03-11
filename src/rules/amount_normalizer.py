"""
amount_normalizer.py
Owner: Krutika
Task 3, Week 2–3 — Rule-Based Layer

Normalizes monetary value strings to a standard format: '$5,000,000.00'

Formats handled:
    $5,000,000.00         → $5,000,000.00  (pass through)
    USD 5,000,000         → $5,000,000.00
    USD 2.5M              → $2,500,000.00
    5,000,000 dollars     → $5,000,000.00
    5 million dollars     → $5,000,000.00
    five million dollars  → $5,000,000.00
    2.5M                  → $2,500,000.00
    2.5B                  → $2,500,000,000.00
    $5,O00,000            → $5,000,000.00  (OCR noise: letter O vs zero)
"""

import re

# ─── Word-form number mapping ─────────────────────────────────────────────────
_WORD_NUMBERS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
    'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18,
    'nineteen': 19, 'twenty': 20, 'thirty': 30, 'forty': 40,
    'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
    'hundred': 100, 'thousand': 1_000, 'million': 1_000_000,
    'billion': 1_000_000_000, 'trillion': 1_000_000_000_000,
}

# Multiplier suffixes (letter abbreviations)
_SUFFIX_MULTIPLIERS = {
    'k': 1_000,
    'K': 1_000,
    'm': 1_000_000,
    'M': 1_000_000,
    'b': 1_000_000_000,
    'B': 1_000_000_000,
    't': 1_000_000_000_000,
    'T': 1_000_000_000_000,
}

# OCR noise fix map for amount strings
_OCR_AMOUNT_NOISE: dict[str, str] = {
    'O': '0',  # letter O → zero
    'l': '1',  # lowercase L → 1
    'I': '1',  # uppercase I → 1
    'S': '5',  # S → 5 in some OCR fonts
}


def _fix_ocr_noise(text: str) -> str:
    """
    Replace OCR-confused characters inside what should be digit groups.
    Only replaces within runs adjacent to digits or standard separators.
    """
    # Targeted fix: replace O with 0 within numeric context
    # e.g. "$5,O00,000" → "$5,000,000"
    result = list(text)
    for i, ch in enumerate(result):
        if ch in _OCR_AMOUNT_NOISE:
            # Check if surrounded by digits or separators (heuristic)
            left  = result[i - 1] if i > 0 else ''
            right = result[i + 1] if i < len(result) - 1 else ''
            if (left.isdigit() or left in '$,. ') and \
               (right.isdigit() or right in ',. '):
                result[i] = _OCR_AMOUNT_NOISE[ch]
    return ''.join(result)


def _parse_word_amount(text: str) -> float | None:
    """
    Convert English word-form amounts to a float.
    e.g. "five million" → 5_000_000.0
         "two point five million" → 2_500_000.0
    """
    text = text.lower().strip()

    # Handle "X point Y" or "X.Y" within word forms
    text = re.sub(r'\bpoint\b', '.', text)

    # Replace word numbers with their digit equivalents
    tokens = re.split(r'[\s\-]+', text)
    total  = 0.0
    current = 0.0
    multiplier = 1.0

    for token in tokens:
        token = token.strip('.,')
        if token in _WORD_NUMBERS:
            val = _WORD_NUMBERS[token]
            if val >= 1_000:
                if current == 0:
                    current = 1.0
                current *= val
                total   += current
                current  = 0.0
            elif val == 100:
                if current == 0:
                    current = 1.0
                current *= 100
            else:
                current += val
        else:
            # Try numeric conversion for mixed tokens
            try:
                current += float(token)
            except ValueError:
                continue

    return total + current if (total + current) > 0 else None


def normalize_amount(raw_amount: str) -> str | None:
    """
    Parse a raw monetary string and return standardized format '$X,XXX,XXX.XX'.

    Args:
        raw_amount: Raw amount string extracted by the NER model.

    Returns:
        Standardized amount string e.g. '$5,000,000.00',
        or None if the string cannot be parsed.

    Examples:
        >>> normalize_amount("$5,000,000.00")
        '$5,000,000.00'
        >>> normalize_amount("USD 2.5M")
        '$2,500,000.00'
        >>> normalize_amount("five million dollars")
        '$5,000,000.00'
        >>> normalize_amount("$5,O00,000")
        '$5,000,000.00'
        >>> normalize_amount("not an amount")
        None
    """
    if not raw_amount or not isinstance(raw_amount, str):
        return None

    text = raw_amount.strip()

    # Fix OCR noise first
    text = _fix_ocr_noise(text)

    # Normalise whitespace
    text = re.sub(r'\s+', ' ', text)

    # ── Step 1: Check for word-form amounts first ─────────────────────────────
    # e.g. "five million dollars", "two point five billion"
    word_pattern = re.compile(
        r'\b((?:' + '|'.join(_WORD_NUMBERS.keys()) + r')[\s\.\-]*)+',
        re.IGNORECASE
    )
    # Look for sequences of purely English words
    word_only = re.sub(
        r'\b(dollars?|usd|gbp|eur|currency|cents?)\b', '', text, flags=re.IGNORECASE
    ).strip()
    if re.match(r'^[a-zA-Z\s\.\-]+$', word_only):
        value = _parse_word_amount(word_only)
        if value is not None and value > 0:
            return f'${value:,.2f}'

    # ── Step 2: Strip currency prefixes ──────────────────────────────────────
    # Remove: $, USD, GBP, EUR (with optional space)
    cleaned = re.sub(r'^\s*(?:\$|USD|GBP|EUR|£|€)\s*', '', text, flags=re.IGNORECASE)

    # ── Step 3: Handle suffix multipliers (2.5M, 1.2B, 500K) ─────────────────
    suffix_match = re.search(r'([\d,\.]+)\s*([KkMmBbTt])\b', cleaned)
    if suffix_match:
        num_str    = suffix_match.group(1).replace(',', '')
        suffix     = suffix_match.group(2)
        multiplier = _SUFFIX_MULTIPLIERS.get(suffix, 1)
        try:
            value = float(num_str) * multiplier
            if value > 0:
                return f'${value:,.2f}'
        except ValueError:
            pass

    # ── Step 4: Handle "X million / billion" word multipliers in numeric context
    # e.g. "5 million", "2.5 billion"
    word_mult_match = re.search(
        r'([\d,\.]+)\s*(million|billion|thousand|trillion)',
        cleaned, re.IGNORECASE
    )
    if word_mult_match:
        num_str    = word_mult_match.group(1).replace(',', '')
        multiplier = _WORD_NUMBERS.get(word_mult_match.group(2).lower(), 1)
        try:
            value = float(num_str) * multiplier
            if value > 0:
                return f'${value:,.2f}'
        except ValueError:
            pass

    # ── Step 5: Strip remaining non-numeric chars and parse plain number ──────
    # Remove trailing words like "dollars", "cents"
    cleaned = re.sub(r'\b(dollars?|cents?|only|and)\b', '', cleaned, flags=re.IGNORECASE)
    # Keep only digits, commas, and decimal point
    num_only = re.sub(r'[^\d\.,]', '', cleaned).strip()
    # Remove trailing commas
    num_only = num_only.rstrip(',')

    if not num_only:
        return None

    # If multiple dots, it's ambiguous — treat last as decimal
    parts = num_only.split('.')
    if len(parts) > 2:
        # e.g. "1.000.000" European style → join all but last
        num_only = ''.join(parts[:-1]) + '.' + parts[-1]

    # Remove commas now that we've handled European-style
    num_only = num_only.replace(',', '')

    try:
        value = float(num_only)
        if value > 0:
            return f'${value:,.2f}'
        return None
    except ValueError:
        return None
