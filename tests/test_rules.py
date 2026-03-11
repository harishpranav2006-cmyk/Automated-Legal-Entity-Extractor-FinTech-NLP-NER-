"""
test_rules.py
Owner: Krutika
Task 3, Week 3 — Unit Tests for Rule-Based Layer

Comprehensive tests for:
  - date_normalizer.py
  - amount_normalizer.py
  - constraint_validator.py
  - entity_deduplicator.py
  - rule_engine.py

Target: ≥ 15 passing tests (this file has 25+).
Run with: pytest tests/test_rules.py -v --tb=short
"""

import pytest
from datetime import date, timedelta

from src.rules.date_normalizer      import normalize_date
from src.rules.amount_normalizer    import normalize_amount
from src.rules.constraint_validator import validate_entities
from src.rules.entity_deduplicator  import deduplicate
from src.rules.rule_engine          import apply_rules


# ═══════════════════════════════════════════════════════════════════════════════
# TestDateNormalizer — 8 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDateNormalizer:

    def test_iso_format_passthrough(self):
        """Already-ISO dates must pass through unchanged."""
        assert normalize_date("2024-01-15") == "2024-01-15"

    def test_month_day_year_long(self):
        """'January 15, 2024' → '2024-01-15'"""
        assert normalize_date("January 15, 2024") == "2024-01-15"

    def test_month_day_year_short(self):
        """'Jan 15, 2024' → '2024-01-15'"""
        assert normalize_date("Jan 15, 2024") == "2024-01-15"

    def test_slash_format_mdy(self):
        """'01/15/2024' → '2024-01-15'"""
        assert normalize_date("01/15/2024") == "2024-01-15"

    def test_ordinal_format(self):
        """'15th of January 2024' → '2024-01-15'"""
        result = normalize_date("15th of January 2024")
        assert result == "2024-01-15"

    def test_ordinal_without_of(self):
        """'15th January 2024' → '2024-01-15'"""
        result = normalize_date("15th January 2024")
        assert result == "2024-01-15"

    def test_invalid_date_returns_none(self):
        """Unparseable strings must return None."""
        assert normalize_date("not a date") is None

    def test_empty_string_returns_none(self):
        """Empty string must return None."""
        assert normalize_date("") is None

    def test_ocr_noise_letter_o_in_year(self):
        """OCR noise: 'January 15, 2O24' (O instead of 0) should normalise."""
        result = normalize_date("January 15, 2O24")
        # Should resolve to 2024-01-15
        assert result == "2024-01-15"

    def test_hyphen_format(self):
        """'01-15-2024' → '2024-01-15'"""
        result = normalize_date("01-15-2024")
        assert result == "2024-01-15"


# ═══════════════════════════════════════════════════════════════════════════════
# TestAmountNormalizer — 8 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAmountNormalizer:

    def test_dollar_format_passthrough(self):
        """'$5,000,000.00' should normalise to the same."""
        assert normalize_amount("$5,000,000.00") == "$5,000,000.00"

    def test_usd_prefix(self):
        """'USD 5000000' → '$5,000,000.00'"""
        assert normalize_amount("USD 5000000") == "$5,000,000.00"

    def test_million_word_form(self):
        """'5 million' → '$5,000,000.00'"""
        assert normalize_amount("5 million") == "$5,000,000.00"

    def test_decimal_million_suffix(self):
        """'2.5M' → '$2,500,000.00'"""
        assert normalize_amount("2.5M") == "$2,500,000.00"

    def test_usd_decimal_million(self):
        """'USD 2.5M' → '$2,500,000.00'"""
        assert normalize_amount("USD 2.5M") == "$2,500,000.00"

    def test_word_form_with_dollars(self):
        """'five million dollars' → '$5,000,000.00'"""
        assert normalize_amount("five million dollars") == "$5,000,000.00"

    def test_invalid_amount_returns_none(self):
        """Unparseable string must return None."""
        assert normalize_amount("not an amount") is None

    def test_noisy_ocr_amount(self):
        """'$5,O00,000' (letter O vs zero) should normalise to '$5,000,000.00'."""
        result = normalize_amount("$5,O00,000")
        assert result == "$5,000,000.00"

    def test_plain_integer_with_commas(self):
        """'$1,250,000' → '$1,250,000.00'"""
        assert normalize_amount("$1,250,000") == "$1,250,000.00"

    def test_billion_suffix(self):
        """'1.5B' → '$1,500,000,000.00'"""
        assert normalize_amount("1.5B") == "$1,500,000,000.00"


