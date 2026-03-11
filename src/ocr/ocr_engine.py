"""
ocr_engine.py
Owner: Harish
Task 1, Week 1 — OCR Pipeline

Core OCR wrapper. Tries PyMuPDF text extraction first (fast, for text-based PDFs),
then falls back to Tesseract OCR via pdf2image (for scanned/image PDFs).

Interface contract:
    extract_text(pdf_path: str) -> str
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── Optional heavy imports (graceful degradation) ────────────────────────────
try:
    import fitz  # PyMuPDF
    _FITZ_AVAILABLE = True
except ImportError:
    _FITZ_AVAILABLE = False
    logger.warning("PyMuPDF (fitz) not installed — direct text extraction unavailable.")

try:
    import pytesseract
    import numpy as np
    from PIL import Image
    _TESSERACT_AVAILABLE = True

    # Auto-detect Tesseract on common Windows locations
    import shutil, sys
    _tess_cmd = shutil.which("tesseract")
    if _tess_cmd:
        pytesseract.pytesseract.tesseract_cmd = _tess_cmd
    else:
        # Common Windows install paths
        _candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"E:\education\infotact\week 2\Tesseract-OCR\tesseract.exe",
        ]
        for path in _candidates:
            if Path(path).exists():
                pytesseract.pytesseract.tesseract_cmd = path
                break

except ImportError:
    _TESSERACT_AVAILABLE = False
    logger.warning("pytesseract / Pillow not installed — Tesseract OCR unavailable.")

try:
    from pdf2image import convert_from_path
    # Auto-detect poppler on common paths
    import shutil as _shutil
    _POPPLER_PATH = None
    _poppler_cmd = _shutil.which("pdftoppm")
    if not _poppler_cmd:
        _poppler_candidates = [
            r"C:\poppler\Library\bin",
            r"C:\Program Files\poppler\Library\bin",
            r"C:\Users\kruti\poppler\bin",
            r"E:\infotact\poppler-25.12.0\Library\bin",
        ]
        for p in _poppler_candidates:
            if Path(p).exists():
                _POPPLER_PATH = p
                break
    _PDF2IMAGE_AVAILABLE = True
except ImportError:
    _PDF2IMAGE_AVAILABLE = False
    _POPPLER_PATH = None
    logger.warning("pdf2image not installed — image-PDF OCR unavailable.")


# ─── Text extraction via PyMuPDF ──────────────────────────────────────────────

def _extract_with_pymupdf(pdf_path: str) -> str:
    """Extract embedded text from a text-PDF using PyMuPDF."""
    if not _FITZ_AVAILABLE:
        return ""
    try:
        doc = fitz.open(pdf_path)
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())
        doc.close()
        return "\n".join(pages_text)
    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed: {e}")
        return ""


def _has_text_layer(pdf_path: str) -> bool:
    """Return True if PDF has embedded selectable text."""
    if not _FITZ_AVAILABLE:
        return False
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            if page.get_text().strip():
                doc.close()
                return True
        doc.close()
        return False
    except Exception:
        return False


# ─── OCR via Tesseract ────────────────────────────────────────────────────────

def _preprocess_image(pil_image) -> "Image.Image":
    """Convert PIL image to grayscale for better OCR accuracy."""
    return pil_image.convert("L")  # Grayscale


def _extract_with_tesseract(pdf_path: str) -> str:
    """Extract text from image-PDF using pdf2image + Tesseract."""
    if not _PDF2IMAGE_AVAILABLE or not _TESSERACT_AVAILABLE:
        logger.warning("Tesseract/pdf2image not available — returning empty text.")
        return ""
    try:
        kwargs = {"dpi": 300}
        if _POPPLER_PATH:
            kwargs["poppler_path"] = _POPPLER_PATH

        pages = convert_from_path(pdf_path, **kwargs)
        full_text = ""
        for page_img in pages:
            processed = _preprocess_image(page_img)
            text = pytesseract.image_to_string(processed, config="--oem 3 --psm 6")
            full_text += text + "\n"
        return full_text
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        return ""


# ─── Public Interface ─────────────────────────────────────────────────────────

def extract_text(pdf_path: str) -> str:
    """
    Extract plain text from a PDF file.

    Strategy:
        1. If the PDF has embedded text (text-based PDF) → extract directly
           with PyMuPDF (fast, no OCR needed).
        2. If image-based → convert pages to images → run Tesseract OCR.
        3. If all methods fail → returns empty string (never raises).

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        Extracted plain text as a single string. Never raises.
    """
    pdf_path = str(pdf_path)
    logger.info(f"extract_text() called for: {pdf_path}")

    if not Path(pdf_path).exists():
        logger.error(f"PDF not found: {pdf_path}")
        return ""

    # Try fast text extraction first
    if _has_text_layer(pdf_path):
        logger.info("Text layer detected — using PyMuPDF direct extraction.")
        text = _extract_with_pymupdf(pdf_path)
        if text.strip():
            return text.strip()

    # Fall back to Tesseract OCR
    logger.info("No text layer — falling back to Tesseract OCR.")
    text = _extract_with_tesseract(pdf_path)
    return text.strip()