"""
test_rules.py
Owner: Krutika
Task 3, Week 3 — Unit Tests for Rule-Based Layer

Tests for date_normalizer, amount_normalizer, constraint_validator,
entity_deduplicator, and rule_engine.

Target: ≥ 15 passing tests.
Run with: pytest tests/test_rules.py -v --tb=short
"""

import pytest

# TODO (Krutika): Uncomment once modules are implemented
# from src.rules.date_normalizer import normalize_date
# from src.rules.amount_normalizer import normalize_amount
# from src.rules.constraint_validator import validate_entities
# from src.rules.entity_deduplicator import deduplicate
# from src.rules.rule_engine import apply_rules


class TestDateNormalizer:
    def test_iso_format_passthrough(self):
        # TODO: normalize_date("2024-01-15") == "2024-01-15"
        pass

    def test_month_day_year(self):
        # TODO: normalize_date("January 15, 2024") == "2024-01-15"
        pass

    def test_slash_format(self):
        # TODO: normalize_date("01/15/2024") == "2024-01-15"
        pass

    def test_ordinal_format(self):
        # TODO: normalize_date("15th of January 2024") == "2024-01-15"
        pass

    def test_invalid_date_returns_none(self):
        # TODO: normalize_date("not a date") is None
        pass


class TestAmountNormalizer:
    def test_dollar_format_passthrough(self):
        # TODO: normalize_amount("$5,000,000.00") == "$5,000,000.00"
        pass

    def test_usd_prefix(self):
        # TODO: normalize_amount("USD 5000000") == "$5,000,000.00"
        pass

    def test_million_word_form(self):
        # TODO: normalize_amount("5 million") == "$5,000,000.00"
        pass

    def test_decimal_million(self):
        # TODO: normalize_amount("2.5M") == "$2,500,000.00"
        pass

    def test_invalid_amount_returns_none(self):
        # TODO: normalize_amount("not an amount") is None
        pass


class TestConstraintValidator:
    def test_valid_contract_no_warnings(self):
        # TODO: validate_entities({valid entities}) == []
        pass

    def test_termination_before_effective_date(self):
        # TODO: validate_entities({term < eff}) contains "CONSTRAINT_VIOLATION"
        pass

    def test_fewer_than_two_parties(self):
        # TODO: validate_entities({parties: ["Only One"]}) contains "INCOMPLETE_CONTRACT"
        pass

    def test_negative_amount(self):
        # TODO: validate_entities({total_amount: "$-100.00"}) contains "INVALID_AMOUNT"
        pass


class TestEntityDeduplicator:
    def test_no_duplicates_unchanged(self):
        # TODO: deduplicate([non-overlapping entities]) returns same list
        pass

    def test_overlapping_spans_resolved(self):
        # TODO: overlapping spans → only one kept
        pass

    def test_near_duplicate_parties_merged(self):
        # TODO: "ABC Corp" + "ABC Corporation" → ["ABC Corporation"]
        pass


class TestEdgeCases:
    def test_empty_entity_list(self):
        # TODO: apply_rules([]) returns empty entities with INCOMPLETE_CONTRACT warning
        pass

    def test_noisy_ocr_amount(self):
        # TODO: normalize_amount("$5,O00,000") handles letter-O-vs-zero gracefully
        pass