# ═══════════════════════════════════════════════════════════════════════════════
# TestConstraintValidator — 7 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestConstraintValidator:

    def _valid_entities(self, overrides: dict = {}) -> dict:
        """Return a valid base entity dict, optionally overridden."""
        base = {
            "parties":          ["Alpha Corp", "Beta Ltd"],
            "effective_date":   "2024-01-15",
            "termination_date": "2026-01-15",
            "total_amount":     "$5,000,000.00",
            "jurisdiction":     "New York",
        }
        base.update(overrides)
        return base

    def test_valid_contract_no_warnings(self):
        """A fully valid contract should produce zero warnings."""
        warnings = validate_entities(self._valid_entities())
        assert warnings == []

    def test_termination_before_effective_date(self):
        """termination_date < effective_date must raise CONSTRAINT_VIOLATION."""
        entities = self._valid_entities({
            "effective_date":   "2024-06-01",
            "termination_date": "2024-01-01",  # before effective
        })
        warnings = validate_entities(entities)
        assert any("CONSTRAINT_VIOLATION" in w for w in warnings)

    def test_effective_date_far_future(self):
        """effective_date > 10 years from today must raise SUSPECT_DATE."""
        far_future = (date.today() + timedelta(days=4000)).strftime('%Y-%m-%d')
        entities   = self._valid_entities({"effective_date": far_future})
        warnings   = validate_entities(entities)
        assert any("SUSPECT_DATE" in w for w in warnings)

    def test_fewer_than_two_parties(self):
        """Fewer than 2 parties must raise INCOMPLETE_CONTRACT."""
        entities = self._valid_entities({"parties": ["Only One Party"]})
        warnings = validate_entities(entities)
        assert any("INCOMPLETE_CONTRACT" in w for w in warnings)

    def test_zero_parties(self):
        """Empty parties list must raise INCOMPLETE_CONTRACT."""
        entities = self._valid_entities({"parties": []})
        warnings = validate_entities(entities)
        assert any("INCOMPLETE_CONTRACT" in w for w in warnings)

    def test_negative_amount(self):
        """Negative total_amount must raise INVALID_AMOUNT."""
        entities = self._valid_entities({"total_amount": "$-100.00"})
        warnings = validate_entities(entities)
        assert any("INVALID_AMOUNT" in w for w in warnings)

    def test_none_dates_do_not_raise_errors(self):
        """None dates should not produce date-related warnings."""
        entities = self._valid_entities({
            "effective_date":   None,
            "termination_date": None,
        })
        warnings = validate_entities(entities)
        # Only possible warning is INCOMPLETE_CONTRACT if parties < 2 but we have 2
        date_warnings = [w for w in warnings if "CONSTRAINT_VIOLATION" in w or "SUSPECT_DATE" in w]
        assert date_warnings == []


