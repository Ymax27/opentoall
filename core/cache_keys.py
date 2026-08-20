"""Cache versioning for issue/leaderboard pages.

Bump ``ISSUES_CACHE_VERSION`` after ingestion so explore/leaderboard/home
never serve silently stale issue counts for longer than one TTL window.
"""

from __future__ import annotations

from django.core.cache import cache

ISSUES_CACHE_VERSION_KEY = "issues_cache_version"
CACHE_TTL = 60 * 12  # 12 minutes — within the 10–15 min target


def issues_cache_version() -> int:
    version = cache.get(ISSUES_CACHE_VERSION_KEY)
    if version is None:
        cache.set(ISSUES_CACHE_VERSION_KEY, 1, timeout=None)
        return 1
    return int(version)


def bump_issues_cache() -> int:
    """Invalidate explore / leaderboard / home stats caches."""
    try:
        return int(cache.incr(ISSUES_CACHE_VERSION_KEY))
    except ValueError:
        cache.set(ISSUES_CACHE_VERSION_KEY, 2, timeout=None)
        return 2


def cache_key(*parts: object) -> str:
    version = issues_cache_version()
    joined = ":".join(str(p) for p in parts)
    return f"v{version}:{joined}"
