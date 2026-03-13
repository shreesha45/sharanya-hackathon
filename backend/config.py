import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── Logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("meeting_action")

# ── API credentials ─────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
TRELLO_API_KEY: str = os.getenv("TRELLO_API_KEY", "")
TRELLO_TOKEN: str = os.getenv("TRELLO_TOKEN", "")
TRELLO_DEFAULT_LIST_ID: str = os.getenv("TRELLO_DEFAULT_LIST_ID", "")

# ── Gemini API endpoint ─────────────────────────────────
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"

# ── GitHub base URL ─────────────────────────────────────
GITHUB_API_BASE = "https://api.github.com"

# ── Trello base URL ─────────────────────────────────────
TRELLO_API_BASE = "https://api.trello.com/1"

# ── CORS origins ────────────────────────────────────────
CORS_ORIGINS: list[str] = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")