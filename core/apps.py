import os

from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        import core.signals  # noqa: F401

        host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
        if not host:
            return
        try:
            from django.conf import settings
            from django.contrib.sites.models import Site

            Site.objects.update_or_create(
                pk=settings.SITE_ID,
                defaults={"domain": host, "name": getattr(settings, "SITE_NAME", "OpenToAll")},
            )
        except (OperationalError, ProgrammingError):
            # Database not ready yet (first migrate).
            pass
