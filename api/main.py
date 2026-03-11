"""
api/main.py — Akshada
FastAPI application entry point for LexiScan Auto.

Usage (local):
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

Usage (Docker):
    docker-compose up --build
    Then visit: http://localhost:8000/docs
"""

import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes.extract import router as extract_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ─── Lifespan (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load the NER model at startup so the first request isn't slow."""
    logger.info("🚀 LexiScan Auto API starting up...")
    try:
        from src.ner.predictor import _load_model
        _load_model()
        logger.info("✅ NER model pre-loaded successfully.")
    except FileNotFoundError as e:
        logger.warning(f"⚠️  NER model not found at startup: {e}")
        logger.warning("   The /extract endpoint will fail until the model is trained.")
    yield
    logger.info("LexiScan Auto API shut down.")


# ─── App Initialisation ───────────────────────────────────────────────────────
app = FastAPI(
    title="LexiScan Auto API",
    description=(
        "Automated Legal Entity Extractor — extracts PARTY, DATE, AMOUNT, "
        "and JURISDICTION entities from scanned/text PDF contracts."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (allow all origins for development; tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request Timing Middleware ────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start   = time.time()
    response = await call_next(request)
    elapsed  = round((time.time() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    return response


# ─── Global Exception Handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check server logs."}
    )


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(extract_router, prefix="", tags=["Extraction"])


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Returns API health status and model availability."""
    from pathlib import Path
    model_ready = Path("models/spacy_ner").exists()
    return {
        "status":      "ok",
        "version":     "1.0.0",
        "model_ready": model_ready,
    }


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "LexiScan Auto API is running.",
        "docs":    "/docs",
        "health":  "/health",
        "extract": "POST /extract"
    }