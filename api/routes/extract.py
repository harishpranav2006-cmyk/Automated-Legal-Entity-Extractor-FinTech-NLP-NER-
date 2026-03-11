"""
extract.py
Owner: Krutika
Task 4, Week 4 — /extract Endpoint

Wires the full pipeline: PDF upload → OCR → NER → Rules → JSON response.

POST /extract
    Request:  multipart/form-data with field "file" (PDF)
    Response: ExtractionResponse JSON
"""

"""
evaluate.py — Akshada
Evaluates the trained spaCy NER model on dev.jsonl.
Reports per-entity F1, Precision, Recall using seqeval.

Usage:
    python src/ner/evaluate.py
"""

import json
import logging
from pathlib import Path

import spacy
from seqeval.metrics import (
    f1_score,
    precision_score,
    recall_score,
    classification_report
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Paths ─────────────────────────────────────────────────────────────────────
MODEL_PATH   = Path("models/spacy_ner")
DEV_JSONL    = Path("data/annotated/dev.jsonl")
REPORT_PATH  = Path("reports/evaluation_report.txt")

LABELS = ["PARTY", "DATE", "AMOUNT", "JURISDICTION"]

# Target F1 thresholds (from project plan)
TARGET_F1 = {
    "DATE":         0.90,
    "AMOUNT":       0.90,
    "PARTY":        0.80,
    "JURISDICTION": 0.75,
}


# ─── Helpers ──────────────────────────────────────────────────────────────────
def load_dev_data(jsonl_path: Path) -> list[dict]:
    """Loads dev JSONL records: [{text, entities: [[start,end,label], ...]}, ...]"""
    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    logger.info(f"Loaded {len(records)} dev records from {jsonl_path}")
    return records


def char_spans_to_bio_tags(text: str, entities: list, doc) -> list[str]:
    """
    Converts character-level entity spans to token-level BIO tags
    aligned with spaCy tokenisation of `doc`.
    """
    # Map each character position to its entity label
    char_label = ["O"] * len(text)
    for start, end, label in entities:
        if label not in LABELS:
            continue
        char_label[start] = f"B-{label}"
        for i in range(start + 1, end):
            char_label[i] = f"I-{label}"

    bio = []
    for token in doc:
        bio.append(char_label[token.idx] if token.idx < len(char_label) else "O")
    return bio


def ents_to_bio_tags(doc) -> list[str]:
    """Converts spaCy doc.ents predictions to token-level BIO tags."""
    bio = ["O"] * len(doc)
    for ent in doc.ents:
        bio[ent.start] = f"B-{ent.label_}"
        for i in range(ent.start + 1, ent.end):
            bio[i] = f"I-{ent.label_}"
    return bio


# ─── Main Evaluation ──────────────────────────────────────────────────────────
def evaluate():
    # 1. Load model
    if not MODEL_PATH.exists():
        logger.error(f"Model not found at {MODEL_PATH}. Run train_spacy.py first.")
        return

    logger.info(f"Loading model from {MODEL_PATH}")
    nlp = spacy.load(MODEL_PATH)

    # 2. Load dev data
    records = load_dev_data(DEV_JSONL)

    y_true = []
    y_pred = []

    for record in records:
        text     = record.get("text", "")
        entities = record.get("entities", [])

        doc_ref  = nlp.make_doc(text)       # Tokenise (no prediction)
        doc_pred = nlp(text)                 # Full prediction

        true_tags = char_spans_to_bio_tags(text, entities, doc_ref)
        pred_tags = ents_to_bio_tags(doc_pred)

        # Align lengths (should match since same tokeniser)
        min_len = min(len(true_tags), len(pred_tags))
        y_true.append(true_tags[:min_len])
        y_pred.append(pred_tags[:min_len])

    # 3. Compute metrics
    logger.info("Computing evaluation metrics...")

    overall_f1   = f1_score(y_true, y_pred)
    overall_prec = precision_score(y_true, y_pred)
    overall_rec  = recall_score(y_true, y_pred)
    report       = classification_report(y_true, y_pred, digits=4)

    # 4. Display results
    separator = "=" * 60
    print(f"\n{separator}")
    print("  LexiScan Auto — NER Evaluation Report")
    print(separator)
    print(f"  Model    : {MODEL_PATH}")
    print(f"  Dev Set  : {DEV_JSONL}  ({len(records)} samples)")
    print(separator)
    print(report)
    print(separator)
    print(f"  Overall Precision : {overall_prec:.4f}")
    print(f"  Overall Recall    : {overall_rec:.4f}")
    print(f"  Overall F1        : {overall_f1:.4f}")
    print(separator)

    # 5. Per-entity target check
    print("\n  Target F1 Check:")
    all_passed = True
    for label, target in TARGET_F1.items():
        # Extract per-label F1 from seqeval classification_report (parse lines)
        label_f1 = _extract_label_f1(y_true, y_pred, label)
        status   = "✅ PASS" if label_f1 >= target else "❌ FAIL"
        if label_f1 < target:
            all_passed = False
        print(f"    {label:<15} F1={label_f1:.4f}  Target≥{target:.2f}  {status}")

    print(separator)
    print(f"  Final Status: {'✅ ALL TARGETS MET' if all_passed else '⚠️  SOME TARGETS NOT MET'}")
    print(separator)

    # 6. Save report to file
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write(f"LexiScan Auto — NER Evaluation Report\n")
        f.write(f"Model: {MODEL_PATH}\n")
        f.write(f"Dev Set: {DEV_JSONL} ({len(records)} samples)\n\n")
        f.write(report)
        f.write(f"\nOverall Precision : {overall_prec:.4f}\n")
        f.write(f"Overall Recall    : {overall_rec:.4f}\n")
        f.write(f"Overall F1        : {overall_f1:.4f}\n\n")
        f.write("Target F1 Check:\n")
        for label, target in TARGET_F1.items():
            label_f1 = _extract_label_f1(y_true, y_pred, label)
            status   = "PASS" if label_f1 >= target else "FAIL"
            f.write(f"  {label:<15} F1={label_f1:.4f}  Target>={target:.2f}  {status}\n")

    logger.info(f"Report saved to {REPORT_PATH}")
    return overall_f1


def _extract_label_f1(y_true, y_pred, label: str) -> float:
    """Extracts F1 score for a specific entity label using seqeval."""
    from seqeval.metrics import f1_score as seq_f1

    # Filter sequences to only the target label
    def filter_tags(seq):
        return [t if label in t else "O" for t in seq]

    y_true_f = [filter_tags(seq) for seq in y_true]
    y_pred_f = [filter_tags(seq) for seq in y_pred]

    try:
        return seq_f1(y_true_f, y_pred_f, zero_division=0)
    except Exception:
        return 0.0


if __name__ == "__main__":
    evaluate()