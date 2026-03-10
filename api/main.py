"""
main.py
Owner: Akshada (skeleton) | Krutika (final wiring)
Task 4, Week 4 — FastAPI Application Entry Point

Initializes the FastAPI app and registers the /extract route.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# TODO (Akshada): Uncomment once extract.py route is implemented
# from api.routes import extract

app = FastAPI(
    title="LexiScan Auto API",
    description="Automated Legal Entity Extractor — OCR + NER + Rule-Based Validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO (Akshada): Register the extract router once implemented
# app.include_router(extract.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "LexiScan Auto", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
