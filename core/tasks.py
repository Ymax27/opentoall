"""Ingestion of contributor-friendly issues from GitHub.

The heavy lifting lives in :func:`ingest_issues`, which is shared by:
- the Celery beat task :func:`fetch_all_issues` (scheduled, in production), and
- the ``fetch_issues`` management command (manual, no broker required).

GitHub's search API is capped (1000 results per query, ~30 req/min) and rate
limited, which is exactly why OpenToAll aggregates issues periodically into its
own database instead of querying GitHub on every page view.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime

from celery import shared_task

from .cache_keys import bump_issues_cache
from .models import Issue
from .services.github_client import (
    GitHubAPIError,
    GitHubRateLimitError,
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
LABELS = ["good first issue", "help wanted"]

# Extra pause between pages (search client already enforces ~2.2s between searches).
THROTTLE_SECONDS = 0.5


def _parse_dt(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def ingest_issues(
    languages: list[str] | None = None,
    labels: list[str] | None = None,
    pages: int = 1,
    per_page: int = 50,
    throttle: float = THROTTLE_SECONDS,
    on_progress=None,
) -> int:
    """Fetch and upsert issues for the given languages/labels/pages.

    Idempotent via ``update_or_create`` on ``github_issue_id``. Returns the
    number of issues created or updated. ``on_progress`` is an optional
    callable receiving a human-readable status string.
    """
    languages = languages or LANGUAGES
    labels = labels or LABELS
    processed = 0
    repo_cache: dict[str, dict] = {}

    def _log(msg: str):
        logger.info(msg)
        if on_progress:
            on_progress(msg)

    for lang in languages:
        for label in labels:
            for page in range(1, pages + 1):
                items = search_issues(
                    language=lang, label=label, page=page, per_page=per_page
                )
                _log(f"{lang} · {label} · page {page}: {len(items)} issues")
                if not items:
                    break

                for item in items:
                    # Pull requests are returned by the issue search too — skip them.
                    if "pull_request" in item:
                        continue

                    repo_full_name = item["repository_url"].split("repos/")[-1]

                    if repo_full_name not in repo_cache:
                        repo_data = get_repo_details(repo_full_name)
                        community = get_repo_community_profile(repo_full_name)
                        repo_cache[repo_full_name] = {
                            "repo": repo_data,
                            "community": community,
                        }
                        time.sleep(throttle)

                    repo_data = repo_cache[repo_full_name]["repo"]
                    community = repo_cache[repo_full_name]["community"]
                    files = (community or {}).get("files") or {}

                    issue_labels = [lab["name"] for lab in item.get("labels", [])]

                    Issue.objects.update_or_create(
                        github_issue_id=item["id"],
                        defaults={
                            "number": item.get("number"),
                            "title": item["title"],
                            "body": (item.get("body") or "")[:4000],
                            "url": item["html_url"],
                            "repo_full_name": repo_full_name,
                            "repo_avatar_url": repo_data.get("owner", {}).get(
                                "avatar_url", ""
                            ),
                            "language": lang,
                            "labels": ",".join(issue_labels),
                            "foundation": detect_foundation(repo_full_name),
                            "difficulty": estimate_difficulty(issue_labels),
                            "is_assigned": item.get("assignee") is not None,
                            "stars_count": repo_data.get("stargazers_count", 0),
                            "comments_count": item.get("comments", 0),
                            "repo_size_kb": repo_data.get("size", 0),
                            "has_contributing": bool(files.get("contributing")),
                            "has_code_of_conduct": bool(files.get("code_of_conduct")),
                            "pr_acceptance_rate": (community or {}).get(
                                "health_percentage", 0
                            )
                            / 100
                            or None,
                            "beginner_friendly_score": compute_beginner_friendly_score(
                                repo_data, community, merged_first_pr_ratio=0.5
                            ),
                            "issue_updated_at": _parse_dt(item.get("updated_at")),
                        },
                    )
                    processed += 1

                time.sleep(throttle)

    bump_issues_cache()
    _log(f"Ingestion complete: {processed} issues processed.")
    return processed


@shared_task(
    bind=True,
    name="core.tasks.fetch_all_issues",
    autoretry_for=(GitHubAPIError,),
    retry_backoff=True,
    retry_backoff_max=900,
    retry_jitter=True,
    max_retries=5,
    soft_time_limit=25 * 60,
    time_limit=30 * 60,
    acks_late=True,
)
def fetch_all_issues(self, pages: int = 1):
    """Celery entry point used by the scheduled beat task."""
    try:
        return ingest_issues(pages=pages)
    except GitHubRateLimitError as exc:
        countdown = min(int(exc.retry_after or 60), 900)
        logger.error(
            "Deferring fetch_all_issues after rate limit (retry in %ss)",
            countdown,
            extra={"event": "celery_rate_limit", "task_id": self.request.id},
        )
        raise self.retry(exc=exc, countdown=countdown)
