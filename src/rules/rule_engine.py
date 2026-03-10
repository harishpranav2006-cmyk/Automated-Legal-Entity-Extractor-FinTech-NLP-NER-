"""
rule_engine.py
Owner: Krutika
Task 3, Week 2–3 — Rule-Based Layer

Master orchestrator for the post-processing pipeline.
Wires together deduplication → normalization → semantic role assignment → validation.

Input:  Raw entity list from predictor.predict(text)
Output: Structured + validated entity dict (used by api/routes/extract.py)
"""

from src.rules.date_normalizer import normalize_date
from src.rules.amount_normalizer import normalize_amount
from src.rules.entity_deduplicator import deduplicate
from src.rules.constraint_validator import validate_entities


def apply_rules(raw_entities: list[dict], raw_text: str = "") -> dict:
    """
    Apply the full post-processing rule pipeline to raw NER output.

    *** THIS IS THE PRIMARY HANDOFF INTERFACE to the API layer ***
    api/routes/extract.py calls: rule_engine.apply_rules(entities, text)

    Args:
        raw_entities: Entity list from predictor.predict(). Each dict:
                        {"text": str, "label": str, "start": int, "end": int}
        raw_text:     Original OCR text (used for date role assignment context).

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
    # TODO (Krutika):
    # 1. Call deduplicate(raw_entities) to remove overlapping spans
    # 2. Separate entities by label (DATE, AMOUNT, PARTY, JURISDICTION)
    # 3. Normalize each DATE with normalize_date()
    # 4. Normalize each AMOUNT with normalize_amount()
    # 5. Assign semantic roles to dates (effective vs termination)
    #    - Hint: look for context keywords like "effective", "commencing", "termination", "expiry"
    # 6. Build structured dict
    # 7. Call validate_entities(structured) to get validation_flags
    # 8. Return {"entities": structured, "validation_flags": warnings}
    pass
