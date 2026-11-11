import json

from django.conf import settings
from django.templatetags.static import static

from core.services.repo_credit import built_by_context


def _json_ld(data: dict) -> str:
    """Serialise for a <script type="application/ld+json"> block.

    Escape "<", ">" and "&" so the payload can never close the script tag.
    """
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def site_globals(request):
    """Expose project-wide metadata to every template."""
    site_name = getattr(settings, "SITE_NAME", "OpenToAll")
    home_url = request.build_absolute_uri("/")
    logo_url = request.build_absolute_uri(static("img/logo.png"))

    organization = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site_name,
        "url": home_url,
        "logo": logo_url,
    }
    website = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site_name,
        "url": home_url,
    }
    webpage = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": site_name,
        "url": request.build_absolute_uri(request.path),
        "isPartOf": {"@type": "WebSite", "name": site_name, "url": home_url},
    }

    globals_ctx = {
        "SITE_NAME": site_name,
        "GITHUB_REPO_URL": getattr(settings, "GITHUB_REPO_URL", ""),
        "SUPPORT_EMAIL": getattr(
            settings, "SUPPORT_EMAIL", "linxconcept27@gmail.com"
        ),
        "nav_links": [
            ("home", "Accueil", "home"),
            ("explore", "Issues", "travel_explore"),
            ("leaderboard", "Classement", "leaderboard"),
        ],
        "json_ld_blocks": [
            _json_ld(organization),
            _json_ld(website),
            _json_ld(webpage),
        ],
    }
    globals_ctx.update(built_by_context())
    return globals_ctx
