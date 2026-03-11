"""
rule_engine.py
Owner: Krutika
Task 3, Week 2–3 — Rule-Based Layer

Master orchestrator for the post-processing pipeline.
Wires together: deduplication → normalization → semantic role assignment → validation.

Input:  Raw entity list from predictor.predict(text)
Output: Structured + validated entity dict (used by api/routes/extract.py)
"""

import re
import logging

from src.rules.date_normalizer      import normalize_date
from src.rules.amount_normalizer    import normalize_amount
from src.rules.entity_deduplicator  import deduplicate
from src.rules.constraint_validator import validate_entities

logger = logging.getLogger(__name__)

# ─── Date Role Assignment Keywords ───────────────────────────────────────────
# Used to classify which DATE entity is the effective date vs termination date
_EFFECTIVE_KEYWORDS = re.compile(
    r'\b(effective|commence[sd]?|commencement|start|begin[ns]?|beginning|'
    r'execution|executed|dated?|entered)\b',
    re.IGNORECASE,
)

_TERMINATION_KEYWORDS = re.compile(
    r'\b(terminat(?:e[sd]?|ion|ing)|expir(?:e[sd]?|y|ation)|end[s]?|'
    r'conclud(?:e[sd]?|es)|expiration|completion)\b',
    re.IGNORECASE,
)

# Context window (characters) around a date span to search for keywords
_CONTEXT_WINDOW = 120


def _get_context(text: str, start: int, end: int, window: int = _CONTEXT_WINDOW) -> str:
    """Extract surrounding text context for a span."""
    ctx_start = max(0, start - window)
    ctx_end   = min(len(text), end + window)
    return text[ctx_start:ctx_end]


def _assign_date_roles(
    date_entities: list[dict],
    raw_text: str,
) -> tuple[str | None, str | None]:
    """
    Assign semantic roles (effective_date, termination_date) to extracted DATE entities.

    Strategy:
      1. For each DATE entity, inspect surrounding text for role keywords.
      2. First entity strongly associated with effective keywords → effective_date.
      3. First entity strongly associated with termination keywords → termination_date.
      4. Fallback: if only one date and no keywords, treat as effective_date.
      5. Fallback: if two dates and roles unresolved, assign chronologically
         (earlier → effective, later → termination).

    Args:
        date_entities: List of DATE entity dicts with start/end offsets.
        raw_text:      Original OCR/text string for context keyword lookup.

    Returns:
        (effective_date_iso, termination_date_iso) — either may be None.
    """
    if not date_entities:
        return None, None

    # Normalize all date values
    normalized: list[tuple[dict, str | None]] = []
    for ent in date_entities:
        iso = normalize_date(ent.get("text", ""))
        if iso:
            normalized.append((ent, iso))

    if not normalized:
        return None, None

    # Score each date by keyword matches in its surrounding context
    effective_candidates:    list[tuple[str, int]] = []  # (iso_date, score)
    termination_candidates:  list[tuple[str, int]] = []

    for ent, iso in normalized:
        start   = ent.get("start", 0)
        end     = ent.get("end", 0)
        context = _get_context(raw_text, start, end)

        eff_score  = len(_EFFECTIVE_KEYWORDS.findall(context))
        term_score = len(_TERMINATION_KEYWORDS.findall(context))

        if eff_score > 0:
            effective_candidates.append((iso, eff_score))
        if term_score > 0:
            termination_candidates.append((iso, term_score))

    # Pick best-scoring candidates
    effective_date    = None
    termination_date  = None

    if effective_candidates:
        effective_date = max(effective_candidates, key=lambda x: x[1])[0]
    if termination_candidates:
        termination_date = max(termination_candidates, key=lambda x: x[1])[0]

    # If same date was assigned both roles, clear termination (prefer effective)
    if effective_date and termination_date and effective_date == termination_date:
        termination_date = None

    # ── Fallback: chronological assignment ────────────────────────────────────
    if not effective_date and not termination_date:
        iso_dates = sorted(set(iso for _, iso in normalized))
        if iso_dates:
            effective_date   = iso_dates[0]
            termination_date = iso_dates[1] if len(iso_dates) > 1 else None

    elif not effective_date and termination_date:
        # Assign the earliest remaining date as effective_date
        remaining = [iso for _, iso in normalized if iso != termination_date]
        if remaining:
            effective_date = min(remaining)

    elif effective_date and not termination_date:
        # Assign the latest remaining date as termination_date
        remaining = [iso for _, iso in normalized if iso != effective_date]
        if remaining:
            termination_date = max(remaining)

    return effective_date, termination_date


