import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from core.models import Contribution, Issue, Profile
from core.services.metrics import (
    compute_beginner_friendly_score,
    detect_foundation,
    estimate_difficulty,
)


# --------------------------------------------------------------------------- #
# Metrics (pure functions, no DB)                                             #
# --------------------------------------------------------------------------- #
def test_beginner_friendly_score_bounds():
    repo = {"has_wiki": True, "open_issues_count": 5}
    community = {"files": {"contributing": {}, "code_of_conduct": {}}}
    score = compute_beginner_friendly_score(repo, community, merged_first_pr_ratio=0.8)
    assert 0.0 <= score <= 1.0


def test_estimate_difficulty():
    assert estimate_difficulty(["good first issue"]) == "beginner"
    assert estimate_difficulty(["expert", "complex"]) == "advanced"
    assert estimate_difficulty(["refactor"]) == "intermediate"


def test_detect_foundation():
    assert detect_foundation("kubernetes/kubernetes") == "CNCF"
    assert detect_foundation("apache/airflow") == "Apache"
    assert detect_foundation("some/random") == ""


# --------------------------------------------------------------------------- #
# Models                                                                      #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_issue_size_category_and_bars():
    issue = Issue.objects.create(
        github_issue_id=1, title="Test", url="https://github.com",
        repo_full_name="test/test", repo_size_kb=1000,
    )
    assert issue.size_category() == "léger"
    assert issue.size_bars == 1
    assert issue.repo_owner == "test"
    assert issue.repo_name == "test"


@pytest.mark.django_db
def test_issue_percentage_properties():
    issue = Issue.objects.create(
        github_issue_id=2, title="T", url="https://x", repo_full_name="a/b",
        beginner_friendly_score=0.85, pr_acceptance_rate=0.9,
    )
    assert issue.beginner_friendly_pct == 85
    assert issue.pr_acceptance_pct == 90


@pytest.mark.django_db
def test_profile_created_for_new_user_and_counts():
    user = User.objects.create_user("dev1")
    # Signal creates the profile automatically.
    assert Profile.objects.filter(user=user).exists()
    Contribution.objects.create(
        user=user, repo_full_name="a/b", pr_url="https://x", merged_at=None,
    )
    assert user.profile.total_prs == 1
    assert user.profile.merged_prs == 0


# --------------------------------------------------------------------------- #
# Views                                                                       #
# --------------------------------------------------------------------------- #
@pytest.mark.django_db
def test_home_page_loads(client):
    assert client.get(reverse("home")).status_code == 200


@pytest.mark.django_db
def test_explore_page_and_htmx(client):
    Issue.objects.create(
        github_issue_id=3, title="Fix bug", url="https://x",
        repo_full_name="org/repo", language="Python", difficulty="beginner",
    )
    full = client.get(reverse("explore"))
    assert full.status_code == 200
    assert b"Fix bug" in full.content

    partial = client.get(reverse("explore"), HTTP_HX_REQUEST="true")
    assert partial.status_code == 200
    # HTMX response is the fragment, not the full page (no <html>).
    assert b"<html" not in partial.content


@pytest.mark.django_db
def test_explore_language_filter(client):
    Issue.objects.create(github_issue_id=4, title="Py", url="https://x",
                         repo_full_name="a/py", language="Python")
    Issue.objects.create(github_issue_id=5, title="Go", url="https://x",
                         repo_full_name="a/go", language="Go")
    resp = client.get(reverse("explore"), {"language": "Go"})
    assert b"Go" in resp.content
    assert b">Py<" not in resp.content


@pytest.mark.django_db
def test_leaderboard_and_profile(client):
    user = User.objects.create_user("kwame")
    profile = user.profile
    profile.github_username = "kwame"
    profile.country = "Ghana"
    profile.save()
    Contribution.objects.create(user=user, repo_full_name="a/b", pr_url="https://x")

    assert client.get(reverse("leaderboard")).status_code == 200
    assert client.get(reverse("profile", args=["kwame"])).status_code == 200
