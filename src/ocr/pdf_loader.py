"""
pdf_loader.py
Owner: Harish
Detect whether a PDF contains embedded text or needs OCR.
"""

import fitz  # PyMuPDF


def has_text_layer(pdf_path: str) -> bool:
    """
    Check if the PDF already contains selectable text.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        True if the PDF contains text, False if OCR is required.
    """

    doc = fitz.open(pdf_path)

    for page in doc:
        text = page.get_text()

        if text.strip():
            return True

    return False