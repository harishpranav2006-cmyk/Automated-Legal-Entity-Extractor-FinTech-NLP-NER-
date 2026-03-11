"""
annotation_converter.py
Owner: Harish
Task 1, Week 2 — Data Annotation

Converts Doccano JSONL export to spaCy-compatible DocBin binary format.

Doccano JSONL format (input):
    {"id": 1, "text": "ABC Corp agrees...", "label": [[0, 8, "PARTY"], [45, 60, "DATE"]]}
  OR
    {"text": "ABC Corp agrees...", "entities": [[0, 8, "PARTY"], [45, 60, "DATE"]]}

spaCy DocBin format (output):
    Binary .spacy file readable by spacy.tokens.DocBin

Usage:
    python src/data/annotation_converter.py
    (or import and call convert_doccano_to_spacy() directly)
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

LABELS = {"PARTY", "DATE", "AMOUNT", "JURISDICTION"}


def convert_doccano_to_spacy(input_jsonl: str, output_spacy: str) -> int:
    """
    Convert Doccano JSONL annotations to spaCy DocBin binary format.

    Args:
        input_jsonl:  Path to input .jsonl file.
        output_spacy: Output path for the .spacy DocBin file.

    Returns:
        Number of successfully converted documents.
    """
    try:
        import spacy
        from spacy.tokens import DocBin
        from spacy.util import filter_spans
    except ImportError:
        logger.error("spaCy not installed. Run: pip install spacy")
        return 0

    input_path  = Path(input_jsonl)
    output_path = Path(output_spacy)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load spaCy blank model for tokenisation only
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.warning("en_core_web_sm not found, using blank English model.")
        nlp = spacy.blank("en")

    db      = DocBin()
    total   = 0
    skipped = 0

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)
            text   = record.get("text", "")

            # Support both Doccano formats: "label" and "entities"
            raw_ents = record.get("entities", record.get("label", []))

            doc   = nlp.make_doc(text)
            spans = []

            for ann in raw_ents:
                # Handle [start, end, label] list or {"start":…,"end":…,"label":…} dict
                if isinstance(ann, (list, tuple)) and len(ann) >= 3:
                    start, end, label = int(ann[0]), int(ann[1]), str(ann[2])
                elif isinstance(ann, dict):
                    start = int(ann.get("start_offset", ann.get("start", 0)))
                    end   = int(ann.get("end_offset",   ann.get("end",   0)))
                    label = str(ann.get("label", ""))
                else:
                    continue

                if label not in LABELS:
                    continue

                span = doc.char_span(start, end, label=label, alignment_mode="expand")
                if span is None:
                    logger.warning(
                        f"Line {line_num}: Cannot align [{start}:{end}] "
                        f"'{text[start:end]}' — span skipped."
                    )
                    skipped += 1
                    continue
                spans.append(span)

            doc.ents = filter_spans(spans)
            db.add(doc)
            total += 1

    db.to_disk(output_path)
    logger.info(
        f"Converted {total} docs → '{output_path}'  ({skipped} spans skipped)"
    )
    return total


if __name__ == "__main__":
    convert_doccano_to_spacy(
        input_jsonl="data/annotated/train.jsonl",
        output_spacy="data/annotated/train.spacy"
    )
    convert_doccano_to_spacy(
        input_jsonl="data/annotated/dev.jsonl",
        output_spacy="data/annotated/dev.spacy"
    )
    logger.info("Annotation conversion complete.")
