import os
import logging

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("meeting_action")

# ── API credentials (loaded from environment) ─────────────────────────────────
SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
TRELLO_API_KEY: str = os.getenv("TRELLO_API_KEY", "")
TRELLO_TOKEN: str = os.getenv("TRELLO_TOKEN", "")
TRELLO_DEFAULT_LIST_ID: str = os.getenv("TRELLO_DEFAULT_LIST_ID", "")

# ── Sarvam endpoints ──────────────────────────────────────────────────────────
SARVAM_CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_STT_URL  = "https://api.sarvam.ai/speech-to-text"

# ── GitHub base URL ───────────────────────────────────────────────────────────
GITHUB_API_BASE = "https://api.github.com"

# ── Trello base URL ───────────────────────────────────────────────────────────
TRELLO_API_BASE = "https://api.trello.com/1"

# ── CORS origins (override via env) ──────────────────────────────────────────
CORS_ORIGINS: list[str] = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")
