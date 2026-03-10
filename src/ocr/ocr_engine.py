"""
ocr_engine.py
Owner: Harish
Task 1, Week 1 — OCR Pipeline

Core Tesseract OCR wrapper.
Converts PDF pages to images and extracts text using pytesseract.

Pipeline:
    PDF page → 300 DPI image → grayscale → binarize (Otsu) → deskew → Tesseract → text
"""

# TODO (Harish): Install dependencies
# pip install pdf2image pytesseract Pillow
# Also install Tesseract binary: https://github.com/UB-Mannheim/tesseract/wiki


def extract_text(pdf_path: str) -> str:
    """
    Run OCR on an image-based PDF and return the extracted text.

    This is the primary handoff function — Akshada will call this directly.

    Args:
        pdf_path: Absolute path to the PDF file.

    Returns:
        Full extracted text as a single string.
    """
    # TODO (Harish):
    # 1. Convert PDF pages to 300 DPI images using pdf2image.convert_from_path()
    # 2. For each image:
    #    a. Convert to grayscale
    #    b. Apply Otsu binarization (cv2.threshold or PIL)
    #    c. Deskew if needed
    #    d. Run pytesseract.image_to_string(img, config='--oem 3 --psm 6')
    # 3. Concatenate page texts and return
    pass


def extract_page(page_image) -> str:
    """
    Run Tesseract OCR on a single PIL image (one PDF page).

    Args:
        page_image: A PIL.Image object of the page.

    Returns:
        Extracted text for that page.
    """
    # TODO (Harish): Apply preprocessing then call pytesseract
    pass