# ═══════════════════════════════════════════════════════════════════════════════
# TestEntityDeduplicator — 5 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEntityDeduplicator:

    def test_no_duplicates_unchanged(self):
        """Non-overlapping entities with different texts should all be kept."""
        entities = [
            {"text": "ABC Corp",  "label": "PARTY",  "start": 0,  "end": 8},
            {"text": "XYZ Ltd",   "label": "PARTY",  "start": 50, "end": 57},
            {"text": "2024-01-15","label": "DATE",   "start": 100,"end": 110},
        ]
        result = deduplicate(entities)
        labels = [e["label"] for e in result]
        assert "DATE" in labels
        # Both parties present (no near-duplication)
        party_texts = {e["text"] for e in result if e["label"] == "PARTY"}
        assert len(party_texts) == 2

    def test_overlapping_spans_resolved(self):
        """Overlapping spans must be reduced to a single winner (longer span)."""
        entities = [
            {"text": "ABC",         "label": "PARTY", "start": 0, "end": 3},
            {"text": "ABC Corp",    "label": "PARTY", "start": 0, "end": 8},  # longer
        ]
        result = deduplicate(entities)
        party_results = [e for e in result if e["label"] == "PARTY"]
        assert len(party_results) == 1
        assert party_results[0]["text"] == "ABC Corp"

    def test_near_duplicate_parties_merged(self):
        """'ABC Corp' and 'ABC Corporation' must be merged into one entity."""
        entities = [
            {"text": "ABC Corp",        "label": "PARTY", "start": 0,  "end": 8},
            {"text": "ABC Corporation", "label": "PARTY", "start": 50, "end": 65},
        ]
        result = deduplicate(entities)
        party_results = [e for e in result if e["label"] == "PARTY"]
        assert len(party_results) == 1
        assert party_results[0]["text"] == "ABC Corporation"  # canonical = longer

    def test_empty_list_returns_empty(self):
        """deduplicate([]) must return []."""
        assert deduplicate([]) == []

    def test_non_party_entities_not_merged(self):
        """Near-duplicate merging must only affect PARTY entities."""
        entities = [
            {"text": "January 2024",    "label": "DATE",   "start": 0,  "end": 12},
            {"text": "January 15 2024", "label": "DATE",   "start": 50, "end": 65},
        ]
        result = deduplicate(entities)
        date_results = [e for e in result if e["label"] == "DATE"]
        # Both dates are non-overlapping and non-PARTY, so both should be kept
        assert len(date_results) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# TestRuleEngine — 4 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRuleEngine:

    def test_empty_entity_list_returns_structure(self):
        """apply_rules([]) must return a valid dict with INCOMPLETE_CONTRACT warning."""
        result = apply_rules([])
        assert "entities"         in result
        assert "validation_flags" in result
        flags = result["validation_flags"]
        assert any("INCOMPLETE_CONTRACT" in f for f in flags)

    def test_full_pipeline_structured_output(self):
        """apply_rules with a complete entity list returns normalized, validated output."""
        raw_text = (
            "This SERVICES AGREEMENT is effective January 15, 2024 "
            "and shall terminate on January 15, 2026. "
            "Between ABC Corporation and XYZ Pvt Ltd. "
            "Total contract value: USD 5M. "
            "Governed under the laws of the State of New York."
        )
        raw_entities = [
            {"text": "ABC Corporation", "label": "PARTY",        "start": 80,  "end": 95},
            {"text": "XYZ Pvt Ltd",     "label": "PARTY",        "start": 100, "end": 111},
            {"text": "January 15, 2024","label": "DATE",         "start": 35,  "end": 51},
            {"text": "January 15, 2026","label": "DATE",         "start": 75,  "end": 91},
            {"text": "USD 5M",          "label": "AMOUNT",       "start": 130, "end": 136},
            {"text": "State of New York","label": "JURISDICTION", "start": 165, "end": 181},
        ]
        result = apply_rules(raw_entities, raw_text)

        entities = result["entities"]
        assert len(entities["parties"]) == 2
        assert entities["effective_date"]   == "2024-01-15"
        assert entities["termination_date"] == "2026-01-15"
        assert entities["total_amount"]     == "$5,000,000.00"
        assert entities["jurisdiction"]     == "State of New York"
        assert result["validation_flags"]   == []

    def test_pipeline_flags_bad_contract(self):
        """apply_rules detects constraint violations in a bad contract."""
        raw_entities = [
            {"text": "Alpha Inc",  "label": "PARTY",  "start": 0,  "end": 9},
            # Only 1 party → INCOMPLETE_CONTRACT
            {"text": "2023-06-01", "label": "DATE",   "start": 20, "end": 30},
            {"text": "2022-01-01", "label": "DATE",   "start": 50, "end": 60},
            # termination < effective → CONSTRAINT_VIOLATION
        ]
        result = apply_rules(raw_entities, "effective 2023-06-01 termination 2022-01-01")
        flags  = result["validation_flags"]
        flag_text = " ".join(flags)
        # Should have INCOMPLETE_CONTRACT
        assert "INCOMPLETE_CONTRACT" in flag_text

    def test_noisy_ocr_text_handled(self):
        """apply_rules handles noisy OCR text without crashing."""
        raw_entities = [
            {"text": "Acme Corp",   "label": "PARTY",  "start": 0,  "end": 9},
            {"text": "Beta Co.",    "label": "PARTY",  "start": 15, "end": 23},
            {"text": "$5,O00,000",  "label": "AMOUNT", "start": 30, "end": 40},
            {"text": "Jan 15 2024", "label": "DATE",   "start": 50, "end": 61},
        ]
        result = apply_rules(raw_entities, "$5,O00,000 effective Jan 15 2024")
        # Should not raise, amount should be resolved
        assert result["entities"]["total_amount"] == "$5,000,000.00"
        assert result["entities"]["effective_date"] == "2024-01-15"


# ═══════════════════════════════════════════════════════════════════════════════
# TestEdgeCases — 5 tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_none_input_to_normalize_date(self):
        """normalize_date(None) must return None without raising."""
        assert normalize_date(None) is None  # type: ignore[arg-type]

    def test_none_input_to_normalize_amount(self):
        """normalize_amount(None) must return None without raising."""
        assert normalize_amount(None) is None  # type: ignore[arg-type]

    def test_ocr_letter_o_vs_zero_in_amount(self):
        """OCR artefact: 'O' instead of '0' in numeric strings is handled."""
        result = normalize_amount("$5,O00,000")
        assert result == "$5,000,000.00"

    def test_partial_date_jan_2024(self):
        """Partial dates like 'Jan 2024' should be parseable (defaults to 1st)."""
        result = normalize_date("Jan 2024")
        assert result is not None
        assert result.startswith("2024-01")

    def test_deduplicate_keeps_all_non_overlapping(self):
        """All non-overlapping entities across all labels must be preserved."""
        entities = [
            {"text": "Corp A",     "label": "PARTY",        "start": 0,   "end": 6},
            {"text": "Corp B",     "label": "PARTY",        "start": 20,  "end": 26},
            {"text": "2024-01-15", "label": "DATE",         "start": 50,  "end": 60},
            {"text": "$5,000,000", "label": "AMOUNT",       "start": 70,  "end": 80},
            {"text": "New York",   "label": "JURISDICTION", "start": 90,  "end": 98},
        ]
        result = deduplicate(entities)
        # All 5 should be retained (no overlaps, no near-duplicates)
        assert len(result) == 5
