"""
tests/test_e2e.py — Krutika (owner) / Akshada (skeleton)
End-to-end integration test for the full LexiScan Auto pipeline.
Runs against a live Docker container at http://localhost:8000

Prerequisites:
    docker-compose up --build
    # Wait for container to be healthy
    pytest tests/test_e2e.py -v

The test uses data/test/held_out_contract.pdf — a clean contract
that should produce zero validation flags.
"""

import re
import pytest
import requests

BASE_URL        = "http://localhost:8000"
TEST_PDF_PATH   = "data/test/held_out_contract.pdf"
TIMEOUT_SECONDS = 60


# ─── Helper ───────────────────────────────────────────────────────────────────
def post_pdf(pdf_path: str) -> requests.Response:
    with open(pdf_path, "rb") as f:
        return requests.post(
            f"{BASE_URL}/extract",
            files={"file": (pdf_path.split("/")[-1], f, "application/pdf")},
            timeout=TIMEOUT_SECONDS,
        )


# ─── Health Check ─────────────────────────────────────────────────────────────
def test_api_health():
    """API must be reachable and healthy before running pipeline tests."""
    resp = requests.get(f"{BASE_URL}/health", timeout=10)
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    data = resp.json()
    assert data["status"] == "ok"


# ─── Full Pipeline Test ───────────────────────────────────────────────────────
def test_full_pipeline_on_held_out_contract():
    """
    Submits a held-out clean contract PDF and verifies:
    - HTTP 200 response
    - All 4 entity types present
    - Dates in ISO 8601 format
    - No constraint violations
    """
    resp = post_pdf(TEST_PDF_PATH)

    assert resp.status_code == 200, (
        f"Expected 200 but got {resp.status_code}.\nBody: {resp.text}"
    )

    data = resp.json()

    # ── Structural checks ──────────────────────────────────────────────────────
    assert "document_id"        in data
    assert "processing_time_ms" in data
    assert "entities"           in data
    assert "validation_flags"   in data

    entities = data["entities"]

    # ── At least 2 parties ─────────────────────────────────────────────────────
    parties = entities.get("parties", [])
    assert len(parties) >= 2, (
        f"Expected ≥2 parties, got {len(parties)}: {parties}"
    )

    # ── Effective date present and ISO 8601 ───────────────────────────────────
    eff_date = entities.get("effective_date")
    assert eff_date is not None, "effective_date is None — should be detected."
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", eff_date), (
        f"effective_date '{eff_date}' is not ISO 8601 (YYYY-MM-DD)."
    )

    # ── Amount present ────────────────────────────────────────────────────────
    amount = entities.get("total_amount")
    assert amount is not None, "total_amount is None — should be detected."

    # ── No validation flags on a clean contract ────────────────────────────────
    flags = data.get("validation_flags", [])
    assert flags == [], (
        f"Expected no validation flags on clean contract, got: {flags}"
    )

    # ── Processing time sanity check ──────────────────────────────────────────
    ms = data.get("processing_time_ms", 0)
    assert ms > 0, "processing_time_ms must be positive."
    assert ms < 30_000, f"Processing took too long: {ms}ms (>30s threshold)."

    print(f"\n✅ E2E test passed in {ms}ms")
    print(f"   Parties:    {parties}")
    print(f"   Eff. Date:  {eff_date}")
    print(f"   Amount:     {amount}")
    print(f"   Flags:      {flags}")


# ─── Error Handling Tests ─────────────────────────────────────────────────────
def test_non_pdf_upload_rejected():
    """Non-PDF files should return HTTP 400."""
    resp = requests.post(
        f"{BASE_URL}/extract",
        files={"file": ("test.txt", b"this is not a pdf", "text/plain")},
        timeout=10,
    )
    assert resp.status_code == 400, (
        f"Expected 400 for non-PDF, got {resp.status_code}"
    )


def test_empty_file_rejected():
    """Empty PDF should return a non-200 error."""
    resp = requests.post(
        f"{BASE_URL}/extract",
        files={"file": ("empty.pdf", b"", "application/pdf")},
        timeout=10,
    )
    assert resp.status_code in (400, 422, 500), (
        f"Expected error status for empty file, got {resp.status_code}"
    )