import logging
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .cache_keys import CACHE_TTL, cache_key, cache_get, cache_set
from .forms import SupportForm
from .models import Contribution, Issue, Profile

logger = logging.getLogger(__name__)

from django.contrib.sites.requests import RequestSite
from django.contrib.sitemaps.views import x_robots_tag
from django.template.response import TemplateResponse

from .sitemaps import sitemaps as sitemap_classes

SORT_OPTIONS = {
    "stars": "-stars_count",
    "recent": "-issue_updated_at",
    "beginner": "-beginner_friendly_score",
    "light": "repo_size_kb",
}

# Number of issues per page in the explore view.
PAGE_SIZE = 30

# Number of contributors per page on the leaderboard.
LEADERBOARD_PAGE_SIZE = 50

# Homepage FAQ (#46) — kept in the view so tests can assert the same copy.
FAQ_ITEMS = (
    {
        "question": "Pour qui est OpenToAll ?",
        "answer": (
            "Pour les développeurs qui veulent une vraie première contribution "
            "open source — surtout si tu as une connexion limitée ou peu de temps. "
            "Tu cherches une issue encore libre, pas un tutoriel figé."
        ),
    },
    {
        "question": "Comment marchent les filtres ?",
        "answer": (
            "Sur Explorer, tu filtres par langage, niveau, poids du clone et "
            "fondation. Seules les issues ouvertes et non assignées restent "
            "visibles, pour éviter les good first issues déjà prises."
        ),
    },
    {
        "question": "C’est quoi le poids du clone ?",
        "answer": (
            "Le compteur Clone estime la taille du dépôt. Un repo léger se "
            "télécharge plus vite : utile quand la bande passante est serrée. "
            "Trois barres = plus lourd."
        ),
    },
    {
        "question": "Est-ce gratuit ?",
        "answer": (
            "Oui. OpenToAll est gratuit, sans spam, et le code est open source "
            "sous licence MIT. Tu te connectes avec GitHub si tu veux un profil "
            "et le classement."
        ),
    },
    {
        "question": "Comment j’apparais au classement ?",
        "answer": (
            "Connecte-toi avec GitHub. On synchronise tes pull requests "
            "publiques mergées. Cliquer « Ouvre sur GitHub » n’enregistre rien : "
            "seules les PR mergées comptent."
        ),
    },
    {
        "question": "Les issues listées sont-elles vraiment ouvertes ?",
        "answer": (
            "Oui au moment de l’ingestion. On rafraîchit régulièrement depuis "
            "GitHub. Si une issue vient d’être assignée ou fermée, elle peut "
            "disparaître au prochain passage."
        ),
    },
    {
        "question": "Comment contribuer à OpenToAll ?",
        "answer": (
            "Le dépôt est public : issues labeled good first issue, pull "
            "requests bienvenues. Pour une question hors code, utilise "
            "l’email ou WhatsApp indiqués dans le footer."
        ),
    },
)

# Fields needed by issue cards / explore list (avoid pulling full body blobs).
ISSUE_LIST_FIELDS = (
    "id",
    "github_issue_id",
    "number",
    "title",
    "body",
    "url",
    "repo_full_name",
    "repo_avatar_url",
    "language",
    "labels",
    "foundation",
    "difficulty",
    "stars_count",
    "comments_count",
    "repo_size_kb",
    "avg_response_time_hours",
    "beginner_friendly_score",
    "issue_updated_at",
)


def home(request):
    stats_key = cache_key("home", "stats")
    stats = cache_get(stats_key)
    if stats is None:
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
        cache_set(stats_key, stats, CACHE_TTL)

    featured = (
        Issue.objects.filter(is_assigned=False)
        .only(*ISSUE_LIST_FIELDS)
        .order_by("-beginner_friendly_score", "-stars_count")[:3]
    )
    return render(
        request,
        "core/home.html",
        {"stats": stats, "featured": featured, "faq_items": FAQ_ITEMS},
    )


