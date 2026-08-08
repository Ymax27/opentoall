"""Populate the database with realistic demo data.

Lets anyone run the project and see a fully alive UI without needing a GitHub
token or waiting for the Celery ingestion job.

Usage:
    python manage.py seed_demo          # add demo data (idempotent)
    python manage.py seed_demo --fresh  # wipe demo data first
"""

from __future__ import annotations

import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Contribution, Issue, Profile

CONTRIBUTORS = [
    ("kwame_m", "Kwame Mensah", "Ghana", "Full-stack dev passionné de cloud-native et d'UI/UX.", "Go, Rust, Python"),
    ("sarah_d", "Sarah Doe", "Kenya", "Open source, c'est s'élever en élevant les autres.", "Python, JavaScript"),
    ("moussa_d", "Moussa Diallo", "Sénégal", "Backend engineer, amoureux des systèmes distribués.", "Java, Go"),
    ("amina_k", "Amina Kone", "Côte d'Ivoire", "Frontend & design systems. Je code des interfaces qui respirent.", "TypeScript, JavaScript"),
    ("chidi_o", "Chidi Okafor", "Nigeria", "Platform engineer. Kubernetes est mon terrain de jeu.", "Go, Python"),
    ("fatima_z", "Fatima Zahra", "Maroc", "Data & ML. J'aime rendre les modèles utiles.", "Python, Rust"),
    ("thabo_n", "Thabo Nkosi", "South Africa", "Mobile-first dev, obsédé par la performance.", "TypeScript, Kotlin"),
    ("yaw_a", "Yaw Asante", "Ghana", "Sécurité applicative et bonnes pratiques DevSecOps.", "Go, Python"),
]

REPOS = [
    ("kubernetes/kubernetes", "Go", "CNCF", 108000, 900000, "advanced"),
    ("vuejs/core", "TypeScript", "", 45000, 32000, "beginner"),
    ("nodejs/node", "JavaScript", "", 98000, 780000, "intermediate"),
    ("pallets/flask", "Python", "", 66000, 7000, "beginner"),
    ("rust-lang/rust", "Rust", "", 92000, 640000, "advanced"),
    ("prometheus/prometheus", "Go", "CNCF", 54000, 210000, "intermediate"),
    ("django/django", "Python", "", 78000, 250000, "intermediate"),
    ("facebook/react", "JavaScript", "", 225000, 320000, "advanced"),
    ("apache/airflow", "Python", "Apache", 36000, 190000, "intermediate"),
    ("helm/helm", "Go", "CNCF", 27000, 45000, "beginner"),
]

ISSUE_TITLES = [
    "Improve error message when config file is missing",
    "Add documentation for the new plugin API",
    "Fix flaky test in the scheduler module",
    "Support timeout option in the HTTP client",
    "Update deprecated lifecycle hooks in examples",
    "Handle empty response body gracefully",
    "Add French locale to the CLI output",
    "Refactor logging to use structured fields",
    "Memory leak when unmounting nested components",
    "Clarify contribution guidelines for first-timers",
]

LABELS = ["good first issue", "help wanted", "documentation", "bug", "enhancement"]


class Command(BaseCommand):
    help = "Seed the database with realistic demo data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fresh", action="store_true", help="Delete existing demo data first."
        )

    def handle(self, *args, **options):
        if options["fresh"]:
            Contribution.objects.all().delete()
            Issue.objects.all().delete()
            Profile.objects.exclude(user__is_superuser=True).delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING("Demo data wiped."))

        random.seed(42)
        now = timezone.now()

        # --- Issues -------------------------------------------------------
        issues: list[Issue] = []
        for idx, title in enumerate(ISSUE_TITLES):
            repo, lang, foundation, stars, size, difficulty = REPOS[idx % len(REPOS)]
            issue, _ = Issue.objects.update_or_create(
                github_issue_id=900000 + idx,
                defaults={
                    "number": 1000 + idx,
                    "title": title,
                    "body": (
                        "This issue is part of the OpenToAll demo dataset. It mirrors "
                        "the shape of a real GitHub issue so the interface feels alive "
                        "without requiring a live API token.\n\n"
                        "**Requirements:**\n"
                        "- Reproduce the described behaviour\n"
                        "- Add or update the relevant tests\n"
                        "- Keep the change focused and well documented"
                    ),
                    "url": f"https://github.com/{repo}/issues/{1000 + idx}",
                    "repo_full_name": repo,
                    "language": lang,
                    "foundation": foundation,
                    "difficulty": difficulty,
                    "labels": ",".join(random.sample(LABELS, k=random.randint(2, 3))),
                    "is_assigned": False,
                    "stars_count": stars,
                    "comments_count": random.randint(0, 24),
                    "repo_size_kb": size,
                    "avg_response_time_hours": round(random.uniform(1, 72), 1),
                    "pr_acceptance_rate": round(random.uniform(0.55, 0.95), 2),
                    "beginner_friendly_score": round(random.uniform(0.4, 0.98), 2),
                    "has_contributing": random.random() > 0.2,
                    "has_code_of_conduct": random.random() > 0.3,
                    "issue_updated_at": now - timedelta(hours=random.randint(1, 240)),
                },
            )
            issues.append(issue)

        # --- Contributors + contributions --------------------------------
        for username, name, country, headline, langs in CONTRIBUTORS:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"first_name": name.split()[0], "last_name": name.split()[-1]},
            )
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "github_username": username,
                    "avatar_url": f"https://api.dicebear.com/9.x/thumbs/svg?seed={username}",
                    "country": country,
                    "headline": headline,
                    "languages": langs,
                },
            )
            for _ in range(random.randint(3, 14)):
                issue = random.choice(issues)
                merged = random.random() > 0.25
                Contribution.objects.create(
                    user=user,
                    issue=issue,
                    repo_full_name=issue.repo_full_name,
                    title=issue.title,
                    pr_url=f"{issue.url.replace('issues', 'pull')}",
                    kind=random.choice(Contribution.Kind.values),
                    merged_at=now - timedelta(days=random.randint(1, 120)) if merged else None,
                    verified=merged,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Issue.objects.count()} issues, "
                f"{Profile.objects.count()} profiles, "
                f"{Contribution.objects.count()} contributions."
            )
        )
