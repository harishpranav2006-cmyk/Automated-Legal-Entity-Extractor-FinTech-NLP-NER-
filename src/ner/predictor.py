"""
predictor.py
Owner: Akshada
Task 2, Week 3 — NER Inference

Inference wrapper for the trained NER model.
This is the PRIMARY HANDOFF INTERFACE to Krutika's rule-based layer.

Krutika's rule_engine.py will call:
    from src.ner.predictor import predict
    entities = predict(text)
"""


def predict(text: str) -> list[dict]:
    """
    Run NER on input text and return a list of extracted entities.

    *** THIS INTERFACE IS FIXED — DO NOT CHANGE THE RETURN FORMAT ***
    Krutika's rule_engine depends on this exact structure.

    Args:
        text: Plain text string (output of OCR pipeline).

    Returns:
        List of entity dicts. Each dict has:
            {
                "text":  str,   # The entity surface form, e.g. "ABC Corp"
                "label": str,   # Entity type: PARTY | DATE | AMOUNT | JURISDICTION
                "start": int,   # Start character offset in text
                "end":   int,   # End character offset in text
            }

    Example:
        [
            {"text": "ABC Corp",         "label": "PARTY",        "start": 0,  "end": 8},
            {"text": "January 15, 2024", "label": "DATE",         "start": 45, "end": 61},
            {"text": "$5,000,000",        "label": "AMOUNT",       "start": 80, "end": 90},
            {"text": "State of New York", "label": "JURISDICTION", "start": 100,"end": 118},
        ]
    """
    # TODO (Akshada):
    # 1. Load the trained model from models/spacy_ner/ (load once, cache globally)
    # 2. Run nlp(text) to get a spaCy Doc
    # 3. Iterate doc.ents and build the return list
    pass
