from django.contrib import admin

from .models import Contribution, Issue, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("github_username", "country", "total_prs", "created_at")
    search_fields = ("github_username", "user__username", "country")
    list_filter = ("country",)


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = (
        "title", "repo_full_name", "language", "difficulty",
        "stars_count", "is_assigned", "beginner_friendly_score",
    )
    list_filter = ("difficulty", "language", "is_assigned", "foundation")
    search_fields = ("title", "repo_full_name")
    ordering = ("-stars_count",)


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ("user", "repo_full_name", "kind", "merged_at", "verified")
    list_filter = ("kind", "verified")
    search_fields = ("user__username", "repo_full_name", "title")
