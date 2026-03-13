# AI Meeting-to-Action System — Backend

FastAPI backend that converts meeting transcripts into structured engineering
tasks via Sarvam AI, then pushes them to GitHub and Trello.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI + Uvicorn |
| LLM / STT | Sarvam AI (`sarvam-m`, `saarika:v2`) |
| Task management | GitHub REST API + Trello REST API |
| PDF export | ReportLab |
| Real-time transcription | WebSockets |
| Storage | **In-memory only** (no database) |

---

## Folder structure

```
backend/
├── main.py                        # App entry-point, CORS, middleware
├── config.py                      # Env vars & constants
├── requirements.txt
├── .env.example
├── routes/
│   ├── meeting_routes.py          # Transcript analysis, WS, exports
│   └── integration_routes.py     # GitHub & Trello endpoints
├── services/
│   ├── sarvam_llm_service.py      # LLM analysis & task generation
│   ├── speech_to_text_service.py  # Sarvam STT
│   ├── github_service.py          # GitHub issue creation
│   └── trello_service.py          # Trello card creation
└── utils/
    └── pdf_export.py              # ReportLab PDF builder
```

---

## Quick start

```bash
# 1. Clone / enter the backend directory
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and fill in your API keys

# 5. Run the server
uvicorn main:app --reload
```

The API is now available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

---

## API reference

### `POST /analyze-transcript`
```json
{ "transcript": "full meeting text..." }
```
Returns: `meeting_summary`, `discussion_points`, `decisions`, `tasks[]`

---

### `WS /ws/live-transcription`
Binary frames → audio bytes from microphone  
Text frames → `{"type":"transcript","text":"...","full_transcript":"..."}`

Control messages (send as JSON text):
- `{"action":"get_transcript"}` — get accumulated transcript
- `{"action":"clear"}` — clear session transcript

---

### `POST /generate-tasks`
```json
{ "transcript": "live meeting transcript..." }
```
Returns: `meeting_summary`, `decisions`, `tasks[]`

---

### `POST /github/create-issue`
```json
{
  "repo": "owner/repo",
  "title": "...",
  "description": "...",
  "team": "Backend",
  "priority": "High",
  "assignee": "github_username"
}
```

---

### `POST /trello/create-card`
```json
{
  "task_title": "...",
  "description": "...",
  "priority": "High",
  "team": "Backend",
  "status": "To Do",
  "list_id": "optional_list_id"
}
```

---

### `POST /export/pdf`
Body: `{ "meeting_summary", "decisions", "tasks", "discussion_points", "title" }`  
Returns: PDF file download.

### `POST /export/json`
Same body as `/export/pdf`.  
Returns: JSON file download.

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `SARVAM_API_KEY` | ✅ | Sarvam AI API subscription key |
| `GITHUB_TOKEN` | ✅ | GitHub PAT with `repo` scope |
| `TRELLO_API_KEY` | ✅ | Trello Power-Up API key |
| `TRELLO_TOKEN` | ✅ | Trello OAuth token |
| `TRELLO_DEFAULT_LIST_ID` | optional | Default list for new cards |
| `CORS_ORIGINS` | optional | Comma-separated allowed origins |
