"""Thin, defensive wrapper around the GitHub REST API.

Only the endpoints required by the MVP are implemented. Every call is
authenticated with a Personal Access Token when available (raising the rate
limit from 60 to 5000 requests/hour) and fails softly so a single bad repo
never breaks a whole ingestion run — except hard rate limits, which raise so
Celery can back off and retry.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
DEFAULT_TIMEOUT = 15.0

# Leave headroom under GitHub's ~30 search req/min and 5000 REST req/h.
SEARCH_MIN_INTERVAL = 2.2
_last_search_at = 0.0


class GitHubRateLimitError(Exception):
    """Raised when GitHub returns 403/429 due to rate limiting."""

    def __init__(self, message: str, *, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class GitHubAPIError(Exception):
    """Transient GitHub API failure worth retrying at the task level."""


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


def _retry_after_seconds(resp: httpx.Response) -> float | None:
    raw = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    reset = resp.headers.get("X-RateLimit-Reset")
    if reset:
        try:
            return max(0.0, float(reset) - time.time())
        except ValueError:
            pass
    return None


def _respect_search_budget() -> None:
    """Client-side throttle for search/issues (~30 req/min with safety margin)."""
    global _last_search_at
    elapsed = time.monotonic() - _last_search_at
    if elapsed < SEARCH_MIN_INTERVAL:
        time.sleep(SEARCH_MIN_INTERVAL - elapsed)
    _last_search_at = time.monotonic()


def _handle_rate_limit(resp: httpx.Response, context: str) -> None:
    if resp.status_code not in {403, 429}:
        return
    remaining = resp.headers.get("X-RateLimit-Remaining")
    # Secondary / search abuse limits also return 403 with remaining often "0".
    if resp.status_code == 429 or remaining == "0" or "rate limit" in resp.text.lower():
        wait = _retry_after_seconds(resp)
        logger.error(
            "GitHub rate limited (%s): status=%s remaining=%s retry_after=%s",
            context,
            resp.status_code,
            remaining,
            wait,
            extra={"event": "github_rate_limit", "status_code": resp.status_code},
        )
        raise GitHubRateLimitError(
            f"GitHub rate limit hit during {context}",
            retry_after=wait,
        )


def _get(url: str, *, params: dict[str, Any] | None = None, context: str) -> dict | list | None:
    try:
        resp = httpx.get(
            url,
            headers=_headers(),
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )
    except httpx.TimeoutException as exc:
        logger.warning(
            "GitHub timeout (%s): %s",
            context,
            exc,
            extra={"event": "github_timeout"},
        )
        raise GitHubAPIError(str(exc)) from exc
    except httpx.HTTPError as exc:
        logger.warning(
            "GitHub request failed (%s): %s",
            context,
            exc,
            extra={"event": "github_http_error"},
        )
        raise GitHubAPIError(str(exc)) from exc

    _handle_rate_limit(resp, context)

    if resp.status_code >= 500:
        logger.warning(
            "GitHub server error (%s): %s",
            context,
            resp.status_code,
            extra={"event": "github_server_error", "status_code": resp.status_code},
        )
        raise GitHubAPIError(f"GitHub {resp.status_code} on {context}")

    if resp.status_code >= 400:
        # Soft-fail for missing community profiles / private repos, etc.
        logger.debug("GitHub client error (%s): %s", context, resp.status_code)
        return None

    remaining = resp.headers.get("X-RateLimit-Remaining")
    if remaining is not None:
        try:
            left = int(remaining)
            if left < 50:
                # Global REST budget running low — pause briefly.
                logger.warning(
                    "GitHub rate budget low (%s remaining)",
                    left,
                    extra={"event": "github_budget_low"},
                )
                time.sleep(1.5)
        except ValueError:
            pass

    return resp.json()


def search_issues(
    language: str | None = None,
    label: str = "good first issue",
    page: int = 1,
    per_page: int = 30,
) -> list[dict]:
    """Search open, unassigned issues that welcome contributors."""
    query = f'is:issue is:open no:assignee label:"{label}"'
    if language:
        query += f" language:{language}"

    _respect_search_budget()
    data = _get(
        f"{GITHUB_API}/search/issues",
        params={"q": query, "per_page": per_page, "page": page, "sort": "updated"},
        context=f"search lang={language}",
    )
    if not isinstance(data, dict):
        return []
    return data.get("items", [])


def get_repo_details(full_name: str) -> dict:
    """Fetch repository metadata (stars, size, health signals)."""
    data = _get(f"{GITHUB_API}/repos/{full_name}", context=f"repo {full_name}")
    return data if isinstance(data, dict) else {}


def get_repo_community_profile(full_name: str) -> dict:
    """Return GitHub's community health profile (CONTRIBUTING.md, CoC, ...)."""
    data = _get(
        f"{GITHUB_API}/repos/{full_name}/community/profile",
        context=f"community {full_name}",
    )
    return data if isinstance(data, dict) else {}


