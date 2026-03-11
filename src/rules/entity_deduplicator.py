"""
entity_deduplicator.py
Owner: Krutika
Task 3, Week 2–3 — Rule-Based Layer

Removes duplicate and overlapping entity spans from NER output.

Two cases handled:
    1. Overlapping spans — two entities share character offsets
       → Keep the longer span (covers more context); on a tie, keep higher
         confidence if available, otherwise keep the first one.
    2. Near-duplicate party names — e.g., "ABC Corp" vs "ABC Corporation"
       → Merge into the longer (more canonical) form.
"""

import re


def _spans_overlap(e1: dict, e2: dict) -> bool:
    """Return True if entity spans e1 and e2 overlap in character space."""
    s1, end1 = e1.get("start", 0), e1.get("end", 0)
    s2, end2 = e2.get("start", 0), e2.get("end", 0)
    return s1 < end2 and s2 < end1


def _span_length(entity: dict) -> int:
    """Return the character-span length of an entity."""
    return entity.get("end", 0) - entity.get("start", 0)


def _confidence(entity: dict) -> float:
    """Return the model confidence of an entity (default 0.0 if absent)."""
    return float(entity.get("confidence", entity.get("score", 0.0)))


def _normalize_party_name(name: str) -> str:
    """
    Normalize a party name for near-duplicate comparison.
    Lowercases, strips punctuation, and expands common abbreviations.
    """
    name = name.lower().strip()
    # Expand common corporate suffix abbreviations
    abbreviations = {
        r'\bcorp\b':   'corporation',
        r'\bco\b':     'company',
        r'\bltd\b':    'limited',
        r'\binc\b':    'incorporated',
        r'\bllc\b':    'limited liability company',
        r'\bllp\b':    'limited liability partnership',
        r'\bplc\b':    'public limited company',
        r'\bpvt\b':    'private',
        r'\bpvt ltd\b': 'private limited',
        r'\bint\'?l\b': 'international',
    }
    for pattern, replacement in abbreviations.items():
        name = re.sub(pattern, replacement, name)
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def _are_near_duplicates(name_a: str, name_b: str) -> bool:
    """
    Return True if two party names are near-duplicates.

    Strategy:
      - Exact match after normalization
      - One normalized name is a substring of the other (containment check)
      - Both names share ≥ 80% of tokens (for fuzzy matching without extra deps)
    """
    norm_a = _normalize_party_name(name_a)
    norm_b = _normalize_party_name(name_b)

    if norm_a == norm_b:
        return True

    # Containment check
    if norm_a in norm_b or norm_b in norm_a:
        return True

    # Token overlap check (80% threshold, min 2 shared tokens)
    tokens_a = set(norm_a.split())
    tokens_b = set(norm_b.split())
    if not tokens_a or not tokens_b:
        return False
    shared    = tokens_a & tokens_b
    smaller   = min(len(tokens_a), len(tokens_b))
    if smaller >= 1 and len(shared) / smaller >= 0.8 and len(shared) >= 2:
        return True

    return False


