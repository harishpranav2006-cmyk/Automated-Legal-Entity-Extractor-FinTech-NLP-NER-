# Dockerfile — Akshada
# Builds the LexiScan Auto API container.
# Includes Tesseract OCR + Poppler (for pdf2image) + all Python deps.

FROM python:3.11-slim

# ── System dependencies ────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ──────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Download spaCy base model ──────────────────────────────────────────────────
RUN python -m spacy download en_core_web_sm

# ── Copy application source ────────────────────────────────────────────────────
COPY . .

# ── Create necessary directories ───────────────────────────────────────────────
RUN mkdir -p data/raw data/processed data/annotated models/spacy_ner reports

# ── Expose API port ────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Healthcheck ────────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Start the API ──────────────────────────────────────────────────────────────
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]