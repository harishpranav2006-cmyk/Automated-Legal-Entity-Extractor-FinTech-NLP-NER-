"""
entity_deduplicator.py
Owner: Krutika
Task 3, Week 2–3 — Rule-Based Layer

Removes duplicate and overlapping entity spans from NER output.

Two cases to handle:
    1. Overlapping spans — two entities share character offsets
       → Keep the longer / higher-confidence span, discard the other
    2. Near-duplicate party names — e.g., "ABC Corp" vs "ABC Corporation"
       → Merge into the longer canonical form
"""


def deduplicate(entities: list[dict]) -> list[dict]:
    """
    Remove overlapping and near-duplicate entities from NER output.

    Args:
        entities: Raw entity list from predictor.predict(). Each dict:
                    {"text": str, "label": str, "start": int, "end": int}

    Returns:
        Deduplicated list with overlapping/redundant entities removed.
    """
    # TODO (Krutika):
    # 1. Sort entities by start offset
    # 2. Scan for overlapping (start, end) pairs → keep longer span
    # 3. For PARTY entities: find near-duplicates using string containment
    #    (e.g., "ABC Corp" contained in "ABC Corporation" → keep longer form)
    # 4. Return cleaned list
    pass
