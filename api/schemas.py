"""
schemas.py
Owner: Akshada
Task 4, Week 4 — Pydantic Request/Response Models

Defines the data shapes for the /extract API endpoint.
"""

from pydantic import BaseModel


class EntitiesSchema(BaseModel):
    """Structured entity output after rule-based post-processing."""
    parties: list[str] = []
    effective_date: str | None = None
    termination_date: str | None = None
    total_amount: str | None = None
    jurisdiction: str | None = None


class ExtractionResponse(BaseModel):
    """
    Full response returned by POST /extract.

    Example:
        {
            "document_id":      "contract_001.pdf",
            "processing_time_ms": 1240,
            "entities": { ... },
            "validation_flags": [],
            "ocr_confidence":   0.91
        }
    """
    document_id: str
    processing_time_ms: int
    entities: EntitiesSchema
    validation_flags: list[str] = []
    ocr_confidence: float | None = None

    # TODO (Akshada): Add any additional fields needed by the API response