def _resolve_overlaps(entities: list[dict]) -> list[dict]:
    """
    Remove overlapping entity spans *of the same label*, keeping the better
    entity for each conflict.

    IMPORTANT: Entities with *different* labels (e.g. DATE vs PARTY) are
    allowed to share character offsets without eliminating each other — in
    real contracts a date mention often falls inside or near a party name
    phrase, and we must not drop valid entities of a different type.

    Selection priority (within same-label conflicts):
      1. Longer span (more context captured)
      2. Higher confidence score (if spans are equal length)
      3. Earlier occurrence (stable sort fallback)

    Returns a sorted, non-overlapping-within-label list of entities.
    """
    if not entities:
        return []

    # Group entities by label, resolve overlaps within each group independently
    from collections import defaultdict
    by_label: dict[str, list[dict]] = defaultdict(list)
    for e in entities:
        by_label[e.get("label", "UNKNOWN")].append(e)

    all_kept: list[dict] = []

    for label, group in by_label.items():
        # Sort by start offset, then by descending span length (greedy approach)
        sorted_ents = sorted(
            group,
            key=lambda e: (e.get("start", 0), -_span_length(e))
        )

        kept: list[dict] = []
        for candidate in sorted_ents:
            overlaps_with_kept = [e for e in kept if _spans_overlap(candidate, e)]

            if not overlaps_with_kept:
                kept.append(candidate)
            else:
                # Compare candidate against each entity it overlaps with
                replace_all = True
                for existing in overlaps_with_kept:
                    cand_len   = _span_length(candidate)
                    exist_len  = _span_length(existing)
                    cand_conf  = _confidence(candidate)
                    exist_conf = _confidence(existing)

                    # Candidate wins if it's longer, or same length with higher conf
                    if cand_len > exist_len or (
                        cand_len == exist_len and cand_conf > exist_conf
                    ):
                        continue  # candidate beats this existing entity
                    else:
                        replace_all = False
                        break

                if replace_all:
                    # Remove all overlapping existing entities and add candidate
                    kept = [e for e in kept if not _spans_overlap(candidate, e)]
                    kept.append(candidate)
                # else: candidate loses to at least one existing entity; skip it

        all_kept.extend(kept)

    return sorted(all_kept, key=lambda e: e.get("start", 0))


def _merge_party_near_duplicates(entities: list[dict]) -> list[dict]:
    """
    Merge near-duplicate PARTY entities, keeping the canonical (longer) form.

    For each cluster of near-duplicates, the canonical form is the one with
    the longest original text string.  All duplicate occurrences are removed
    and replaced by a single entry for the canonical form.

    Non-PARTY entities are returned unchanged.
    """
    party_entities   = [e for e in entities if e.get("label") == "PARTY"]
    non_party_entities = [e for e in entities if e.get("label") != "PARTY"]

    if not party_entities:
        return non_party_entities

    # Union-find style clustering
    n      = len(party_entities)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for i in range(n):
        for j in range(i + 1, n):
            if _are_near_duplicates(
                party_entities[i].get("text", ""),
                party_entities[j].get("text", "")
            ):
                union(i, j)

    # Group by cluster
    clusters: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        clusters.setdefault(root, []).append(i)

    merged_parties: list[dict] = []
    for root, members in clusters.items():
        # Canonical form = entity with longest text
        canonical_idx = max(members, key=lambda i: len(party_entities[i].get("text", "")))
        canonical = dict(party_entities[canonical_idx])  # copy
        merged_parties.append(canonical)

    return non_party_entities + merged_parties


def deduplicate(entities: list[dict]) -> list[dict]:
    """
    Remove overlapping and near-duplicate entities from NER output.

    Pipeline:
        1. Resolve overlapping character spans (keep longer / higher-confidence)
        2. Merge near-duplicate PARTY names (keep canonical long form)

    Args:
        entities: Raw entity list from predictor.predict(). Each dict must
                  contain at minimum:
                    {
                        "text":  str,
                        "label": str,   # PARTY | DATE | AMOUNT | JURISDICTION
                        "start": int,   # character start offset
                        "end":   int    # character end offset
                    }
                  Optionally: "confidence" or "score" (float, default 0.0)

    Returns:
        Deduplicated list with overlapping / redundant entities removed.

    Examples:
        >>> deduplicate([])
        []
        >>> deduplicate([
        ...     {"text": "ABC Corp",        "label": "PARTY", "start": 0,  "end": 8},
        ...     {"text": "ABC Corporation", "label": "PARTY", "start": 30, "end": 45},
        ... ])
        [{"text": "ABC Corporation", "label": "PARTY", "start": 30, "end": 45}]
    """
    if not entities:
        return []

    non_empty = [e for e in entities if isinstance(e, dict) and e.get("text", "").strip()]

    # Step 1 — remove overlapping spans
    deduped = _resolve_overlaps(non_empty)

    # Step 2 — merge near-duplicate party names
    deduped = _merge_party_near_duplicates(deduped)

    return deduped
