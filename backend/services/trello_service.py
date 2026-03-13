"""
Trello REST API service — create cards on a board list.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from config import TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_API_BASE, TRELLO_DEFAULT_LIST_ID

logger = logging.getLogger("meeting_action.trello")

# Map priority → Trello label color
PRIORITY_COLOR_MAP = {
    "High":   "red",
    "Medium": "yellow",
    "Low":    "green",
}


def _auth_params() -> dict[str, str]:
    return {"key": TRELLO_API_KEY, "token": TRELLO_TOKEN}


def get_lists(board_id: str) -> list[dict[str, Any]]:
    """Return all lists on a Trello board."""
    url = f"{TRELLO_API_BASE}/boards/{board_id}/lists"
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=_auth_params())
        resp.raise_for_status()
    return resp.json()


def create_card(
    task_title: str,
    description: str = "",
    priority: str = "Medium",
    team: str = "General",
    status: str = "To Do",
    list_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a Trello card and return the API response.

    Parameters
    ----------
    task_title  : Card name
    description : Card description (markdown)
    priority    : High / Medium / Low
    team        : Team label string appended to description
    status      : Informational (used to pick list when list_id is not given)
    list_id     : Trello list ID to place the card in.
                  Falls back to TRELLO_DEFAULT_LIST_ID env var.
    """
    target_list = list_id or TRELLO_DEFAULT_LIST_ID
    if not target_list:
        raise ValueError(
            "list_id must be provided or TRELLO_DEFAULT_LIST_ID must be set."
        )

    full_desc = (
        f"{description}\n\n"
        f"**Team:** {team}  \n"
        f"**Priority:** {priority}  \n"
        f"**Status:** {status}"
    )

    params = {
        **_auth_params(),
        "idList":   target_list,
        "name":     task_title,
        "desc":     full_desc,
        "pos":      "bottom",
    }

    logger.info("Creating Trello card  title=%s  list=%s", task_title, target_list)

    url = f"{TRELLO_API_BASE}/cards"
    with httpx.Client(timeout=20) as client:
        resp = client.post(url, params=params)
        resp.raise_for_status()

    data = resp.json()
    logger.info("Trello card created  id=%s  url=%s", data.get("id"), data.get("shortUrl"))
    return {
        "card_id":    data["id"],
        "card_url":   data["shortUrl"],
        "card_name":  data["name"],
        "list_id":    data["idList"],
    }