def apply_rules(raw_entities: list[dict], raw_text: str = "") -> dict:
    """
    Apply the full post-processing rule pipeline to raw NER output.

    *** THIS IS THE PRIMARY HANDOFF INTERFACE to the API layer ***
    api/routes/extract.py calls: rule_engine.apply_rules(entities, text)

    Pipeline stages:
        1. Deduplicate + resolve overlapping spans
        2. Separate entities by label
        3. Normalize DATE strings to ISO 8601
        4. Normalize AMOUNT strings to standardized format
        5. Assign semantic roles to dates (effective vs termination)
        6. Build structured entity dict
        7. Validate structured entities (constraint rules)
        8. Return {entities, validation_flags}

    Args:
        raw_entities: Entity list from predictor.predict(). Each dict:
                        {"text": str, "label": str, "start": int, "end": int}
                      Optionally includes "confidence" (float).
        raw_text:     Original OCR text (used for date role keyword lookup).

    Returns:
        Dict with keys:
            entities         (dict)  — structured, normalized entities
            validation_flags (list)  — list of warning strings (empty = clean)

    Example return:
        {
            "entities": {
                "parties":          ["ABC Corporation", "XYZ Pvt Ltd"],
                "effective_date":   "2024-01-15",
                "termination_date": "2026-01-14",
                "total_amount":     "$5,000,000.00",
                "jurisdiction":     "State of New York"
            },
            "validation_flags": []
        }
    """
    logger.debug("apply_rules() called with %d raw entities.", len(raw_entities))

    # ── Stage 1: Deduplicate ──────────────────────────────────────────────────
    entities = deduplicate(raw_entities or [])
    logger.debug("%d entities after deduplication.", len(entities))

    # ── Stage 2: Separate by label ────────────────────────────────────────────
    date_ents:         list[dict] = [e for e in entities if e.get("label") == "DATE"]
    amount_ents:       list[dict] = [e for e in entities if e.get("label") == "AMOUNT"]
    party_ents:        list[dict] = [e for e in entities if e.get("label") == "PARTY"]
    jurisdiction_ents: list[dict] = [e for e in entities if e.get("label") == "JURISDICTION"]

    # ── Stage 3 & 4: Normalize dates and amounts ──────────────────────────────
    # (normalization happens inside _assign_date_roles and inline below)

    # ── Stage 5: Assign semantic date roles ───────────────────────────────────
    effective_date, termination_date = _assign_date_roles(date_ents, raw_text)

    # ── Stage 4 (amounts) ─────────────────────────────────────────────────────
    normalized_amounts = []
    for ent in amount_ents:
        norm = normalize_amount(ent.get("text", ""))
        if norm:
            normalized_amounts.append(norm)

    # ── Stage 6: Build structured dict ───────────────────────────────────────
    parties       = [e.get("text", "").strip() for e in party_ents if e.get("text", "").strip()]
    jurisdictions = [e.get("text", "").strip() for e in jurisdiction_ents if e.get("text", "").strip()]

    structured = {
        "parties":          parties,
        "effective_date":   effective_date,
        "termination_date": termination_date,
        "total_amount":     normalized_amounts[0] if normalized_amounts else None,
        "jurisdiction":     jurisdictions[0] if jurisdictions else None,
    }

    # ── Stage 7: Validate ────────────────────────────────────────────────────
    warnings = validate_entities(structured)
    logger.debug("Validation produced %d warnings.", len(warnings))

    # ── Stage 8: Return ──────────────────────────────────────────────────────
    return {
        "entities":         structured,
        "validation_flags": warnings,
    }
