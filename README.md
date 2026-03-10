# LexiScan Auto

**Automated Legal Entity Extractor** — FinTech NLP/NER pipeline for extracting structured entities from scanned legal contracts.

> **Team:** Krutika (Team Leader) · Harish · Akshada  
> **Duration:** 4 Weeks

---

## Project Architecture

```
PDF Input
  │
  ▼
[Harish]  OCR Pipeline (Tesseract + pdf2image)    → Clean Text
  ▼
[Akshada] NER Model (spaCy)                       → Raw Entities
  ▼
[Krutika] Rule-Based Post-Processing Layer         → Validated Entities
  ▼
[Akshada + Krutika] FastAPI + Docker              → JSON Response
```

Extracted entity types: **PARTY · DATE · AMOUNT · JURISDICTION**

---

## Project Structure

```
lexiscan-auto/
├── api/                        # FastAPI application (Akshada + Krutika)
│   ├── main.py
│   ├── schemas.py
│   └── routes/extract.py
├── src/
│   ├── ocr/                    # OCR pipeline (Harish)
│   ├── ner/                    # NER model (Akshada)
│   ├── rules/                  # Rule-based layer (Krutika)
│   └── data/                   # Annotation tools (Harish)
├── data/
│   ├── raw/                    # Original PDFs
│   ├── processed/              # OCR output text
│   └── annotated/              # BIO-tagged training data
├── models/spacy_ner/           # Trained NER model
├── tests/                      # Unit + E2E tests
├── config/model_config.cfg     # spaCy training config
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Docker Desktop
- Tesseract OCR binary → [Installation Guide](https://github.com/UB-Mannheim/tesseract/wiki)

### Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Run Locally (Development)
```bash
uvicorn api.main:app --reload
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Run with Docker
```bash
docker-compose up --build
# API at http://localhost:8000
```

### Test with a Sample PDF
```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@sample_contract.pdf"
```

---

## API Response Example

```json
{
  "document_id": "contract_001.pdf",
  "processing_time_ms": 1240,
  "entities": {
    "parties": ["ABC Corporation", "XYZ Pvt Ltd"],
    "effective_date": "2024-01-15",
    "termination_date": "2026-01-14",
    "total_amount": "$5,000,000.00",
    "jurisdiction": "State of New York"
  },
  "validation_flags": [],
  "ocr_confidence": 0.91
}
```

---

## Running Tests

```bash
pytest tests/ -v --tb=short
```

---

## Task Ownership

| Module | Owner | Week |
|--------|-------|------|
| `src/ocr/` | Harish | Week 1 |
| `data/annotated/` | Harish | Week 2 |
| `src/ner/` | Akshada | Week 3 |
| `src/rules/` | Krutika | Week 2–3 |
| `api/` + Docker | Akshada + Krutika | Week 4 |
