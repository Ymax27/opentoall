"""Thin, defensive wrapper around the GitHub REST API.

Only the endpoints required by the MVP are implemented. Every call is
authenticated with a Personal Access Token when available (raising the rate
limit from 60 to 5000 requests/hour) and fails softly so a single bad repo
never breaks a whole ingestion run.
"""

from __future__ import annotations

import logging

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 15.0

# Labels commonly used to flag issues that welcome new contributors.
BEGINNER_LABELS = [
    "good first issue",
    "help wanted",
    "beginner friendly",
    "good-first-issue",
]


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = getattr(settings, "GITHUB_PAT", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def search_issues(language: str | None = None, label: str = "good first issue",
                  page: int = 1, per_page: int = 30) -> list[dict]:
    """Search open, unassigned issues that welcome contributors."""
    query = f'is:issue is:open no:assignee label:"{label}"'
    if language:
        query += f" language:{language}"

    params = {"q": query, "per_page": per_page, "page": page, "sort": "updated"}

    try:
        resp = httpx.get(
            f"{GITHUB_API}/search/issues",
            headers=_headers(),
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("GitHub issue search failed (lang=%s): %s", language, exc)
        return []

    return resp.json().get("items", [])


def get_repo_details(full_name: str) -> dict:
    """Fetch repository metadata (stars, size, health signals)."""
    try:
        resp = httpx.get(
            f"{GITHUB_API}/repos/{full_name}",
            headers=_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("GitHub repo lookup failed (%s): %s", full_name, exc)
        return {}

    return resp.json()


def get_repo_community_profile(full_name: str) -> dict:
    """Return GitHub's community health profile (CONTRIBUTING.md, CoC, ...)."""
    try:
        resp = httpx.get(
            f"{GITHUB_API}/repos/{full_name}/community/profile",
            headers=_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.debug("Community profile unavailable (%s): %s", full_name, exc)
        return {}

    return resp.json()
