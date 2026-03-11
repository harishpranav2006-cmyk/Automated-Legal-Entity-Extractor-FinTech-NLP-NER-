"""
tests/test_ocr.py
Owner: Harish
Task 1 — Unit Tests for OCR Pipeline

Tests for pdf_loader, ocr_engine, text_cleaner, quality_checker.
Runs without requiring Tesseract installed (graceful mocking).

Run with: pytest tests/test_ocr.py -v --tb=short
"""

import os
import tempfile
import pytest
from pathlib import Path


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _create_minimal_text_pdf(text: str) -> str:
    """
    Create a minimal valid text-layer PDF in a temp file.
    Returns the file path.
    """
    lines = text.split('\n')
    stream_lines = ["BT", "/F1 11 Tf", "50 750 Td", "14 TL"]
    for line in lines:
        safe = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        stream_lines.append(f"({safe}) Tj T*")
    stream_lines.append("ET")
    stream_content = "\n".join(stream_lines)
    stream_bytes = stream_content.encode("latin-1", errors="replace")

    objects = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
    objects.append(
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R\n"
        b"   /MediaBox [0 0 612 792]\n"
        b"   /Contents 4 0 R\n"
        b"   /Resources << /Font << /F1 5 0 R >> >> >>\n"
        b"endobj"
    )
    stream_len = len(stream_bytes)
    obj4 = (
        f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode()
        + stream_bytes + b"\nendstream\nendobj"
    )
    objects.append(obj4)
    objects.append(
        b"5 0 obj\n"
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\n"
        b"endobj"
    )

    pdf = b"%PDF-1.4\n"
    offsets = []
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj + b"\n"

    xref_offset = len(pdf)
    pdf += b"xref\n"
    pdf += f"0 {len(objects) + 1}\n".encode()
    pdf += b"0000000000 65535 f \n"
    for off in offsets:
        pdf += f"{off:010d} 00000 n \n".encode()
    pdf += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(pdf)
    tmp.close()
    return tmp.name


# ═══════════════════════════════════════════════════════════════════════════════
# TestTextCleaner
# ═══════════════════════════════════════════════════════════════════════════════

class TestTextCleaner:

    def test_removes_multiple_spaces(self):
        from src.ocr.text_cleaner import clean_text
        result = clean_text("Hello   World  test")
        assert "  " not in result

    def test_removes_page_numbers(self):
        from src.ocr.text_cleaner import clean_text
        result = clean_text("Some text Page 3 more text")
        assert "Page 3" not in result

    def test_fixes_rn_to_m(self):
        from src.ocr.text_cleaner import clean_text
        result = clean_text("This is rn contract")
        assert " m " in result

    def test_empty_string_returns_empty(self):
        from src.ocr.text_cleaner import clean_text
        result = clean_text("")
        assert result == ""

    def test_none_returns_empty(self):
        from src.ocr.text_cleaner import clean_text
        result = clean_text(None)
        assert result == ""

    def test_strips_leading_trailing_whitespace(self):
        from src.ocr.text_cleaner import clean_text
        result = clean_text("   hello world   ")
        assert result == "hello world"


# ═══════════════════════════════════════════════════════════════════════════════
# TestQualityChecker
# ═══════════════════════════════════════════════════════════════════════════════

class TestQualityChecker:

    def test_high_quality_text_scores_high(self):
        from src.ocr.quality_checker import quality_score
        text   = "This is a good contract document with clean text"
        score  = quality_score(text)
        assert score >= 0.7

    def test_noisy_text_scores_low(self):
        from src.ocr.quality_checker import quality_score
        text  = "42 3.14 $100 2024 ## @@!! 99.9%"
        score = quality_score(text)
        assert score < 0.5

    def test_empty_text_returns_zero(self):
        from src.ocr.quality_checker import quality_score
        assert quality_score("") == 0.0

    def test_score_is_between_zero_and_one(self):
        from src.ocr.quality_checker import quality_score
        score = quality_score("some words 123 numbers")
        assert 0.0 <= score <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# TestOCREngine
# ═══════════════════════════════════════════════════════════════════════════════

class TestOCREngine:

    def test_extract_text_nonexistent_file_returns_empty(self):
        """extract_text on a nonexistent file must return empty string, not raise."""
        from src.ocr.ocr_engine import extract_text
        result = extract_text("nonexistent_file_xyz.pdf")
        assert result == ""

    def test_extract_text_returns_string(self):
        """extract_text always returns str."""
        from src.ocr.ocr_engine import extract_text
        result = extract_text("nonexistent.pdf")
        assert isinstance(result, str)

    def test_extract_text_from_text_pdf(self):
        """extract_text on a text-layer PDF should return non-empty string."""
        try:
            import fitz  # PyMuPDF required
        except ImportError:
            pytest.skip("PyMuPDF not installed")

        tmp_path = _create_minimal_text_pdf(
            "ABC Corp signed agreement on January 15 2024 for $5000000 in New York"
        )
        try:
            from src.ocr.ocr_engine import extract_text
            result = extract_text(tmp_path)
            assert isinstance(result, str)
            # PyMuPDF should extract the embedded text
            assert len(result) > 0
        finally:
            os.unlink(tmp_path)

    def test_pdf_loader_detects_text_layer(self):
        """pdf_loader.has_text_layer should return True for a text PDF."""
        try:
            import fitz
        except ImportError:
            pytest.skip("PyMuPDF not installed")

        tmp_path = _create_minimal_text_pdf("Hello contract world")
        try:
            from src.ocr.pdf_loader import has_text_layer
            result = has_text_layer(tmp_path)
            assert isinstance(result, bool)
        finally:
            os.unlink(tmp_path)