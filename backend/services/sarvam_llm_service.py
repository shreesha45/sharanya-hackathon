"""
Sarvam AI LLM service — transcript analysis & task generation.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from config import SARVAM_API_KEY, SARVAM_CHAT_URL

logger = logging.getLogger("meeting_action.llm")

# ── Prompt template ───────────────────────────────────────────────────────────
ANALYSIS_SYSTEM_PROMPT = """You are an expert engineering project manager.
Analyse the meeting transcript provided by the user and respond ONLY with a
valid JSON object — no markdown fences, no extra text — that exactly matches
this schema:

{
  "meeting_summary": "<2-4 sentence summary>",
  "discussion_points": ["<point>", ...],
  "decisions": ["<decision>", ...],
  "tasks": [
    {
      "title": "<short imperative title>",
      "description": "<detailed description>",
      "team": "<Frontend | Backend | DevOps | QA | Design | General>",
      "priority": "<High | Medium | Low>",
      "status": "Pending"
    }
  ]
}

Rules:
- Extract every actionable task mentioned or implied.
- Assign realistic priorities based on urgency/importance cues.
- Keep descriptions self-contained so an engineer can act immediately.
- Return ONLY the JSON object.
"""


def _call_sarvam(messages: list[dict], max_tokens: int = 2048) -> str:
    """Low-level POST to Sarvam chat-completions endpoint."""
    headers = {
        "Authorization": f"Bearer {SARVAM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sarvam-m",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    logger.info("Calling Sarvam LLM  model=%s  messages=%d", payload["model"], len(messages))
    with httpx.Client(timeout=60) as client:
        resp = client.post(SARVAM_CHAT_URL, json=payload, headers=headers)
        resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _extract_json(raw: str) -> dict:
    """Strip any accidental markdown fences and parse JSON."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def analyze_transcript(transcript: str) -> dict[str, Any]:
    """
    Send transcript to Sarvam LLM and return structured meeting insights.
    Raises httpx.HTTPStatusError or json.JSONDecodeError on failure.
    """
    messages = [
        {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
        {"role": "user",   "content": f"Meeting transcript:\n\n{transcript}"},
    ]
    raw = _call_sarvam(messages, max_tokens=2048)
    logger.debug("Raw LLM response: %s", raw[:300])
    result = _extract_json(raw)

    # Guarantee required keys exist with safe defaults
    result.setdefault("meeting_summary", "")
    result.setdefault("discussion_points", [])
    result.setdefault("decisions", [])
    result.setdefault("tasks", [])
    for task in result["tasks"]:
        task.setdefault("status", "Pending")

    logger.info(
        "Analysis complete — tasks=%d  decisions=%d",
        len(result["tasks"]),
        len(result["decisions"]),
    )
    return result


def generate_tasks(transcript: str) -> dict[str, Any]:
    """Alias used by the /generate-tasks endpoint (same logic)."""
    return analyze_transcript(transcript)