def support(request):
    """Support page: short form + public email."""
    support_email = getattr(settings, "SUPPORT_EMAIL", "linxconcept27@gmail.com")
    if request.method == "POST":
        form = SupportForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("website"):
                messages.success(
                    request,
                    "Merci — on te répond sous quelques jours.",
                )
                return redirect("support")

            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]
            body = form.cleaned_data["message"]
            subject = f"[OpenToAll] Message de {name}"
            content = (
                f"Nom : {name}\n"
                f"Email : {email}\n\n"
                f"{body}\n"
            )
            try:
                mail = EmailMessage(
                    subject=subject,
                    body=content,
                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", support_email),
                    to=[support_email],
                    reply_to=[email],
                )
                mail.send(fail_silently=False)
            except Exception:
                logger.exception(
                    "Support form email failed",
                    extra={"event": "support_email_error"},
                )
                messages.error(
                    request,
                    f"L’envoi a échoué. Écris-nous directement à {support_email}.",
                )
                return render(
                    request,
                    "core/support.html",
                    {"form": form, "support_email": support_email},
                )

            messages.success(
                request,
                "Merci — on te répond sous quelques jours.",
            )
            return redirect("support")
    else:
        form = SupportForm()

    return render(
        request,
        "core/support.html",
        {"form": form, "support_email": support_email},
    )


def about(request):
    return render(request, "core/about.html")


