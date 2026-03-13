"""
Meeting-related routes:
  POST /analyze-transcript
  POST /generate-tasks
  WS   /ws/live-transcription
  POST /export/pdf
  POST /export/json
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from services import sarvam_llm_service, speech_to_text_service
from utils.pdf_export import generate_pdf

logger = logging.getLogger("meeting_action.meeting_routes")
router = APIRouter(tags=["Meeting"])


# ── Request / Response models ──────────────────────────────────────────────────

class TranscriptRequest(BaseModel):
    transcript: str


class ExportRequest(BaseModel):
    meeting_summary: str = ""
    discussion_points: list[str] = []
    decisions: list[str] = []
    tasks: list[dict[str, Any]] = []
    title: str = "Meeting Action Report"


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/analyze-transcript")
async def analyze_transcript(req: TranscriptRequest):
    """
    Analyse a meeting transcript with Sarvam LLM and return structured insights.
    """
    if not req.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript must not be empty.")
    try:
        result = sarvam_llm_service.analyze_transcript(req.transcript)
        return JSONResponse(content=result)
    except Exception as exc:
        logger.exception("Error analysing transcript")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/generate-tasks")
async def generate_tasks(req: TranscriptRequest):
    """
    Generate tasks from a live meeting transcript (same pipeline as /analyze-transcript).
    """
    if not req.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript must not be empty.")
    try:
        result = sarvam_llm_service.generate_tasks(req.transcript)
        return JSONResponse(content={
            "meeting_summary":   result.get("meeting_summary", ""),
            "decisions":         result.get("decisions", []),
            "tasks":             result.get("tasks", []),
        })
    except Exception as exc:
        logger.exception("Error generating tasks")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── WebSocket: Live transcription ──────────────────────────────────────────────

# In-memory store: session_id → accumulated transcript
_live_transcripts: dict[str, str] = {}


@router.websocket("/ws/live-transcription")
async def live_transcription(websocket: WebSocket):
    """
    WebSocket endpoint for live meeting transcription.

    Protocol (binary frames):
      - Client sends raw audio chunks (bytes) captured from the microphone.
      - Server responds with JSON text frames:
          { "type": "transcript", "text": "...", "full_transcript": "..." }
          { "type": "error",      "message": "..." }

    The accumulated transcript is stored in _live_transcripts keyed by
    client host+port so it survives multiple audio chunks.
    """
    await websocket.accept()
    session_key = f"{websocket.client.host}:{websocket.client.port}"
    _live_transcripts[session_key] = ""
    logger.info("WS connected  session=%s", session_key)

    try:
        while True:
            message = await websocket.receive()

            # Client can send audio bytes OR a JSON control message
            if "bytes" in message and message["bytes"]:
                audio_bytes: bytes = message["bytes"]
                try:
                    chunk_text = speech_to_text_service.transcribe_audio_bytes(audio_bytes)
                    _live_transcripts[session_key] += " " + chunk_text
                    await websocket.send_text(json.dumps({
                        "type":             "transcript",
                        "text":             chunk_text,
                        "full_transcript":  _live_transcripts[session_key].strip(),
                    }))
                except Exception as exc:
                    logger.exception("STT error  session=%s", session_key)
                    await websocket.send_text(json.dumps({
                        "type":    "error",
                        "message": str(exc),
                    }))

            elif "text" in message and message["text"]:
                # Allow client to send {"action": "get_transcript"} or {"action": "clear"}
                try:
                    ctrl = json.loads(message["text"])
                    if ctrl.get("action") == "get_transcript":
                        await websocket.send_text(json.dumps({
                            "type":            "full_transcript",
                            "full_transcript": _live_transcripts[session_key].strip(),
                        }))
                    elif ctrl.get("action") == "clear":
                        _live_transcripts[session_key] = ""
                        await websocket.send_text(json.dumps({"type": "cleared"}))
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        logger.info("WS disconnected  session=%s", session_key)
    finally:
        _live_transcripts.pop(session_key, None)


# ── Export routes ─────────────────────────────────────────────────────────────

@router.post("/export/pdf")
async def export_pdf(req: ExportRequest):
    """
    Generate and return a PDF report for the meeting.
    """
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
    """
    Return the meeting data as a formatted JSON download.
    """
    payload = req.model_dump()
    return Response(
        content=json.dumps(payload, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="meeting_report.json"'},
    )
