"""Light “built by” credit: maintainer + live GitHub contributor count."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from django.conf import settings

from core.cache_keys import cache_get, cache_set
from core.services.github_client import get_repo_contributor_count

logger = logging.getLogger(__name__)

CONTRIBUTOR_COUNT_CACHE_KEY = "repo_contributor_count"
CONTRIBUTOR_COUNT_TTL = 60 * 60  # 1 hour — changes slowly


def github_repo_full_name() -> str:
    """``owner/repo`` parsed from ``GITHUB_REPO_URL``."""
    raw = (getattr(settings, "GITHUB_REPO_URL", "") or "").strip().rstrip("/")
    if not raw:
        return "Ymax27/opentoall"
    path = urlparse(raw).path.strip("/")
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return "Ymax27/opentoall"


def github_repo_owner() -> str:
    return github_repo_full_name().split("/", 1)[0]


def cached_contributor_count() -> int | None:
    """Cached GitHub contributor count, or ``None`` when unavailable."""
    payload = cache_get(CONTRIBUTOR_COUNT_CACHE_KEY)
    if isinstance(payload, dict) and "n" in payload:
        return payload["n"]

    count = get_repo_contributor_count(github_repo_full_name())
    # Cache misses (None) briefly so a GitHub outage does not hammer the API.
    cache_set(
        CONTRIBUTOR_COUNT_CACHE_KEY,
        {"n": count},
        timeout=CONTRIBUTOR_COUNT_TTL if count is not None else 60 * 5,
    )
    return count


def built_by_context() -> dict:
    """Template vars for the About page and footer credit."""
    owner = github_repo_owner()
    repo_url = getattr(settings, "GITHUB_REPO_URL", "").rstrip("/") or (
        f"https://github.com/{github_repo_full_name()}"
    )
    return {
        "repo_owner": owner,
        "repo_owner_url": f"https://github.com/{owner}",
        "repo_contributors_url": f"{repo_url}/graphs/contributors",
        "repo_contributor_count": cached_contributor_count(),
    }
