"""Cache versioning for issue/leaderboard pages.

Bump ``ISSUES_CACHE_VERSION`` after ingestion so explore/leaderboard/home
never serve silently stale issue counts for longer than one TTL window.

All helpers degrade gracefully if the cache backend is unavailable (e.g. Redis
misconfigured on Fly) so a cache outage never becomes a site-wide 500.
"""

from __future__ import annotations

import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)

ISSUES_CACHE_VERSION_KEY = "issues_cache_version"
CACHE_TTL = 60 * 12  # 12 minutes — within the 10–15 min target


def issues_cache_version() -> int:
    try:
        version = cache.get(ISSUES_CACHE_VERSION_KEY)
        if version is None:
            cache.set(ISSUES_CACHE_VERSION_KEY, 1, timeout=None)
            return 1
        return int(version)
    except Exception:
        logger.warning("Cache unavailable for issues_cache_version", exc_info=True)
        return 1


def bump_issues_cache() -> int:
    """Invalidate explore / leaderboard / home stats caches."""
    try:
        return int(cache.incr(ISSUES_CACHE_VERSION_KEY))
    except ValueError:
        try:
            cache.set(ISSUES_CACHE_VERSION_KEY, 2, timeout=None)
            return 2
        except Exception:
            logger.warning("Cache unavailable for bump_issues_cache", exc_info=True)
            return 2
    except Exception:
        logger.warning("Cache unavailable for bump_issues_cache", exc_info=True)
        return 2


def cache_key(*parts: object) -> str:
    version = issues_cache_version()
    joined = ":".join(str(p) for p in parts)
    return f"v{version}:{joined}"


def cache_get(key: str, default=None):
    try:
        return cache.get(key, default)
    except Exception:
        logger.warning("Cache get failed for %s", key, exc_info=True)
        return default


def cache_set(key: str, value, timeout: int = CACHE_TTL) -> None:
    try:
        cache.set(key, value, timeout)
    except Exception:
        logger.warning("Cache set failed for %s", key, exc_info=True)
