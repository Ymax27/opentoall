import re
from datetime import timedelta
from html import unescape
from urllib.parse import parse_qs, urlsplit

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone, translation

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
    assert b'id="list-loader"' in full.content
    # The live region exists and starts empty so HTMX events can fill it
    # (aria-live only announces content changes).
    assert b'<span id="list-status" class="sr-only" role="status" aria-live="polite"></span>' in full.content
    assert b"htmx:beforeRequest" in full.content

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


def test_health_does_not_touch_the_database(client):
    assert client.get(reverse("health")).status_code == 200
    assert client.head(reverse("health")).status_code == 200


@pytest.mark.django_db
def test_health_is_fast_enough_for_cron(client, django_assert_num_queries):
    """The health endpoint must complete in milliseconds for cron-job.org.

    cron-job.org disables jobs that time out repeatedly (~30s limit).
    This endpoint powers both the keep-alive cron (every 10 min) and
    Kubernetes liveness probes, so it must never touch the database.
    """
    with django_assert_num_queries(0):
        response = client.get(reverse("health"))
    assert response.status_code == 200
    assert response.content == b"ok"


@pytest.mark.django_db
def test_fetch_issues_trigger_requires_token(client, settings):
    settings.FETCH_ISSUES_TOKEN = "secret-token"
    assert client.get(reverse("fetch_issues_trigger")).status_code == 403
    assert client.get(
        reverse("fetch_issues_trigger"), {"token": "wrong"}
    ).status_code == 403


@pytest.mark.django_db
def test_fetch_issues_trigger_starts_async(client, settings, monkeypatch):
    settings.FETCH_ISSUES_TOKEN = "secret-token"
    called = {}

    def fake_ingest(**kwargs):
        called["pages"] = kwargs.get("pages")
        return 0

    monkeypatch.setattr("core.tasks.ingest_issues", fake_ingest)
    # Force sync path so the test does not rely on threads.
    resp = client.get(
        reverse("fetch_issues_trigger"),
        {"token": "secret-token", "sync": "1", "pages": "1"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert called.get("pages") == 1


@pytest.mark.django_db
def test_explore_filters_have_accessible_labels(client):
    resp = client.get(reverse("explore"))
    content = resp.content.decode()
    for field_id in ("search-filter", "sort-filter", "language-filter", "clone-size-filter"):
        assert f'for="{field_id}"' in content
        assert f'id="{field_id}"' in content


@pytest.mark.parametrize("has_updated_at", [True, False])
def test_issue_card_updated_date(has_updated_at):
    updated_at = timezone.now() - timedelta(days=3, minutes=1) if has_updated_at else None
    issue = Issue(
        pk=1, github_issue_id=1, title="Test issue", url="https://github.com/a/b/issues/1",
        repo_full_name="a/b", issue_updated_at=updated_at,
    )
    with translation.override("fr"):
        html = render_to_string("core/_issue_card.html", {"issue": issue})

    if has_updated_at:
        assert f'<time datetime="{updated_at.isoformat()}">' in html
        assert "Mise à jour" in html
        assert "il y a 3 jours" in html.replace("\xa0", " ")
    else:
        assert "<time" not in html
        assert "Mise à jour" not in html
        assert "None" not in html


@pytest.mark.django_db
@pytest.mark.parametrize("htmx", [False, True])
@pytest.mark.parametrize(
    "max_size, expected_sizes",
    [("", [4999, 5000, 49999, 50000]), ("5000", [4999]), ("50000", [4999, 5000, 49999])],
)
def test_explore_clone_size_filter(client, max_size, expected_sizes, htmx):
    cache.clear()
    for size in [4999, 5000, 49999, 50000]:
        Issue.objects.create(
            github_issue_id=size, title=f"Repo {size}", url="https://github.com/a/b",
            repo_full_name="a/b", repo_size_kb=size, stars_count=size,
        )

    response = client.get(
        reverse("explore"), {"max_size": max_size},
        HTTP_HX_REQUEST="true" if htmx else "false",
    )
    assert response.status_code == 200
    assert response.context["total_count"] == len(expected_sizes)
    assert sorted(issue.repo_size_kb for issue in response.context["page_obj"]) == expected_sizes
    html = response.content.decode()
    for size in [4999, 5000, 49999, 50000]:
        assert (f">Repo {size}</h3>" in html) == (size in expected_sizes)
    if htmx:
        assert "<html" not in html
    else:
        assert f'<option value="{max_size}" selected>' in html


@pytest.mark.django_db
@pytest.mark.parametrize("htmx", [False, True])
@pytest.mark.parametrize("max_size", [5000, 50000])
def test_explore_clone_size_filter_pagination(client, max_size, htmx):
    cache.clear()
    Issue.objects.bulk_create([
        Issue(
            github_issue_id=i + 1, title=f"Matching {i}", url="https://github.com/a/b",
            repo_full_name="a/b", repo_size_kb=max_size - 1, stars_count=i,
            language="Python",
        )
        for i in range(31)
    ])
    Issue.objects.create(
        github_issue_id=100, title="Excluded boundary", url="https://github.com/a/b",
        repo_full_name="a/b", repo_size_kb=max_size, stars_count=100, language="Python",
    )
    params = {"max_size": str(max_size), "language": "Python", "sort": "stars"}
    headers = {"HTTP_HX_REQUEST": "true" if htmx else "false"}
    response = client.get(reverse("explore"), params, **headers)
    assert response.context["total_count"] == 31
    links = re.findall(r'(?:href|hx-get)="([^"]+)"', response.content.decode())
    page_links = [link for link in links if "page=" in link]
    assert page_links
    for link in page_links:
        query = parse_qs(urlsplit(unescape(link)).query)
        assert query["max_size"] == [str(max_size)]
        assert query["language"] == ["Python"]
        assert query["sort"] == ["stars"]

    next_page = next(link for link in page_links if "page=2" in link)
    response = client.get(reverse("explore") + "?" + urlsplit(unescape(next_page)).query, **headers)
    assert response.status_code == 200
    assert response.context["page_obj"].number == 2
    assert len(response.context["page_obj"]) == 1
    assert b"Excluded boundary" not in response.content
