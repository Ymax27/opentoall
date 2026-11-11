from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Issue


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return ["home", "contact", "explore", "leaderboard"]

    def location(self, item):
        return reverse(item)


class IssueSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return Issue.objects.filter(is_assigned=False).order_by("pk")

    def lastmod(self, obj):
        return obj.issue_updated_at or obj.fetched_at

    def location(self, obj):
        return reverse("issue_detail", args=[obj.pk])


sitemaps = {"static": StaticViewSitemap, "issues": IssueSitemap}