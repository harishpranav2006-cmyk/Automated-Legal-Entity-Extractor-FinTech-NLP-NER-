"""
pdf_loader.py
Owner: Harish
Task 1, Week 1 — OCR Pipeline

Detects whether a PDF is text-based or image-based and routes accordingly.
- Text-based PDFs: extract text directly using PyMuPDF (fitz)
- Image-based PDFs: pass pages to ocr_engine.py for Tesseract OCR
"""

# TODO (Harish): Install dependencies
# pip install PyMuPDF pdf2image pytesseract Pillow


def load_pdf(pdf_path: str) -> str:
    """
    Load a PDF and return its full text content.

    Args:
        pdf_path: Absolute path to the PDF file.

    Returns:
        Extracted text as a single string.
    """
    # TODO (Harish):
    # 1. Open PDF with fitz (PyMuPDF)
    # 2. For each page, check if it has an embedded text layer
    #    - If yes → extract text directly with page.get_text()
    #    - If no  → call ocr_engine.extract_page(page) for OCR
    # 3. Concatenate all page texts and return
    pass
