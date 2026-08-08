"""Fetch real issues from GitHub into the database — no Celery required.

Requires a GITHUB_PAT in your environment for a usable rate limit.

Examples:
    python manage.py fetch_issues
    python manage.py fetch_issues --pages 3
    python manage.py fetch_issues --languages Python Go --labels "good first issue"
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand

from core.tasks import LABELS, LANGUAGES, ingest_issues


class Command(BaseCommand):
    help = "Fetch contributor-friendly issues from GitHub into the database."

    def add_arguments(self, parser):
        parser.add_argument("--languages", nargs="+", default=LANGUAGES)
        parser.add_argument("--labels", nargs="+", default=LABELS)
        parser.add_argument("--pages", type=int, default=2)
        parser.add_argument("--per-page", type=int, default=50)

    def handle(self, *args, **options):
        if not getattr(settings, "GITHUB_PAT", ""):
            self.stdout.write(self.style.WARNING(
                "No GITHUB_PAT set — GitHub will rate-limit you at 60 req/hour. "
                "Create a token at https://github.com/settings/tokens and add it "
                "to your .env for 5000 req/hour."
            ))

        count = ingest_issues(
            languages=options["languages"],
            labels=options["labels"],
            pages=options["pages"],
            per_page=options["per_page"],
            on_progress=lambda msg: self.stdout.write(f"  {msg}"),
        )
        self.stdout.write(self.style.SUCCESS(f"Done — {count} issues ingested."))
