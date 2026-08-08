"""Scheduled ingestion of contributor-friendly issues from GitHub."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from celery import shared_task

from .models import Issue
from .services.github_client import (
    get_repo_community_profile,
    get_repo_details,
    search_issues,
)
from .services.metrics import (
    compute_beginner_friendly_score,
    detect_foundation,
    estimate_difficulty,
)

logger = logging.getLogger(__name__)

LANGUAGES = ["Python", "Go", "JavaScript", "TypeScript", "Rust", "Java"]

# search/issues is limited to 30 requests/minute — throttle between calls.
THROTTLE_SECONDS = 2


def _parse_dt(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


@shared_task
def fetch_all_issues():
    """Refresh the issue catalogue for every tracked language."""
    created_or_updated = 0
    repo_cache: dict[str, dict] = {}

    for lang in LANGUAGES:
        for item in search_issues(language=lang):
            repo_full_name = item["repository_url"].split("repos/")[-1]

            if repo_full_name not in repo_cache:
                repo_data = get_repo_details(repo_full_name)
                community = get_repo_community_profile(repo_full_name)
                repo_cache[repo_full_name] = {"repo": repo_data, "community": community}
                time.sleep(THROTTLE_SECONDS)

            repo_data = repo_cache[repo_full_name]["repo"]
            community = repo_cache[repo_full_name]["community"]
            files = (community or {}).get("files") or {}

            labels = [label["name"] for label in item.get("labels", [])]

            Issue.objects.update_or_create(
                github_issue_id=item["id"],
                defaults={
                    "number": item.get("number"),
                    "title": item["title"],
                    "body": (item.get("body") or "")[:4000],
                    "url": item["html_url"],
                    "repo_full_name": repo_full_name,
                    "repo_avatar_url": repo_data.get("owner", {}).get("avatar_url", ""),
                    "language": lang,
                    "labels": ",".join(labels),
                    "foundation": detect_foundation(repo_full_name),
                    "difficulty": estimate_difficulty(labels),
                    "is_assigned": item.get("assignee") is not None,
                    "stars_count": repo_data.get("stargazers_count", 0),
                    "comments_count": item.get("comments", 0),
                    "repo_size_kb": repo_data.get("size", 0),
                    "has_contributing": bool(files.get("contributing")),
                    "has_code_of_conduct": bool(files.get("code_of_conduct")),
                    "beginner_friendly_score": compute_beginner_friendly_score(
                        repo_data, community, merged_first_pr_ratio=0.5
                    ),
                    "issue_updated_at": _parse_dt(item.get("updated_at")),
                },
            )
            created_or_updated += 1

        time.sleep(THROTTLE_SECONDS)

    logger.info("fetch_all_issues: %s issues processed", created_or_updated)
    return created_or_updated
