"""
annotation_converter.py
Owner: Harish
Task 1, Week 2 — Data Annotation

Converts Doccano JSONL export to spaCy-compatible DocBin binary format.

Doccano JSONL format (input):
    {"id": 1, "text": "ABC Corp agrees...", "label": [[0, 8, "PARTY"], [45, 60, "DATE"]]}

spaCy DocBin format (output):
    Binary .spacy file readable by spacy.tokens.DocBin

Usage:
    python annotation_converter.py
    (or import and call convert_doccano_to_spacy() directly)
"""

# TODO (Harish): pip install spacy && python -m spacy download en_core_web_sm


def convert_doccano_to_spacy(input_jsonl: str, output_spacy: str) -> int:
    """
    Convert Doccano JSONL annotations to spaCy DocBin binary format.

    Args:
        input_jsonl:  Path to Doccano exported .jsonl file.
        output_spacy: Output path for the .spacy DocBin file.

    Returns:
        Number of successfully converted documents.
    """
    # TODO (Harish):
    # 1. Load spaCy model for tokenization (en_core_web_sm)
    # 2. Read each line from input_jsonl as JSON
    # 3. For each entry: create a spaCy Doc, set entity spans from label list
    # 4. Handle misaligned spans (char_span returns None) — warn and skip
    # 5. Handle overlapping spans — warn and skip whole doc
    # 6. Add valid docs to DocBin and save to output_spacy
    pass


if __name__ == "__main__":
    convert_doccano_to_spacy(
        input_jsonl="data/annotated/train.jsonl",
        output_spacy="data/annotated/train.spacy"
    )
    convert_doccano_to_spacy(
        input_jsonl="data/annotated/dev.jsonl",
        output_spacy="data/annotated/dev.spacy"
    )
