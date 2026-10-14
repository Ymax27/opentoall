"""Ensure tests never pick up a local Postgres DATABASE_URL / USE_POSTGRES."""

import os

# Must run before Django settings are imported by pytest-django.
os.environ["USE_POSTGRES"] = "0"
os.environ.pop("DATABASE_URL", None)

# Disable Whitenoise manifest storage for tests to avoid collectstatic requirement
os.environ["DEBUG"] = "True"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest"
