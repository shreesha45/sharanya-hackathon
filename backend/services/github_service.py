"""
GitHub REST API service — create issues on any repository.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from config import GITHUB_TOKEN, GITHUB_API_BASE

logger = logging.getLogger("meeting_action.github")

PRIORITY_LABEL_MAP = {
    "High":   "priority: high",
    "Medium": "priority: medium",
    "Low":    "priority: low",
}

TEAM_LABEL_MAP = {
    "Frontend": "team: frontend",
    "Backend":  "team: backend",
    "DevOps":   "team: devops",
    "QA":       "team: qa",
    "Design":   "team: design",
    "General":  "team: general",
}


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def create_issue(
    repo: str,
    title: str,
    description: str,
    team: str = "General",
    priority: str = "Medium",
    assignee: str | None = None,
    extra_labels: list[str] | None = None,
) -> dict[str, Any]:
    """
    Create a GitHub issue and return the API response.

    Parameters
    ----------
    repo        : ``owner/repo`` string
    title       : Issue title
    description : Issue body (markdown supported)
    team        : Maps to a label
    priority    : High / Medium / Low — maps to a label
    assignee    : GitHub username (optional)
    extra_labels: Additional label names (optional)
    """
    owner, repo_name = repo.split("/", 1)
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo_name}/issues"

    labels: list[str] = []
    if team in TEAM_LABEL_MAP:
        labels.append(TEAM_LABEL_MAP[team])
    if priority in PRIORITY_LABEL_MAP:
        labels.append(PRIORITY_LABEL_MAP[priority])
    if extra_labels:
        labels.extend(extra_labels)

    body_md = f"{description}\n\n---\n**Team:** {team}  \n**Priority:** {priority}"

    payload: dict[str, Any] = {
        "title":  title,
        "body":   body_md,
        "labels": labels,
    }
    if assignee:
        payload["assignees"] = [assignee]

    logger.info("Creating GitHub issue  repo=%s  title=%s", repo, title)

    with httpx.Client(timeout=20) as client:
        resp = client.post(url, json=payload, headers=_headers())
        resp.raise_for_status()

    data = resp.json()
    logger.info("Issue created  url=%s", data.get("html_url"))
    return {
        "issue_url":    data["html_url"],
        "issue_number": data["number"],
        "issue_id":     data["id"],
        "state":        data["state"],
        "title":        data["title"],
    }
