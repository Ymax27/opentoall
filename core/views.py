from urllib.parse import urlencode

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Contribution, Issue, Profile

SORT_OPTIONS = {
    "stars": "-stars_count",
    "recent": "-issue_updated_at",
    "beginner": "-beginner_friendly_score",
    "light": "repo_size_kb",
}

# Number of issues per page in the explore view.
PAGE_SIZE = 30


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

    issues = issues.order_by(SORT_OPTIONS.get(sort, "-stars_count"))

    paginator = Paginator(issues, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Querystring carrying every active filter (minus `page`) so pagination
    # links preserve the current search context.
    params = {k: v for k, v in {
        "q": q, "language": language, "difficulty": difficulty,
        "foundation": foundation, "sort": sort,
    }.items() if v}
    querystring = urlencode(params)

    languages = (
        Issue.objects.exclude(language__isnull=True)
        .exclude(language="")
        .values_list("language", flat=True)
        .distinct()
        .order_by("language")
    )

    context = {
        "page_obj": page_obj,
        "total_count": paginator.count,
        "querystring": querystring,
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


@csrf_exempt
@require_http_methods(["GET", "POST"])
def fetch_issues_trigger(request):
    """Cron-friendly ingestion endpoint (Render free → cron-job.org).

    Auth: ``?token=…`` or header ``X-Fetch-Token: …`` must match
    ``FETCH_ISSUES_TOKEN``. Returns 503 if the token is not configured.

    The heavy GitHub crawl runs in a background thread so the HTTP response
    returns quickly (Render / cron free tiers time out long requests).
    """
    expected = getattr(settings, "FETCH_ISSUES_TOKEN", "") or ""
    if not expected:
        return HttpResponse(
            "FETCH_ISSUES_TOKEN is not configured.",
            status=503,
            content_type="text/plain",
        )

    provided = (
        request.headers.get("X-Fetch-Token")
        or request.GET.get("token")
        or request.POST.get("token")
        or ""
    )
    if provided != expected:
        return HttpResponseForbidden("Invalid token.")

    pages = request.GET.get("pages") or request.POST.get("pages") or "1"
    try:
        pages = max(1, min(int(pages), 5))
    except (TypeError, ValueError):
        pages = 1

    sync = (request.GET.get("sync") or request.POST.get("sync") or "") in {
        "1",
        "true",
        "yes",
    }

    from .tasks import ingest_issues

    if sync:
        count = ingest_issues(pages=pages)
        return JsonResponse({"ok": True, "processed": count, "pages": pages})

    import logging
    import threading

    logger = logging.getLogger(__name__)

    def _run():
        try:
            processed = ingest_issues(pages=pages)
            logger.info("Background fetch_issues finished: %s issues", processed)
        except Exception:
            logger.exception("Background fetch_issues failed")

    threading.Thread(target=_run, name="fetch-issues", daemon=True).start()
    return JsonResponse(
        {"ok": True, "started": True, "pages": pages, "mode": "async"},
        status=202,
    )
