"""
api/routes/extract.py
Owner: Krutika
Task 4, Week 4 — /extract Endpoint

Wires the full pipeline: PDF upload → OCR → NER → Rules → JSON response.

POST /extract
    Request:  multipart/form-data with field "file" (PDF)
    Response: ExtractionResponse JSON
"""

import io
import time
import logging
import tempfile
import os
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from api.schemas import ExtractionResponse, EntitiesSchema

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Pipeline Helpers ─────────────────────────────────────────────────────────

def _run_ocr(pdf_path: str) -> tuple[str, float | None]:
    """
    Extract text from a PDF file using the OCR engine (Harish's module).

    Args:
        pdf_path: Absolute path to the temporary PDF file.

    Returns:
        (extracted_text, ocr_confidence) — confidence may be None if not available.
    """
    try:
        from src.ocr.ocr_engine import extract_text
        result = extract_text(pdf_path)
        # extract_text may return a string or a dict with text + confidence
        if isinstance(result, dict):
            text       = result.get("text", "")
            confidence = result.get("confidence", None)
        else:
            text       = str(result)
            confidence = None
        return text, confidence
    except ImportError:
        logger.warning("OCR engine not available — using empty text fallback.")
        return "", None
    except Exception as e:
        logger.error(f"OCR failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")


def _run_ner(text: str) -> list[dict]:
    """
    Run Named Entity Recognition on the extracted text (Akshada's predictor).

    Args:
        text: Plain text extracted from the PDF.

    Returns:
        List of raw entity dicts: [{"text": str, "label": str, "start": int, "end": int}, ...]
    """
    if not text or not text.strip():
        logger.warning("NER called with empty text — returning empty entity list.")
        return []

    try:
        from src.ner.predictor import predict
        entities = predict(text)
        if not isinstance(entities, list):
            logger.warning("predict() returned non-list: %s", type(entities))
            return []
        return entities
    except ImportError:
        logger.warning("NER predictor not available — returning empty entity list.")
        return []
    except FileNotFoundError:
        logger.warning("NER model file not found — returning empty entity list.")
        return []
    except Exception as e:
        logger.error(f"NER prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"NER prediction failed: {e}")


def _run_rules(raw_entities: list[dict], raw_text: str) -> dict:
    """
    Apply the rule-based post-processing layer (Krutika's rule_engine).

    Args:
        raw_entities: Entity list from the NER predictor.
        raw_text:     Original OCR text for date-role context.

    Returns:
        Dict: {"entities": {...}, "validation_flags": [...]}
    """
    try:
        from src.rules.rule_engine import apply_rules
        return apply_rules(raw_entities, raw_text)
    except Exception as e:
        logger.error(f"Rule engine failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Rule processing failed: {e}")


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post(
    "/extract",
    response_model=ExtractionResponse,
    summary="Extract Legal Entities from a Contract PDF",
    description=(
        "Upload a PDF contract. The pipeline runs OCR → NER → Rule-Based Post-Processing "
        "and returns structured entities (parties, dates, amounts, jurisdiction) along with "
        "any validation warnings."
    ),
    responses={
        200: {"description": "Successfully extracted entities."},
        400: {"description": "Invalid file (not a PDF, empty, or too large)."},
        500: {"description": "Internal processing error."},
    },
)
async def extract_entities(
    file: UploadFile = File(..., description="PDF contract file to analyse"),
) -> ExtractionResponse:
    """
    POST /extract — Full pipeline: OCR → NER → Rules → JSON response.

    Request:
        multipart/form-data, field name: "file", content-type: application/pdf

    Response:
        ExtractionResponse JSON with extracted entities and validation flags.
    """
    t_start = time.time()

    # ── Validation ─────────────────────────────────────────────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF files are accepted. Got: '{file.filename}'"
        )

    # Read file bytes (limit 50 MB)
    MAX_SIZE_BYTES = 50 * 1024 * 1024
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(content)} bytes (max 50 MB)."
        )

    # Basic PDF magic-byte check
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="File does not appear to be a valid PDF (missing PDF header)."
        )

    logger.info(
        "Processing upload: '%s' (%d bytes)", file.filename, len(content)
    )

    # ── Stage 1: OCR ──────────────────────────────────────────────────────────
    # Write to a temporary file so OCR engine can read it from disk
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        raw_text, ocr_confidence = _run_ocr(tmp_path)
        logger.info(
            "OCR complete (%d chars, confidence=%.2f).",
            len(raw_text),
            ocr_confidence or 0.0,
        )
    finally:
        # Always remove the temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    # ── Stage 2: NER ─────────────────────────────────────────────────────────
    raw_entities = _run_ner(raw_text)
    logger.info("NER returned %d raw entities.", len(raw_entities))

    # ── Stage 3: Rule-Based Post-Processing ──────────────────────────────────
    rule_output = _run_rules(raw_entities, raw_text)

    structured_entities = rule_output.get("entities", {})
    validation_flags    = rule_output.get("validation_flags", [])

    # ── Build response ────────────────────────────────────────────────────────
    entities_schema = EntitiesSchema(
        parties          = structured_entities.get("parties", []),
        effective_date   = structured_entities.get("effective_date"),
        termination_date = structured_entities.get("termination_date"),
        total_amount     = structured_entities.get("total_amount"),
        jurisdiction     = structured_entities.get("jurisdiction"),
    )

    processing_time_ms = round((time.time() - t_start) * 1000, 2)

    logger.info(
        "Extraction complete for '%s' in %.0f ms. Flags: %s",
        file.filename,
        processing_time_ms,
        validation_flags or "none",
    )

    return ExtractionResponse(
        document_id        = file.filename,
        processing_time_ms = processing_time_ms,
        entities           = entities_schema,
        validation_flags   = validation_flags,
        ocr_confidence     = ocr_confidence,
    )