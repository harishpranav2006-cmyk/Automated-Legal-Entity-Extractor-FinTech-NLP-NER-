"""
extract.py
Owner: Krutika
Task 4, Week 4 — /extract Endpoint

Wires the full pipeline: PDF upload → OCR → NER → Rules → JSON response.

POST /extract
    Request:  multipart/form-data with field "file" (PDF)
    Response: ExtractionResponse JSON
"""

from fastapi import APIRouter, UploadFile, File

# TODO (Krutika): Import modules once they are implemented by Harish and Akshada
# from src.ocr.ocr_engine import extract_text
# from src.ner.predictor import predict
# from src.rules.rule_engine import apply_rules
# from api.schemas import ExtractionResponse

router = APIRouter()


@router.post("/extract", tags=["Extraction"])
async def extract_entities(file: UploadFile = File(...)):
    """
    Extract structured legal entities from an uploaded PDF contract.

    Pipeline:
        1. Save uploaded PDF to a temp file
        2. Run OCR: ocr_engine.extract_text(pdf_path) → raw text
        3. Run NER: predictor.predict(text)            → raw entities list
        4. Apply rules: rule_engine.apply_rules(entities, text) → structured dict
        5. Return ExtractionResponse JSON

    Returns:
        ExtractionResponse with entities, validation_flags, ocr_confidence.
    """
    # TODO (Krutika):
    # 1. Write file.file contents to a temp path (use tempfile.NamedTemporaryFile)
    # 2. Record start time with time.time()
    # 3. Call extract_text(tmp_path) — returns plain text str
    # 4. Call predict(text) — returns list[dict] of raw entities
    # 5. Call apply_rules(entities, text) — returns structured + validated dict
    # 6. Compute processing_time_ms
    # 7. Build and return ExtractionResponse(...)
    pass
