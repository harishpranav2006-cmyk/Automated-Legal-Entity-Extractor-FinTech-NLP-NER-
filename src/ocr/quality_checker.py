import re

def quality_score(text: str) -> float:
    """Calculate OCR text quality score."""

    words = text.split()

    if len(words) == 0:
        return 0.0

    valid_words = []

    for w in words:
        if re.match(r"^[A-Za-z]+$", w):
            valid_words.append(w)

    score = len(valid_words) / len(words)

    return round(score, 2)