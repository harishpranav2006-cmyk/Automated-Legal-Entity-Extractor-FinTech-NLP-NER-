import sys
import os

# add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("Starting OCR test...")

from src.ocr.ocr_engine import extract_text
from src.ocr.text_cleaner import clean_text
from src.ocr.quality_checker import quality_score

pdf_path = r"data/raw/sample_contract.pdf"

print("Running OCR...")

text = extract_text(pdf_path)

cleaned = clean_text(text)

score = quality_score(cleaned)

print("\n--- Extracted Text Preview ---\n")
print(cleaned[:500])

print("\nOCR Quality Score:", score)

with open("data/processed/contract1.txt", "w", encoding="utf-8") as f:
    f.write(cleaned)

print("\nSaved to data/processed/contract1.txt")