def explore(request):
    q = request.GET.get("q", "").strip()
    language = request.GET.get("language", "").strip()
    difficulty = request.GET.get("difficulty", "").strip()
    foundation = request.GET.get("foundation", "").strip()
    max_size = request.GET.get("max_size", "").strip()
    sort = request.GET.get("sort", "stars").strip()
    page_number = request.GET.get("page", "1")

    # Cache the filtered id list (not rendered HTML) so the navbar is always
    # rendered for the current request. Fixes #38: anonymous HTML served to
    # logged-in users when the whole page was cached.
    ids_key = cache_key(
        "explore",
        "ids",
        q,
        language,
        difficulty,
        foundation,
        max_size,
        sort,
    )
    issue_ids = cache_get(ids_key)
    if issue_ids is None:
        issues = Issue.objects.filter(is_assigned=False)

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
            issues = issues.filter(repo_size_kb__lt=int(max_size))

        issues = issues.order_by(SORT_OPTIONS.get(sort, "-stars_count"))
        issue_ids = list(issues.values_list("pk", flat=True))
        cache_set(ids_key, issue_ids, CACHE_TTL)

    paginator = Paginator(issue_ids, PAGE_SIZE)
    page_obj = paginator.get_page(page_number)
    ordered_ids = list(page_obj.object_list)
    issues_by_pk = {
        issue.pk: issue
        for issue in Issue.objects.filter(pk__in=ordered_ids).only(*ISSUE_LIST_FIELDS)
    }
    page_obj.object_list = [
        issues_by_pk[pk] for pk in ordered_ids if pk in issues_by_pk
    ]

    # Querystring carrying every active filter (minus `page`) so pagination
    # links preserve the current search context.
    params = {
        k: v
        for k, v in {
            "q": q,
            "language": language,
            "difficulty": difficulty,
            "foundation": foundation,
            "max_size": max_size,
            "sort": sort,
        }.items()
        if v
    }
    querystring = urlencode(params)

    languages_key = cache_key("explore", "languages")
    languages = cache_get(languages_key)
    if languages is None:
        languages = list(
            Issue.objects.exclude(language__isnull=True)
            .exclude(language="")
            .values_list("language", flat=True)
            .distinct()
            .order_by("language")
        )
        cache_set(languages_key, languages, CACHE_TTL)

    foundations_key = cache_key("explore", "foundations")
    foundations = cache_get(foundations_key)
    if foundations is None:
        foundations = list(
            Issue.objects.exclude(foundation="")
            .values_list("foundation", flat=True)
            .distinct()
            .order_by("foundation")
        )
        cache_set(foundations_key, foundations, CACHE_TTL)

    context = {
        "page_obj": page_obj,
        "total_count": paginator.count,
        "querystring": querystring,
        "languages": languages,
        "foundations": foundations,
        "filters": {
            "q": q,
            "language": language,
            "difficulty": difficulty,
            "foundation": foundation,
            "max_size": max_size,
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
        .only(*ISSUE_LIST_FIELDS)
        .order_by("-beginner_friendly_score")[:3]
    )
    return render(
        request, "core/issue_detail.html", {"issue": issue, "related": related}
    )


def profile_view(request, username):
    profile = get_object_or_404(
        Profile.objects.select_related("user"), github_username=username
    )
    contributions = profile.user.contributions.select_related("issue").only(
        "id",
        "user_id",
        "issue_id",
        "repo_full_name",
        "title",
        "pr_url",
        "kind",
        "merged_at",
        "verified",
        "created_at",
    )
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

    # Cache only the computed rows (not rendered HTML), so the template is
    # rendered per request. This also fixes #38 (anonymous navbar served to
    # logged-in users) and means pagination doesn't need page in the key.
    rows_key = cache_key("leaderboard", "rows", country.lower() or "all")
    profiles = cache_get(rows_key)
    if profiles is None:
        qs = (
            Profile.objects.select_related("user")
            .annotate(total=Count("user__contributions"))
            .filter(total__gt=0)
            .order_by("-total", "pk")  # pk tiebreaker = stable ranking across pages
        )
        if country:
            qs = qs.filter(country__iexact=country)
        profiles = list(qs)  # no [:50] slice any more
        cache_set(rows_key, profiles, CACHE_TTL)

    countries_key = cache_key("leaderboard", "countries")
    countries = cache_get(countries_key)
    if countries is None:
        countries = list(
            Profile.objects.exclude(country__isnull=True)
            .exclude(country="")
            .values_list("country", flat=True)
            .distinct()
            .order_by("country")
        )
        cache_set(countries_key, countries, CACHE_TTL)

    paginator = Paginator(profiles, LEADERBOARD_PAGE_SIZE)
    # get_page() handles ?page=abc and out-of-range values safely.
    page_obj = paginator.get_page(request.GET.get("page", "1"))
    page_rows = list(page_obj.object_list)

    on_first_page = page_obj.number == 1
    if on_first_page:
        podium, rest = page_rows[:3], page_rows[3:]
    else:
        podium, rest = [], page_rows

    # Rank of the row just before `rest` begins: 3 on page 1, 50 on page 2, ...
    rest_offset = max(page_obj.start_index() - 1, 0) + (len(podium))

    querystring = urlencode({"country": country}) if country else ""

    return render(
        request,
        "core/leaderboard.html",
        {
            "profiles": page_rows,
            "podium": podium,
            "rest": rest,
            "rest_offset": rest_offset,
            "top": profiles[0] if (profiles and on_first_page) else None,
            "page_obj": page_obj,
            "querystring": querystring,
            "countries": countries,
            "selected_country": country,
        },
    )


@require_http_methods(["GET", "HEAD"])
def health(request):
    """Cheap liveness check for the keep-alive cron.

    Must not touch the database or the cache: Render's cold start plus a DB
    query is what made cron-job.org time out and disable the job.
    """
    return HttpResponse("ok", content_type="text/plain")


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
            logger.info(
                "Background fetch_issues finished: %s issues",
                processed,
                extra={"event": "fetch_issues_ok"},
            )
        except Exception:
            logger.exception(
                "Background fetch_issues failed",
                extra={"event": "fetch_issues_error"},
            )

    threading.Thread(target=_run, name="fetch-issues", daemon=True).start()
    return JsonResponse(
        {"ok": True, "started": True, "pages": pages, "mode": "async"},
        status=202,
    )


def llms_txt(request):
    """Serve a short, structured llms.txt description for AI search and crawlers."""
    text = (
        "# OpenToAll\n"
        "> Find an open source issue you can actually clone and finish. "
        "Built for developers who need a realistic first contribution.\n\n"
        "## Core Pages\n"
        "- [Home](https://opentoall.onrender.com/): Platform overview and curated issues\n"
        "- [About](https://opentoall.onrender.com/about/): Short product pitch and built-by credit\n"
        "- [Support](https://opentoall.onrender.com/support/): Reach the team without opening a GitHub issue\n"
        "- [Explore](https://opentoall.onrender.com/explore/): Search and browse filtered beginner-friendly issues\n"
        "- [Leaderboard](https://opentoall.onrender.com/leaderboard/): Community contributors and open source milestones\n\n"
        "## Source code\n"
        "- [GitHub repository](https://github.com/Ymax27/opentoall): Source code, open issues and contribution guide\n\n"
        "## Optional\n"
        "- [Login](https://opentoall.onrender.com/accounts/login/): GitHub OAuth login\n"
    )
    return HttpResponse(text, content_type="text/plain; charset=utf-8")

def robots_txt(request):
    """Serve robots.txt: allow public pages, hide admin/internal, point to the sitemap."""
    text = (
        "User-agent: *\n"
        "Disallow: /admin/\n"
        "Disallow: /internal/\n"
        "Disallow: /accounts/\n"
        "Allow: /\n\n"
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}\n"
    )
    return HttpResponse(text, content_type="text/plain; charset=utf-8")

@x_robots_tag
def sitemap_xml(request):
    """sitemap.xml with absolute URLs built from the request host."""
    site = RequestSite(request)
    protocol = "https" if request.is_secure() else "http"
    urls = []
    for section in sitemap_classes.values():
        urls.extend(section().get_urls(site=site, protocol=protocol))
    return TemplateResponse(
        request,
        "sitemap.xml",
        {"urlset": urls},
        content_type="application/xml",
    )