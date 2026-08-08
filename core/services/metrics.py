"""Heuristics that turn raw GitHub data into OpenToAll's real-world metrics.

These are intentionally simple and dependency-free for the MVP (bloc 2 of the
cahier des charges). They can be replaced by community-sourced ratings in V2.
"""

from __future__ import annotations

BEGINNER_LABEL_HINTS = (
    "good first issue", "good-first-issue", "beginner", "starter",
    "easy", "first-timers-only", "help wanted",
)
ADVANCED_LABEL_HINTS = ("hard", "complex", "expert", "advanced", "epic")


def compute_beginner_friendly_score(
    repo_data: dict,
    community_profile: dict | None = None,
    merged_first_pr_ratio: float | None = None,
) -> float:
    """Return a 0.0 → 1.0 "welcoming to beginners" score.

    Combines documentation health, first-time-PR acceptance and project
    activity into a single normalised score.
    """
    community_profile = community_profile or {}
    score = 0.0

    files = community_profile.get("files") or {}
    if files.get("contributing"):
        score += 0.25
    if files.get("code_of_conduct"):
        score += 0.1
    if repo_data.get("has_wiki") or repo_data.get("has_pages"):
        score += 0.1

    if merged_first_pr_ratio is not None:
        score += merged_first_pr_ratio * 0.45

    if repo_data.get("open_issues_count", 0) > 0:
        score += 0.1

    return round(min(score, 1.0), 2)


def estimate_difficulty(labels: list[str]) -> str:
    """Map GitHub labels to one of beginner / intermediate / advanced."""
    lowered = {label.lower() for label in labels}

    if any(hint in label for label in lowered for hint in BEGINNER_LABEL_HINTS):
        return "beginner"
    if any(hint in label for label in lowered for hint in ADVANCED_LABEL_HINTS):
        return "advanced"
    return "intermediate"


def detect_foundation(repo_full_name: str) -> str:
    """Best-effort mapping of an owner org to a well-known foundation."""
    owner = repo_full_name.split("/")[0].lower()
    cncf = {"kubernetes", "helm", "argoproj", "prometheus", "envoyproxy", "etcd-io"}
    apache = {"apache"}
    if owner in cncf:
        return "CNCF"
    if owner in apache:
        return "Apache"
    return ""
