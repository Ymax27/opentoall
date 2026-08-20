"""Data models for OpenToAll.

Three entities mirror the three functional blocks of the cahier des charges:
- ``Issue``        → the aggregator + real-world-constraint metrics (blocs 1 & 2)
- ``Profile``      → public visibility for African contributors (bloc 3)
- ``Contribution`` → the tracked contributions that feed profiles & leaderboard
"""

from __future__ import annotations

from django.contrib.auth.models import User as DjangoUser
from django.db import models
from django.urls import reverse

# Rough ISO country → flag emoji map for the most represented communities.
# Falls back gracefully to a globe when a country is unknown.
_FLAGS = {
    "nigeria": "🇳🇬", "kenya": "🇰🇪", "ghana": "🇬🇭", "senegal": "🇸🇳",
    "sénégal": "🇸🇳", "cameroon": "🇨🇲", "cameroun": "🇨🇲", "morocco": "🇲🇦",
    "maroc": "🇲🇦", "egypt": "🇪🇬", "égypte": "🇪🇬", "south africa": "🇿🇦",
    "tunisia": "🇹🇳", "tunisie": "🇹🇳", "algeria": "🇩🇿", "algérie": "🇩🇿",
    "ivory coast": "🇨🇮", "côte d'ivoire": "🇨🇮", "rwanda": "🇷🇼",
    "uganda": "🇺🇬", "ethiopia": "🇪🇹", "benin": "🇧🇯", "bénin": "🇧🇯",
    "togo": "🇹🇬", "mali": "🇲🇱", "burkina faso": "🇧🇫", "tanzania": "🇹🇿",
}


class Profile(models.Model):
    user = models.OneToOneField(
        DjangoUser, on_delete=models.CASCADE, related_name="profile"
    )
    github_username = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(blank=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    headline = models.CharField(
        max_length=160, blank=True, help_text="Courte accroche affichée sur le profil"
    )
    bio = models.TextField(blank=True)
    languages = models.CharField(
        max_length=255, blank=True, help_text="Séparés par des virgules"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.github_username or self.user.username

    def get_absolute_url(self):
        return reverse("profile", args=[self.github_username or self.user.username])

    @property
    def languages_list(self):
        return [lang.strip() for lang in self.languages.split(",") if lang.strip()]

    @property
    def flag(self):
        if not self.country:
            return "🌍"
        return _FLAGS.get(self.country.strip().lower(), "🌍")

    @property
    def total_prs(self):
        return self.user.contributions.count()

    @property
    def merged_prs(self):
        return self.user.contributions.filter(merged_at__isnull=False).count()

    @property
    def initials(self):
        source = self.github_username or self.user.username or "?"
        return source[:2].upper()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["country"]),
            models.Index(fields=["github_username"]),
        ]


class Issue(models.Model):
    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Débutant"
        INTERMEDIATE = "intermediate", "Intermédiaire"
        ADVANCED = "advanced", "Confirmé"

    github_issue_id = models.BigIntegerField(unique=True)
    number = models.IntegerField(blank=True, null=True)
    title = models.CharField(max_length=500)
    body = models.TextField(blank=True)
    url = models.URLField()
    repo_full_name = models.CharField(max_length=255)
    repo_avatar_url = models.URLField(blank=True)
    language = models.CharField(max_length=100, blank=True, null=True)
    labels = models.CharField(max_length=500, blank=True)
    foundation = models.CharField(
        max_length=100, blank=True, help_text="CNCF, Apache, Linux Foundation, ..."
    )
    difficulty = models.CharField(
        max_length=20, choices=Difficulty.choices, default=Difficulty.INTERMEDIATE
    )

    is_assigned = models.BooleanField(default=False)
    stars_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    repo_size_kb = models.IntegerField(default=0)

    # Bloc 2 — real-world-constraint metrics
    avg_response_time_hours = models.FloatField(blank=True, null=True)
    pr_acceptance_rate = models.FloatField(blank=True, null=True)
    beginner_friendly_score = models.FloatField(blank=True, null=True)
    has_contributing = models.BooleanField(default=False)
    has_code_of_conduct = models.BooleanField(default=False)

    issue_updated_at = models.DateTimeField(blank=True, null=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-stars_count"]
        indexes = [
            models.Index(fields=["language"]),
            models.Index(fields=["difficulty"]),
            models.Index(fields=["is_assigned"]),
            models.Index(fields=["is_assigned", "language"]),
            models.Index(fields=["is_assigned", "difficulty"]),
            models.Index(fields=["foundation"]),
            models.Index(fields=["-stars_count"]),
            models.Index(fields=["-beginner_friendly_score"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.repo_full_name})"

    def get_absolute_url(self):
        return reverse("issue_detail", args=[self.pk])

    # -- Repository owner / name helpers ------------------------------------
    @property
    def repo_owner(self):
        return self.repo_full_name.split("/")[0] if "/" in self.repo_full_name else ""

    @property
    def repo_name(self):
        return self.repo_full_name.split("/")[-1]

    @property
    def labels_list(self):
        return [label.strip() for label in self.labels.split(",") if label.strip()]

    # -- Repository weight (bloc 2) -----------------------------------------
    def size_category(self):
        if self.repo_size_kb < 5000:
            return "léger"
        elif self.repo_size_kb < 50000:
            return "moyen"
        return "lourd"

    @property
    def size_bars(self):
        """1 (light) → 3 (heavy) for the signal-bar visualiser in the UI."""
        return {"léger": 1, "moyen": 2, "lourd": 3}[self.size_category()]

    @property
    def stars_display(self):
        if self.stars_count >= 1000:
            return f"{self.stars_count / 1000:.1f}k".replace(".0k", "k")
        return str(self.stars_count)

    # -- Responsiveness label (bloc 2) --------------------------------------
    @property
    def responsiveness(self):
        hours = self.avg_response_time_hours
        if hours is None:
            return None
        if hours <= 6:
            return "Excellent"
        if hours <= 48:
            return "Bon"
        return "Lent"

    @property
    def beginner_friendly_pct(self):
        if self.beginner_friendly_score is None:
            return None
        return round(self.beginner_friendly_score * 100)

    @property
    def pr_acceptance_pct(self):
        if self.pr_acceptance_rate is None:
            return None
        return round(self.pr_acceptance_rate * 100)

    @property
    def accent(self):
        """Left-border accent colour keyed on difficulty (see DESIGN.md)."""
        return {
            self.Difficulty.BEGINNER: "tertiary",
            self.Difficulty.INTERMEDIATE: "primary",
            self.Difficulty.ADVANCED: "secondary",
        }.get(self.difficulty, "primary")


class Contribution(models.Model):
    class Kind(models.TextChoices):
        FEATURE = "feature", "Fonctionnalité"
        BUGFIX = "bugfix", "Correction de bug"
        DOCS = "docs", "Documentation"
        REFACTOR = "refactor", "Refactoring"
        OTHER = "other", "Autre"

    user = models.ForeignKey(
        DjangoUser, on_delete=models.CASCADE, related_name="contributions"
    )
    issue = models.ForeignKey(
        Issue, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="contributions",
    )
    repo_full_name = models.CharField(max_length=255)
    title = models.CharField(max_length=500, blank=True)
    pr_url = models.URLField()
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTHER)
    merged_at = models.DateTimeField(blank=True, null=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["merged_at"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.repo_full_name}"

    @property
    def is_merged(self):
        return self.merged_at is not None
