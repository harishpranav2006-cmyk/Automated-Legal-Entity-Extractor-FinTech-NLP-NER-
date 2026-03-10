"""
train_spacy.py
Owner: Akshada
Task 2, Week 2–3 — NER Model Training

Train a custom spaCy NER model on Harish's annotated legal contract data.

Entity labels to learn:
    PARTY, DATE, AMOUNT, JURISDICTION

Input:  data/annotated/train.spacy  (converted by Harish's annotation_converter.py)
Output: models/spacy_ner/           (saved best model)
"""

# TODO (Akshada): pip install spacy && python -m spacy download en_core_web_sm
# Run training via spaCy CLI (recommended):
#   python -m spacy train config/model_config.cfg --output models/spacy_ner/


def train(train_data_path: str, dev_data_path: str, output_dir: str) -> None:
    """
    Train a custom spaCy NER model.

    Args:
        train_data_path: Path to train.spacy DocBin file.
        dev_data_path:   Path to dev.spacy DocBin file.
        output_dir:      Directory to save the best model.
    """
    # TODO (Akshada):
    # 1. Load base model: spacy.load("en_core_web_sm")
    # 2. Add 'ner' pipe with labels: PARTY, DATE, AMOUNT, JURISDICTION
    # 3. Load DocBin files and convert to (text, annotations) examples
    # 4. Train using nlp.begin_training() update loop (or spaCy CLI config)
    # 5. Evaluate on dev set each epoch; save best model to output_dir
    pass


if __name__ == "__main__":
    train(
        train_data_path="data/annotated/train.spacy",
        dev_data_path="data/annotated/dev.spacy",
        output_dir="models/spacy_ner/"
    )
