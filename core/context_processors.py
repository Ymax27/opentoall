from django.conf import settings


def site_globals(request):
    """Expose project-wide metadata to every template."""
    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "OpenToAll"),
        "GITHUB_REPO_URL": getattr(settings, "GITHUB_REPO_URL", ""),
        "nav_links": [
            ("home", "Accueil", "home"),
            ("explore", "Explorer", "travel_explore"),
            ("leaderboard", "Classement", "leaderboard"),
        ],
    }
