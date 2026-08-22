"""Sync a user's public merged PRs into Contribution rows for the leaderboard."""

from __future__ import annotations

import logging
from datetime import datetime

from django.contrib.auth.models import User as DjangoUser

from core.models import Contribution, Issue
from core.services.github_client import GitHubAPIError, GitHubRateLimitError, search_merged_prs

logger = logging.getLogger(__name__)


def _parse_dt(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def sync_merged_prs_for_user(user: DjangoUser, *, username: str | None = None, max_items: int = 30) -> int:
    """Fetch merged PRs from GitHub and upsert Contribution rows.

    The « Ouvre sur GitHub » button does **not** create contributions by itself.
    Tracking happens when the user is connected and we sync their public merged
    PRs (on login today). Returns the number of upserts.
    """
    profile = getattr(user, "profile", None)
    login = (username or (profile.github_username if profile else "") or user.username or "").strip()
    if not login:
        return 0

    try:
        items = search_merged_prs(login, per_page=max_items)
    except (GitHubRateLimitError, GitHubAPIError) as exc:
        logger.warning("Could not sync PRs for %s: %s", login, exc)
        return 0

    created_or_updated = 0
    for item in items:
        pr_url = item.get("html_url") or ""
        if not pr_url:
            continue

        repo_url = item.get("repository_url") or ""
        repo_full_name = repo_url.split("repos/")[-1] if "repos/" in repo_url else ""
        if not repo_full_name:
            # Search results sometimes only expose html_url like …/owner/repo/pull/N
            parts = pr_url.rstrip("/").split("/")
            if len(parts) >= 5 and parts[-2] == "pull":
                repo_full_name = f"{parts[-4]}/{parts[-3]}"

        issue = None
        if item.get("id"):
            issue = Issue.objects.filter(github_issue_id=item["id"]).first()

        Contribution.objects.update_or_create(
            user=user,
            pr_url=pr_url,
            defaults={
                "issue": issue,
                "repo_full_name": repo_full_name or "unknown/unknown",
                "title": (item.get("title") or "")[:500],
                "kind": Contribution.Kind.OTHER,
                "merged_at": _parse_dt(item.get("closed_at") or item.get("updated_at")),
                "verified": True,
            },
        )
        created_or_updated += 1

    if created_or_updated:
        logger.info("Synced %s merged PRs for %s", created_or_updated, login)
    return created_or_updated
