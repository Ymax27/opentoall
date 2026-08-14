"""Create or update a Django superuser from environment variables.

Useful on Render free when the one-off Shell is unavailable:

    ADMIN_USERNAME=admin ADMIN_PASSWORD='…' ADMIN_EMAIL=you@example.com \\
      python manage.py bootstrap_admin
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create/update a superuser from ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_EMAIL."

    def handle(self, *args, **options):
        import os

        username = os.getenv("ADMIN_USERNAME", "").strip()
        password = os.getenv("ADMIN_PASSWORD", "").strip()
        email = os.getenv("ADMIN_EMAIL", "").strip() or "admin@example.com"

        if not username or not password:
            raise CommandError(
                "Set ADMIN_USERNAME and ADMIN_PASSWORD in the environment."
            )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} superuser '{username}'."))
