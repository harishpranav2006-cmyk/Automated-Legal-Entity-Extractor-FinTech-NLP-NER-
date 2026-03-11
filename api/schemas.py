"""
api/schemas.py — Akshada
Pydantic models for request validation and response serialisation.
"""

from typing import Optional
from pydantic import BaseModel, Field


# ─── Response Schemas ─────────────────────────────────────────────────────────

class EntitiesSchema(BaseModel):
    """Structured, validated entities extracted from the contract."""
    parties:          list[str]       = Field(default_factory=list,  description="All identified contracting parties")
    effective_date:   Optional[str]   = Field(None, description="ISO 8601 effective date (YYYY-MM-DD)")
    termination_date: Optional[str]   = Field(None, description="ISO 8601 termination date (YYYY-MM-DD)")
    total_amount:     Optional[str]   = Field(None, description="Standardised monetary value e.g. '$5,000,000.00'")
    jurisdiction:     Optional[str]   = Field(None, description="Governing law jurisdiction")


class ExtractionResponse(BaseModel):
    """Full API response returned by POST /extract."""
    document_id:        str            = Field(...,  description="Original uploaded filename")
    processing_time_ms: float          = Field(...,  description="End-to-end processing time in milliseconds")
    entities:           EntitiesSchema = Field(...,  description="Extracted and normalised entities")
    validation_flags:   list[str]      = Field(default_factory=list, description="Constraint violations or warnings")
    ocr_confidence:     Optional[float] = Field(None, description="Average OCR confidence score (0–1)")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id":        "contract_001.pdf",
                "processing_time_ms": 1240,
                "entities": {
                    "parties":          ["ABC Corporation", "XYZ Pvt Ltd"],
                    "effective_date":   "2024-01-15",
                    "termination_date": "2026-01-14",
                    "total_amount":     "$5,000,000.00",
                    "jurisdiction":     "State of New York"
                },
                "validation_flags": [],
                "ocr_confidence":   0.91
            }
        }


class RawEntityItem(BaseModel):
    """Single raw entity from the NER predictor (internal use)."""
    text:  str = Field(..., description="Matched text span")
    label: str = Field(..., description="Entity type: PARTY | DATE | AMOUNT | JURISDICTION")
    start: int = Field(..., description="Character start offset")
    end:   int = Field(..., description="Character end offset")


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    code:   Optional[str] = None