def search_merged_prs(username: str, page: int = 1, per_page: int = 30) -> list[dict]:
    """Public merged PRs authored by ``username`` (for profile / leaderboard sync)."""
    if not username:
        return []
    _respect_search_budget()
    data = _get(
        f"{GITHUB_API}/search/issues",
        params={
            "q": f"author:{username} type:pr is:merged",
            "per_page": per_page,
            "page": page,
            "sort": "updated",
        },
        context=f"merged prs {username}",
    )
    if not isinstance(data, dict):
        return []
    return data.get("items", [])


def _is_community_contributor(entry: dict, *, owner_login: str) -> bool:
    """Humans other than the maintainer — no bots, Cursor, or anonymous."""
    login = (entry.get("login") or "").strip()
    if not login:
        return False
    lower = login.lower()
    if entry.get("type") == "Bot" or lower.endswith("[bot]"):
        return False
    if "dependabot" in lower or "cursor" in lower:
        return False
    if lower == owner_login.lower():
        return False
    return True


def get_repo_contributor_count(full_name: str) -> int | None:
    """Community contributor count for the built-by credit.

    Public Contributors API (no PAT). Excludes the repo owner, bots
    (Dependabot, …), Cursor-related accounts, and anonymous entries.
    Soft-fails for the UI — never raises.
    """
    if not full_name or "/" not in full_name:
        return None

    owner_login = full_name.split("/", 1)[0]
    public_headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    count = 0
    page = 1
    retried_202 = False
    # Small repos fit in one page; cap pages so a huge graph cannot stall the UI.
    while page <= 5:
        try:
            resp = httpx.get(
                f"{GITHUB_API}/repos/{full_name}/contributors",
                headers=public_headers,
                params={"per_page": 100, "anon": "true", "page": page},
                timeout=3.0,
            )
        except httpx.HTTPError as exc:
            logger.warning(
                "GitHub contributor count failed (%s): %s",
                full_name,
                exc,
                extra={"event": "github_contributor_count_error"},
            )
            return None if page == 1 else count

        if resp.status_code == 202 and page == 1 and not retried_202:
            # Stats still computing — one retry after a short pause is enough.
            retried_202 = True
            time.sleep(0.5)
            continue
        if resp.status_code == 204:
            return count
        if resp.status_code >= 400 or resp.status_code == 202:
            logger.warning(
                "GitHub contributor count error (%s): %s",
                full_name,
                resp.status_code,
                extra={
                    "event": "github_contributor_count_http",
                    "status_code": resp.status_code,
                },
            )
            return None if page == 1 else count

        try:
            data = resp.json()
        except ValueError:
            return None if page == 1 else count
        if not isinstance(data, list):
            return None if page == 1 else count
        if not data:
            break

        count += sum(
            1 for entry in data if _is_community_contributor(entry, owner_login=owner_login)
        )
        if len(data) < 100:
            break
        page += 1

    return count
