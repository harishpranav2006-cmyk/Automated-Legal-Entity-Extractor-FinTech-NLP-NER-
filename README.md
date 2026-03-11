# LexiScan Auto — Automated Legal Entity Extractor

> **FinTech NLP/NER Pipeline** | Extract parties, dates, amounts, and jurisdictions from scanned contract PDFs.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-green)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://www.docker.com/)
[![spaCy](https://img.shields.io/badge/spaCy-3.7%2B-orange)](https://spacy.io/)

---

## Overview

**LexiScan Auto** is an end-to-end NLP pipeline that:
1. **OCR** — Extracts text from scanned/text PDFs (PyMuPDF + Tesseract)
2. **NER** — Identifies legal entities (spaCy custom model)
3. **Rule Engine** — Normalises and validates extracted entities
4. **REST API** — Serves results via a FastAPI endpoint

**Entity Types Extracted**

| Entity | Example | Normalised Form |
|---|---|---|
| `PARTY` | `ABC Corporation` | Canonical long form |
| `DATE` | `15th of January 2024` | `2024-01-15` (ISO 8601) |
| `AMOUNT` | `USD 2.5M` | `$2,500,000.00` |
| `JURISDICTION` | `State of New York` | Raw text |

---

## Team

| Member | Task |
|---|---|
| **Harish** | Task 1 — OCR Pipeline + Data Annotation |
| **Akshada** | Task 2 — NER Model (spaCy / Bi-LSTM) + Docker setup |
| **Krutika** | Task 3 — Rule-Based Layer + Task 4 — API wiring & E2E tests |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- (For local dev) Python 3.10+, `pip install -r requirements.txt`

---

## Quick Start (Docker)

### 1 — Build and launch

```bash
docker-compose up --build
```

The API starts at **http://localhost:8000**

Interactive docs: **http://localhost:8000/docs**

### 2 — Test with a sample PDF

```bash
curl -X POST "http://localhost:8000/extract" \
     -F "file=@sample_contract.pdf"
```

**Example response:**
```json
{
  "document_id": "sample_contract.pdf",
  "processing_time_ms": 1240,
  "entities": {
    "parties":          ["ABC Corporation", "XYZ Pvt Ltd"],
    "effective_date":   "2024-01-15",
    "termination_date": "2026-01-14",
    "total_amount":     "$5,000,000.00",
    "jurisdiction":     "State of New York"
  },
  "validation_flags": [],
  "ocr_confidence": 0.91
}
```

### 3 — Health check

```bash
curl http://localhost:8000/health
```

---

## Local Development (without Docker)

```bash
# 1. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # baseline spaCy model

# 2. (Optional) Train the NER model
python src/ner/train_spacy.py

# 3. Start the API
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Open docs
# http://localhost:8000/docs
```

---

## Running Tests

```bash
# All unit tests (no Docker required)
pytest tests/test_rules.py -v --tb=short

# End-to-end test (requires docker-compose up first)
pytest tests/test_e2e.py -v --tb=short

# Full suite
pytest tests/ -v --tb=short
```

**Unit test coverage:**

| Module | Tests |
|---|---|
| `date_normalizer` | ISO passthrough, long/short month, slash, ordinal, OCR noise, empty, hyphen |
| `amount_normalizer` | Dollar, USD prefix, million/billion word form, M/B suffix, OCR noise, plain integer |
| `constraint_validator` | Valid contract, termination before effective, far-future date, negative amount, <2 parties |
| `entity_deduplicator` | No overlaps, overlapping spans, near-duplicate parties, empty list |
| `rule_engine` | Full pipeline, constraint violations, OCR text, empty list |
| **Total** | **25 tests** |

---

## Project Structure

```
lexiscan-auto/
├── api/
│   ├── main.py               # FastAPI app entry point
│   ├── schemas.py            # Pydantic request/response models
│   └── routes/
│       └── extract.py        # POST /extract endpoint (OCR→NER→Rules)
├── src/
│   ├── ocr/
│   │   └── ocr_engine.py     # PDF text extraction (Harish)
│   ├── ner/
│   │   ├── train_spacy.py    # Model training (Akshada)
│   │   ├── predictor.py      # predict(text) → entities (Akshada)
│   │   └── evaluate.py       # F1 scoring (Akshada)
│   └── rules/
│       ├── date_normalizer.py      # ISO 8601 date normalisation (Krutika)
│       ├── amount_normalizer.py    # Monetary value normalisation (Krutika)
│       ├── constraint_validator.py # Business rule checks (Krutika)
│       ├── entity_deduplicator.py  # Span deduplication & party merging (Krutika)
│       └── rule_engine.py          # Master orchestrator (Krutika)
├── data/
│   ├── annotated/
│   │   ├── train.jsonl       # Training data (Harish)
│   │   └── dev.jsonl         # Validation data (Harish)
│   └── test/
│       └── held_out_contract.pdf
├── models/
│   └── spacy_ner/            # Trained model output
├── tests/
│   ├── test_rules.py         # Rule-layer unit tests (Krutika)
│   └── test_e2e.py           # End-to-end integration tests (Krutika)
├── config/
│   └── model_config.cfg      # spaCy training config (Akshada)
├── Dockerfile                # Container image (Akshada)
├── docker-compose.yml        # One-command deployment (Akshada)
└── requirements.txt
```

---

## API Reference

### `POST /extract`

| Parameter | Type | Description |
|---|---|---|
| `file` | `UploadFile` | PDF contract (multipart/form-data) |

**Validation rules applied:**
- Termination date must not precede effective date
- Effective date must not be >10 years in the future
- Total amount must be positive
- Contract must have ≥2 identified parties

**Validation flags** are returned in the `validation_flags` array and never block the response.

### `GET /health`

Returns API status and NER model availability.

### `GET /docs`

Interactive Swagger UI.

---

## Stopping the Container

```bash
docker-compose down
```
