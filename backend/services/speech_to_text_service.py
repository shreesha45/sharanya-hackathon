"""
Sarvam Speech-to-Text service.
Accepts raw audio bytes and returns transcribed text.
"""
from __future__ import annotations

import logging
from io import BytesIO

import httpx

from config import SARVAM_API_KEY, SARVAM_STT_URL

logger = logging.getLogger("meeting_action.stt")


def transcribe_audio_bytes(audio_bytes: bytes, language_code: str = "en-IN") -> str:
    """
    Send raw audio bytes to Sarvam STT and return the transcript string.

    Parameters
    ----------
    audio_bytes:
        Raw audio data (wav / webm / ogg etc.) from the browser microphone.
    language_code:
        BCP-47 code.  Sarvam supports 'en-IN', 'hi-IN', 'ta-IN', etc.
        Defaults to English (India).
    """
    headers = {"api-subscription-key": SARVAM_API_KEY}

    files = {
        "file": ("audio.wav", BytesIO(audio_bytes), "audio/wav"),
    }
    data = {
        "language_code": language_code,
        "model": "saarika:v2",
        "with_timestamps": "false",
    }

    logger.info("Sending %d bytes to Sarvam STT", len(audio_bytes))

    with httpx.Client(timeout=30) as client:
        resp = client.post(SARVAM_STT_URL, headers=headers, files=files, data=data)
        resp.raise_for_status()

    result = resp.json()
    transcript: str = result.get("transcript", "")
    logger.info("STT returned %d chars", len(transcript))
    return transcript
