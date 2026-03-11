"""
predictor.py — Akshada
Inference wrapper for the trained spaCy NER model.

This is the CRITICAL handoff module to Krutika's rule-based layer.
Interface contract:
    predict(text: str) -> list[dict]
    Each dict: {"text": str, "label": str, "start": int, "end": int}

Usage:
    from src.ner.predictor import predict
    entities = predict("ABC Corp signed a deal worth $5,000,000 on January 15, 2024.")
"""

import logging
from pathlib import Path
from typing import Optional

import spacy

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH = Path("models/spacy_ner")
LABELS     = {"PARTY", "DATE", "AMOUNT", "JURISDICTION"}

# ─── Singleton Model Loader ────────────────────────────────────────────────────
_nlp_model = None


def _load_model():
    """Loads and caches the spaCy model (singleton pattern)."""
    global _nlp_model
    if _nlp_model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model not found at '{MODEL_PATH}'. "
                "Please run src/ner/train_spacy.py first."
            )
        logger.info(f"Loading NER model from {MODEL_PATH}...")
        _nlp_model = spacy.load(MODEL_PATH)
        logger.info("NER model loaded successfully.")
    return _nlp_model


# ─── Public Interface ─────────────────────────────────────────────────────────
def predict(text: str) -> list[dict]:
    """
    Runs NER inference on input text and returns structured entity list.

    Args:
        text (str): Clean extracted text from OCR pipeline.

    Returns:
        list[dict]: Each entity as:
            {
                "text":  str,   # Raw matched text e.g. "ABC Corp"
                "label": str,   # Entity type: PARTY | DATE | AMOUNT | JURISDICTION
                "start": int,   # Character start offset
                "end":   int    # Character end offset
            }

    Example:
        >>> predict("ABC Corp agreed to pay $5,000,000 by January 15, 2024.")
        [
            {"text": "ABC Corp",      "label": "PARTY",  "start": 0,  "end": 8},
            {"text": "$5,000,000",    "label": "AMOUNT", "start": 22, "end": 32},
            {"text": "January 15, 2024", "label": "DATE","start": 36, "end": 52}
        ]
    """
    if not text or not text.strip():
        logger.warning("predict() called with empty text — returning []")
        return []

    nlp = _load_model()
    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        if ent.label_ not in LABELS:
            continue
        entities.append({
            "text":  ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end":   ent.end_char,
        })

    logger.debug(f"predict(): found {len(entities)} entities in {len(text)}-char text.")
    return entities


def predict_batch(texts: list[str]) -> list[list[dict]]:
    """
    Batch inference for multiple documents.

    Args:
        texts (list[str]): List of document texts.

    Returns:
        list[list[dict]]: Entity list per document.
    """
    if not texts:
        return []

    nlp = _load_model()
    results = []

    for doc in nlp.pipe(texts, batch_size=16):
        entities = [
            {
                "text":  ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end":   ent.end_char,
            }
            for ent in doc.ents
            if ent.label_ in LABELS
        ]
        results.append(entities)

    return results


def get_model_info() -> dict:
    """Returns metadata about the loaded model."""
    nlp = _load_model()
    return {
        "model_path": str(MODEL_PATH),
        "pipeline":   nlp.pipe_names,
        "labels":     list(nlp.get_pipe("ner").labels) if "ner" in nlp.pipe_names else [],
        "spacy_version": spacy.__version__,
    }


# ─── Quick Self-Test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_text = (
        "This Agreement is entered into between ABC Corporation and XYZ Pvt Ltd "
        "on January 15, 2024, for a total consideration of $5,000,000.00, "
        "governed by the laws of the State of New York."
    )

    print("Running predictor self-test...")
    print(f"Input: {sample_text}\n")

    results = predict(sample_text)
    print(f"Entities found: {len(results)}")
    for e in results:
        print(f"  [{e['label']:15}] '{e['text']}'  (chars {e['start']}–{e['end']})")

    print("\nModel info:")
    for k, v in get_model_info().items():
        print(f"  {k}: {v}")