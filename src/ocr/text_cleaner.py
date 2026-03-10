import re

def clean_text(text: str) -> str:
    """
    Clean OCR output text.
    """

    if text is None:
        return ""

    # remove multiple spaces
    text = re.sub(r"\s+", " ", text)

    # fix common OCR mistake
    text = text.replace(" rn ", " m ")

    # remove page numbers
    text = re.sub(r"\bPage \d+\b", "", text)

    return text.strip()