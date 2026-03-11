"""
run_training.py — Training bootstrap script
Adds D:\pylibs to sys.path before importing anything, then trains the NER model.
Run: python run_training.py
"""
import sys
import os

# Add D:\pylibs to path so spaCy is findable
_extra = r"D:\pylibs"
if os.path.isdir(_extra) and _extra not in sys.path:
    sys.path.insert(0, _extra)

# Now safe to import spaCy
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

TRAIN_JSONL = Path("data/annotated/train.jsonl")
DEV_JSONL   = Path("data/annotated/dev.jsonl")
MODEL_OUT   = Path("models/spacy_ner")
LABELS      = ["PARTY", "DATE", "AMOUNT", "JURISDICTION"]
MAX_EPOCHS  = 30
PATIENCE    = 5
BATCH_SIZE  = 4
DROPOUT     = 0.3
LEARN_RATE  = 0.001


def load_jsonl_to_docbin(jsonl_path, nlp):
    db      = DocBin()
    skipped = 0
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            record   = json.loads(line)
            text     = record.get("text", "")
            entities = record.get("entities", [])
            doc      = nlp.make_doc(text)
            spans    = []
            for start, end, label in entities:
                if label not in LABELS:
                    continue
                span = doc.char_span(start, end, label=label, alignment_mode="expand")
                if span is None:
                    skipped += 1
                    continue
                spans.append(span)
            doc.ents = filter_spans(spans)
            db.add(doc)
    logger.info(f"Loaded '{jsonl_path.name}': {len(db)} docs | {skipped} spans skipped.")
    return db


def train():
    # Try en_core_web_sm first, fall back to blank model
    try:
        nlp = spacy.load("en_core_web_sm")
        logger.info("Using en_core_web_sm base model.")
    except OSError:
        logger.warning("en_core_web_sm not found — using blank English model.")
        nlp = spacy.blank("en")

    # Add NER pipe
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")

    for label in LABELS:
        ner.add_label(label)

    # Disable other pipes
    other_pipes = [p for p in nlp.pipe_names if p != "ner"]
    disabled = nlp.disable_pipes(*other_pipes)

    # Load data
    train_db   = load_jsonl_to_docbin(TRAIN_JSONL, nlp)
    dev_db     = load_jsonl_to_docbin(DEV_JSONL, nlp)
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

    optimizer        = nlp.initialize(get_examples=lambda: make_examples(train_docs))
    optimizer.learn_rate = LEARN_RATE

    best_f1       = 0.0
    patience_left = PATIENCE

    logger.info(f"Training: {len(train_docs)} train | {len(dev_docs)} dev | "
                f"epochs={MAX_EPOCHS} batch={BATCH_SIZE}")

    for epoch in range(1, MAX_EPOCHS + 1):
        examples = make_examples(train_docs)
        random.shuffle(examples)
        losses   = {}
        batches  = [examples[i:i+BATCH_SIZE] for i in range(0, len(examples), BATCH_SIZE)]
        for batch in batches:
            nlp.update(batch, drop=DROPOUT, losses=losses, sgd=optimizer)

        dev_examples = make_examples(dev_docs)
        scores       = nlp.evaluate(dev_examples)
        f1           = scores.get("ents_f", 0.0)
        prec         = scores.get("ents_p", 0.0)
        rec          = scores.get("ents_r", 0.0)

        logger.info(
            f"Epoch {epoch:02d} | Loss={losses.get('ner',0):.2f} | "
            f"P={prec:.3f} R={rec:.3f} F1={f1:.3f}"
        )

        if f1 > best_f1:
            best_f1       = f1
            patience_left = PATIENCE
            MODEL_OUT.mkdir(parents=True, exist_ok=True)
            nlp.to_disk(MODEL_OUT)
            logger.info(f"  ✅ Best model saved → {MODEL_OUT} (F1={best_f1:.3f})")
        else:
            patience_left -= 1
            if patience_left == 0:
                logger.info(f"Early stopping at epoch {epoch}.")
                break

    logger.info(f"Training done. Best dev F1: {best_f1:.3f}")


if __name__ == "__main__":
    train()
