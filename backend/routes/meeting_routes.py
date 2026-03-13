from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from services.gemini_service import analyze_transcript
from utils.pdf_export import generate_pdf

logger = logging.getLogger("meeting_action.meeting_routes")
router = APIRouter(tags=["Meeting"])

# ── Request / Response models ─────────────────────────────
class TranscriptRequest(BaseModel):
    transcript: str

class ExportRequest(BaseModel):
    meeting_summary: str = ""
    discussion_points: list[str] = []
    decisions: list[str] = []
    tasks: list[dict[str, Any]] = []
    title: str = "Meeting Action Report"

# ── Routes ───────────────────────────────────────────────
@router.post("/analyze-transcript")
async def analyze_transcript_route(req: TranscriptRequest):
    if not req.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript must not be empty.")
    try:
        result = analyze_transcript(req.transcript)
        return JSONResponse(content=result)
    except Exception as exc:
        logger.exception("Error analysing transcript")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/generate-tasks")
async def generate_tasks(req: TranscriptRequest):
    if not req.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript must not be empty.")
    try:
        result = analyze_transcript(req.transcript)
        return JSONResponse(content={
            "meeting_summary": result.get("meeting_summary", ""),
            "decisions": result.get("decisions", []),
            "tasks": result.get("tasks", []),
        })
    except Exception as exc:
        logger.exception("Error generating tasks")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

# ── Export routes ───────────────────────────────────────
@router.post("/export/pdf")
async def export_pdf(req: ExportRequest):
    try:
        pdf_bytes = generate_pdf(
            meeting_summary=req.meeting_summary,
            decisions=req.decisions,
            tasks=req.tasks,
            discussion_points=req.discussion_points,
            title=req.title,
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="meeting_report.pdf"'},
        )
    except Exception as exc:
        logger.exception("Error generating PDF")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/export/json")
async def export_json(req: ExportRequest):
    payload = req.model_dump()
    return Response(
        content=json.dumps(payload, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="meeting_report.json"'},
    )