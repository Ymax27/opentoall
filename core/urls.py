from django.urls import path
from django.views.generic import RedirectView, TemplateView

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("support/", views.support, name="support"),
    path(
        "mentions-legales/",
        TemplateView.as_view(template_name="core/legal.html"),
        name="legal",
    ),
    path(
        "contact/",
        RedirectView.as_view(pattern_name="support", permanent=True),
        name="contact_redirect",
    ),
    path("explore/", views.explore, name="explore"),
    path("issue/<int:pk>/", views.issue_detail, name="issue_detail"),
    path("u/<str:username>/", views.profile_view, name="profile"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("internal/health/", views.health, name="health"),
    path(
        "internal/fetch-issues/",
        views.fetch_issues_trigger,
        name="fetch_issues_trigger",
    ),
    path("llms.txt", views.llms_txt, name="llms_txt"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap_xml"),
]
