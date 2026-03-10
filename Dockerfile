# Dockerfile
# Owner: Akshada
# Task 4, Week 4 — Container Build Instructions
#
# Builds the LexiScan Auto API into a Docker container.
# Includes system dependencies: Tesseract OCR + Poppler (for pdf2image).
#
# TODO (Akshada): Fill in once requirements.txt is finalized.

FROM python:3.11-slim

# System dependencies for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy base model
RUN python -m spacy download en_core_web_sm

# Copy project source
COPY . .

# TODO (Akshada): Expose port and set startup command
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
