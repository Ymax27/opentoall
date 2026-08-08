from django.contrib.auth.models import User as DjangoUser
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from .models import Contribution, Issue, Profile

SORT_OPTIONS = {
    "stars": "-stars_count",
    "recent": "-issue_updated_at",
    "beginner": "-beginner_friendly_score",
    "light": "repo_size_kb",
}


def home(request):
    stats = {
        "total_contributors": Profile.objects.count(),
        "total_contributions": Contribution.objects.count(),
        "total_countries": (
            Profile.objects.exclude(country__isnull=True)
            .exclude(country="")
            .values("country")
            .distinct()
            .count()
        ),
        "total_issues": Issue.objects.filter(is_assigned=False).count(),
    }
    featured = Issue.objects.filter(is_assigned=False).order_by(
        "-beginner_friendly_score", "-stars_count"
    )[:3]
    return render(request, "core/home.html", {"stats": stats, "featured": featured})


def explore(request):
    issues = Issue.objects.filter(is_assigned=False)

    q = request.GET.get("q", "").strip()
    language = request.GET.get("language", "").strip()
    difficulty = request.GET.get("difficulty", "").strip()
    foundation = request.GET.get("foundation", "").strip()
    max_size = request.GET.get("max_size", "").strip()
    sort = request.GET.get("sort", "stars").strip()

    if q:
        issues = issues.filter(
            Q(title__icontains=q) | Q(repo_full_name__icontains=q)
        )
    if language:
        issues = issues.filter(language__iexact=language)
    if difficulty:
        issues = issues.filter(difficulty=difficulty)
    if foundation:
        issues = issues.filter(foundation__iexact=foundation)
    if max_size.isdigit():
        issues = issues.filter(repo_size_kb__lte=int(max_size))

    issues = issues.order_by(SORT_OPTIONS.get(sort, "-stars_count"))[:60]

    languages = (
        Issue.objects.exclude(language__isnull=True)
        .exclude(language="")
        .values_list("language", flat=True)
        .distinct()
        .order_by("language")
    )

    context = {
        "issues": issues,
        "languages": languages,
        "filters": {
            "q": q,
            "language": language,
            "difficulty": difficulty,
            "foundation": foundation,
            "sort": sort,
        },
        "difficulties": Issue.Difficulty.choices,
    }

    template = "core/_issue_list.html" if request.htmx else "core/explore.html"
    return render(request, template, context)


def issue_detail(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    related = (
        Issue.objects.filter(language=issue.language, is_assigned=False)
        .exclude(pk=issue.pk)
        .order_by("-beginner_friendly_score")[:3]
    )
    return render(
        request, "core/issue_detail.html", {"issue": issue, "related": related}
    )


def profile_view(request, username):
    profile = get_object_or_404(
        Profile.objects.select_related("user"), github_username=username
    )
    contributions = profile.user.contributions.select_related("issue")
    languages = profile.languages_list
    return render(
        request,
        "core/profile.html",
        {
            "profile": profile,
            "contributions": contributions,
            "languages": languages,
        },
    )


def leaderboard(request):
    country = request.GET.get("country", "").strip()

    profiles = (
        Profile.objects.select_related("user")
        .annotate(total=Count("user__contributions"))
        .filter(total__gt=0)
        .order_by("-total")
    )
    if country:
        profiles = profiles.filter(country__iexact=country)

    countries = (
        Profile.objects.exclude(country__isnull=True)
        .exclude(country="")
        .values_list("country", flat=True)
        .distinct()
        .order_by("country")
    )

    profiles = list(profiles[:50])
    top = profiles[0] if profiles else None

    return render(
        request,
        "core/leaderboard.html",
        {
            "profiles": profiles,
            "podium": profiles[:3],
            "rest": profiles[3:],
            "top": top,
            "countries": countries,
            "selected_country": country,
        },
    )
