"""Populate the database with realistic demo data.

Lets anyone run the project and see a fully alive UI (with pagination) without
needing a GitHub token or waiting for the Celery ingestion job.

Usage:
    python manage.py seed_demo               # add demo data (idempotent)
    python manage.py seed_demo --fresh       # wipe demo data first
    python manage.py seed_demo --issues 300  # control how many issues
"""

from __future__ import annotations

import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
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
    ("nadia_b", "Nadia Bello", "Nigeria", "API design & developer experience.", "Python, TypeScript"),
    ("liam_o", "Liam Okonkwo", "Nigeria", "Compilers, Rust et systèmes bas niveau.", "Rust, C"),
    ("aisha_m", "Aisha Mwangi", "Kenya", "SRE. J'aime quand ça ne tombe jamais.", "Go, Python"),
    ("omar_t", "Omar Tahiri", "Maroc", "Web performance & accessibilité.", "JavaScript, TypeScript"),
]

# (owner/name, language, foundation, stars, size_kb)
REPOS = [
    ("kubernetes/kubernetes", "Go", "CNCF", 108000, 900000),
    ("vuejs/core", "TypeScript", "", 45000, 32000),
    ("nodejs/node", "JavaScript", "", 98000, 780000),
    ("pallets/flask", "Python", "", 66000, 7000),
    ("rust-lang/rust", "Rust", "", 92000, 640000),
    ("prometheus/prometheus", "Go", "CNCF", 54000, 210000),
    ("django/django", "Python", "", 78000, 250000),
    ("facebook/react", "JavaScript", "", 225000, 320000),
    ("apache/airflow", "Python", "Apache", 36000, 190000),
    ("helm/helm", "Go", "CNCF", 27000, 45000),
    ("microsoft/vscode", "TypeScript", "", 162000, 520000),
    ("tensorflow/tensorflow", "Python", "", 185000, 850000),
    ("golang/go", "Go", "", 122000, 260000),
    ("denoland/deno", "Rust", "", 97000, 120000),
    ("fastapi/fastapi", "Python", "", 76000, 28000),
    ("angular/angular", "TypeScript", "", 95000, 410000),
    ("grpc/grpc", "C++", "CNCF", 41000, 300000),
    ("etcd-io/etcd", "Go", "CNCF", 47000, 95000),
    ("scikit-learn/scikit-learn", "Python", "", 59000, 160000),
    ("vitejs/vite", "TypeScript", "", 67000, 42000),
    ("apache/kafka", "Java", "Apache", 28000, 220000),
    ("tokio-rs/tokio", "Rust", "", 26000, 38000),
    ("pytest-dev/pytest", "Python", "", 12000, 26000),
    ("envoyproxy/envoy", "C++", "CNCF", 24000, 480000),
]

TITLES = [
    "Improve error message when {x} is missing",
    "Add documentation for the new {x} API",
    "Fix flaky test in the {x} module",
    "Support timeout option in the {x} client",
    "Update deprecated {x} hooks in examples",
    "Handle empty {x} response gracefully",
    "Add French locale to the {x} output",
    "Refactor {x} to use structured logging",
    "Memory leak when unmounting {x} components",
    "Clarify contribution guidelines for {x}",
    "Add type hints to the {x} package",
    "Improve performance of {x} serialization",
    "Fix race condition in {x} scheduler",
    "Add retry logic to {x} network calls",
    "Document environment variables for {x}",
    "Migrate {x} tests to the new fixtures",
    "Support dark mode in the {x} dashboard",
    "Validate {x} input before processing",
    "Add example for {x} in the tutorial",
    "Reduce bundle size of the {x} widget",
]
FILLERS = ["config", "auth", "cache", "router", "parser", "scheduler", "client",
           "storage", "metrics", "plugin", "session", "queue", "logger", "worker"]

LABELS = ["good first issue", "help wanted", "documentation", "bug",
          "enhancement", "beginner friendly", "hacktoberfest"]
DIFFS = ["beginner", "beginner", "intermediate", "intermediate", "advanced"]


class Command(BaseCommand):
    help = "Seed the database with realistic demo data."

    def add_arguments(self, parser):
        parser.add_argument("--fresh", action="store_true", help="Delete existing demo data first.")
        parser.add_argument("--issues", type=int, default=180, help="Number of demo issues to create.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["fresh"]:
            Contribution.objects.all().delete()
            Issue.objects.all().delete()
            Profile.objects.exclude(user__is_superuser=True).delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING("Demo data wiped."))

        random.seed(42)
        now = timezone.now()
        n_issues = options["issues"]

        # --- Issues -------------------------------------------------------
        issues: list[Issue] = []
        for idx in range(n_issues):
            repo, lang, foundation, stars, size = REPOS[idx % len(REPOS)]
            filler = random.choice(FILLERS)
            title = random.choice(TITLES).format(x=filler)
            difficulty = random.choice(DIFFS)
            # Lighter repos & docs issues skew beginner-friendly.
            base_score = 0.9 if difficulty == "beginner" else 0.6 if difficulty == "intermediate" else 0.4
            issue, _ = Issue.objects.update_or_create(
                github_issue_id=900000 + idx,
                defaults={
                    "number": 1000 + idx,
                    "title": title,
                    "body": (
                        f"This issue affects the **{filler}** area of `{repo}`. It is part "
                        "of the OpenToAll demo dataset and mirrors the shape of a real "
                        "GitHub issue.\n\n"
                        "**Requirements:**\n"
                        "- Reproduce the described behaviour\n"
                        "- Add or update the relevant tests\n"
                        "- Keep the change focused and well documented"
                    ),
                    "url": f"https://github.com/{repo}/issues/{1000 + idx}",
                    "repo_full_name": repo,
                    "repo_avatar_url": f"https://api.dicebear.com/9.x/shapes/svg?seed={repo.split('/')[0]}",
                    "language": lang,
                    "foundation": foundation,
                    "difficulty": difficulty,
                    "labels": ",".join(random.sample(LABELS, k=random.randint(2, 4))),
                    "is_assigned": False,
                    "stars_count": stars + random.randint(-2000, 2000),
                    "comments_count": random.randint(0, 40),
                    "repo_size_kb": size,
                    "avg_response_time_hours": round(random.uniform(1, 96), 1),
                    "pr_acceptance_rate": round(random.uniform(0.5, 0.96), 2),
                    "beginner_friendly_score": round(min(0.99, base_score + random.uniform(-0.15, 0.1)), 2),
                    "has_contributing": random.random() > 0.2,
                    "has_code_of_conduct": random.random() > 0.35,
                    "issue_updated_at": now - timedelta(hours=random.randint(1, 720)),
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
            for _ in range(random.randint(4, 24)):
                issue = random.choice(issues)
                merged = random.random() > 0.25
                Contribution.objects.create(
                    user=user,
                    issue=issue,
                    repo_full_name=issue.repo_full_name,
                    title=issue.title,
                    pr_url=issue.url.replace("issues", "pull"),
                    kind=random.choice(Contribution.Kind.values),
                    merged_at=now - timedelta(days=random.randint(1, 160)) if merged else None,
                    verified=merged,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Issue.objects.count()} issues, "
                f"{Profile.objects.count()} profiles, "
                f"{Contribution.objects.count()} contributions."
            )
        )
