"""
Integration routes:
  POST /github/create-issue
  POST /trello/create-card
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services import github_service, trello_service

logger = logging.getLogger("meeting_action.integration_routes")
router = APIRouter(tags=["Integrations"])


# ── GitHub ─────────────────────────────────────────────────────────────────────

class GitHubIssueRequest(BaseModel):
    repo:        str = Field(..., example="owner/repo")
    title:       str
    description: str = ""
    team:        str = "General"
    priority:    str = "Medium"
    assignee:    str | None = None
    labels:      list[str] = []


@router.post("/github/create-issue")
async def create_github_issue(req: GitHubIssueRequest):
    """Create a GitHub issue and return the issue URL."""
    if "/" not in req.repo:
        raise HTTPException(
            status_code=400,
            detail='repo must be in "owner/repo" format.',
        )
    try:
        result = github_service.create_issue(
            repo=req.repo,
            title=req.title,
            description=req.description,
            team=req.team,
            priority=req.priority,
            assignee=req.assignee,
            extra_labels=req.labels or None,
        )
        return JSONResponse(content=result)
    except Exception as exc:
        logger.exception("GitHub issue creation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Trello ─────────────────────────────────────────────────────────────────────

class TrelloCardRequest(BaseModel):
    task_title:  str
    description: str = ""
    priority:    str = "Medium"
    team:        str = "General"
    status:      str = "To Do"
    list_id:     str | None = None   # overrides env default


@router.post("/trello/create-card")
async def create_trello_card(req: TrelloCardRequest):
    """Create a Trello card and return the card URL."""
    try:
        result = trello_service.create_card(
            task_title=req.task_title,
            description=req.description,
            priority=req.priority,
            team=req.team,
            status=req.status,
            list_id=req.list_id,
        )
        return JSONResponse(content=result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Trello card creation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
