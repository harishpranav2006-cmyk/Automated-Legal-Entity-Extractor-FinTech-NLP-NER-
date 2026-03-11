"""
train_spacy.py — Akshada
Trains a custom spaCy NER model on Harish's annotated JSONL data.
Entities: PARTY, DATE, AMOUNT, JURISDICTION

Usage:
    python src/ner/train_spacy.py
"""

import json
import random
import logging
from pathlib import Path

import spacy
from spacy.tokens import DocBin
from spacy.training import Example
from spacy.util import filter_spans

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Paths ─────────────────────────────────────────────────────────────────────
TRAIN_JSONL = Path("data/annotated/train.jsonl")
DEV_JSONL   = Path("data/annotated/dev.jsonl")
MODEL_OUT   = Path("models/spacy_ner")
BASE_MODEL  = "en_core_web_sm"  # Falls back to blank "en" model if not installed

LABELS = ["PARTY", "DATE", "AMOUNT", "JURISDICTION"]


def load_jsonl_to_docbin(jsonl_path: Path, nlp) -> DocBin:
    """
    Converts Doccano-exported JSONL into spaCy DocBin.

    Expected JSONL format per line:
    {
        "text": "ABC Corp signed on January 15, 2024",
        "entities": [[0, 8, "PARTY"], [19, 36, "DATE"]]
    }
    """
    db = DocBin()
    skipped = 0

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            record   = json.loads(line)
            text     = record.get("text", "")
            entities = record.get("entities", [])

            doc   = nlp.make_doc(text)
            spans = []

            for start, end, label in entities:
                if label not in LABELS:
                    continue
                span = doc.char_span(start, end, label=label, alignment_mode="expand")
                if span is None:
                    logger.warning(
                        f"Line {line_num}: Cannot align [{start}:{end}] "
                        f"'{text[start:end]}' — skipped."
                    )
                    skipped += 1
                    continue
                spans.append(span)

            doc.ents = filter_spans(spans)
            db.add(doc)

    logger.info(f"Loaded '{jsonl_path.name}': {len(db)} docs | {skipped} spans skipped.")
    return db


def train(
    max_epochs: int   = 30,
    patience: int     = 5,
    batch_size: int   = 8,
    dropout: float    = 0.2,
    learn_rate: float = 0.001,
):
    """
    Fine-tunes en_core_web_sm with custom NER labels.
    Saves best model (highest dev F1) to models/spacy_ner/.
    """
    logger.info(f"Loading base model: {BASE_MODEL}")
    try:
        nlp = spacy.load(BASE_MODEL)
    except OSError:
        logger.warning(f"'{BASE_MODEL}' not found — using blank English model.")
        nlp = spacy.blank("en")

    # Disable all pipes except NER during training
    other_pipes = [p for p in nlp.pipe_names if p != "ner"]
    nlp.disable_pipes(*other_pipes)

    # Add / get NER pipe
    ner = nlp.get_pipe("ner") if "ner" in nlp.pipe_names else nlp.add_pipe("ner", last=True)
    for label in LABELS:
        ner.add_label(label)

    # Load annotated data
    train_db   = load_jsonl_to_docbin(TRAIN_JSONL, nlp)
    dev_db     = load_jsonl_to_docbin(DEV_JSONL,   nlp)
    train_docs = list(train_db.get_docs(nlp.vocab))
    dev_docs   = list(dev_db.get_docs(nlp.vocab))

    def make_examples(docs):
        return [
            Example.from_dict(
                doc,
                {"entities": [(e.start_char, e.end_char, e.label_) for e in doc.ents]}
            )
            for doc in docs
        ]

    optimizer = nlp.initialize()
    optimizer.learn_rate = learn_rate

    best_f1       = 0.0
    patience_left = patience

    logger.info(f"Starting training — max_epochs={max_epochs}, patience={patience}, "
                f"batch_size={batch_size}, dropout={dropout}")

    for epoch in range(1, max_epochs + 1):
        examples = make_examples(train_docs)
        random.shuffle(examples)

        losses = {}
        batches = [examples[i:i+batch_size] for i in range(0, len(examples), batch_size)]
        for batch in batches:
            nlp.update(batch, drop=dropout, losses=losses, sgd=optimizer)

        # Evaluate on dev set
        dev_examples = make_examples(dev_docs)
        scores = nlp.evaluate(dev_examples)
        f1     = scores.get("ents_f", 0.0)
        prec   = scores.get("ents_p", 0.0)
        rec    = scores.get("ents_r", 0.0)

        logger.info(
            f"Epoch {epoch:02d} | Loss: {losses.get('ner', 0):.4f} | "
            f"P: {prec:.4f} R: {rec:.4f} F1: {f1:.4f}"
        )

        if f1 > best_f1:
            best_f1       = f1
            patience_left = patience
            MODEL_OUT.mkdir(parents=True, exist_ok=True)
            nlp.to_disk(MODEL_OUT)
            logger.info(f"  ✅ Best model saved → {MODEL_OUT}  (F1={best_f1:.4f})")
        else:
            patience_left -= 1
            logger.info(f"  No improvement. Patience left: {patience_left}")
            if patience_left == 0:
                logger.info(f"Early stopping triggered at epoch {epoch}.")
                break

    logger.info(f"Training complete. Best Dev F1: {best_f1:.4f}")
    logger.info(f"Model saved at: {MODEL_OUT}")


if __name__ == "__main__":
    train()