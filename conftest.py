"""Ensure tests never pick up a local Postgres DATABASE_URL / USE_POSTGRES."""

import os

import pytest

# Must run before Django settings are imported by pytest-django.
os.environ["USE_POSTGRES"] = "0"
os.environ.pop("DATABASE_URL", None)

# Disable Whitenoise manifest storage for tests to avoid collectstatic requirement
os.environ["DEBUG"] = "True"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest"


@pytest.fixture(autouse=True)
def stub_github_contributor_count(monkeypatch):
    """Avoid live GitHub calls from the site-wide “built by” credit."""
    monkeypatch.setattr(
        "core.services.repo_credit.get_repo_contributor_count",
        lambda _full_name: 12,
    )
