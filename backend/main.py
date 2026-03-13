"""
AI Meeting-to-Action System — FastAPI Backend
============================================
Run with:  uvicorn main:app --reload
"""
from __future__ import annotations

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import CORS_ORIGINS, logger as root_logger
from routes.meeting_routes import router as meeting_router
from routes.integration_routes import router as integration_router

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Meeting-to-Action System",
    description=(
        "Converts meeting transcripts into structured engineering tasks using "
        "Sarvam AI.  Integrates with GitHub and Trello for task management."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request logging middleware ────────────────────────────────────────────────
_req_logger = logging.getLogger("meeting_action.request")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    _req_logger.info(
        "%s  %s  →  %d  (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    root_logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(meeting_router)
app.include_router(integration_router)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "AI Meeting-to-Action System"}


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "AI Meeting-to-Action System is running.",
        "docs":    "/docs",
    }
