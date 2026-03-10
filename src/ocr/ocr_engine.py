import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"E:\education\infotact\week 2\Tesseract-OCR\tesseract.exe"


def extract_page(page_image) -> str:
    """
    Run Tesseract OCR on a single page image.
    """

    img = np.array(page_image)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    text = pytesseract.image_to_string(thresh, config="--oem 3 --psm 6")

    return text


def extract_text(pdf_path: str) -> str:
    """
    Extract text from PDF using OCR.
    """

    pages = convert_from_path(
    pdf_path,
    dpi=300,
    poppler_path=r"E:\infotact\poppler-25.12.0\Library\bin"
)


    full_text = ""

    for page in pages:
        page_text = extract_page(page)
        full_text += page_text + "\n"

    return full_text