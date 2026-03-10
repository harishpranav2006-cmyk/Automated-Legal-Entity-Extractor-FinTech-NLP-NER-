"""
evaluate.py
Owner: Akshada
Task 2, Week 3 — Model Evaluation

Evaluates the trained NER model using entity-level F1 scores (via seqeval).

Reports per-entity F1 for: PARTY, DATE, AMOUNT, JURISDICTION
Target metrics:
    DATE         ≥ 0.90
    AMOUNT       ≥ 0.90
    PARTY        ≥ 0.80
    JURISDICTION ≥ 0.75
"""

# TODO (Akshada): pip install seqeval


def evaluate(model_path: str, dev_data_path: str) -> dict:
    """
    Run the trained NER model on dev set and compute F1 scores.

    Args:
        model_path:    Path to the saved spaCy model directory.
        dev_data_path: Path to dev.spacy DocBin file.

    Returns:
        Dict of per-entity F1 scores and overall micro F1.
        Example: {"DATE": 0.92, "AMOUNT": 0.88, "PARTY": 0.81, "micro_f1": 0.87}
    """
    # TODO (Akshada):
    # 1. Load model with spacy.load(model_path)
    # 2. Load dev DocBin and iterate documents
    # 3. Collect true BIO tag sequences and predicted BIO tag sequences
    # 4. Use seqeval.metrics.f1_score() and classification_report()
    # 5. Print report and return scores dict
    pass


if __name__ == "__main__":
    scores = evaluate(
        model_path="models/spacy_ner/",
        dev_data_path="data/annotated/dev.spacy"
    )
    print(scores)
