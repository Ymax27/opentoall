"""
Django settings for the OpenToAll project.

OpenToAll — plateforme de découverte et de valorisation de la contribution
open source, pensée pour les développeurs africains.

Documentation: https://docs.djangoproject.com/en/6.0/ref/settings/
"""

import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from a local .env file when present.
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def database_from_url(url: str, *, ssl_require: bool | None = None, conn_max_age: int = 600) -> dict:
    """Parse a Postgres DATABASE_URL (Neon / Render / Heroku-style) without extra deps.

    SSL defaults to required for remote hosts (Neon), and disabled for localhost.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")

    host = (parsed.hostname or "").lower()
    if ssl_require is None:
        ssl_require = host not in {"localhost", "127.0.0.1", "::1"}

    options = {}
    query = parse_qs(parsed.query)
    if "sslmode" in query:
        options["sslmode"] = query["sslmode"][0]
    elif ssl_require:
        options["sslmode"] = "require"

    config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/") or "postgres"),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname or "",
        "PORT": str(parsed.port or 5432),
        "CONN_MAX_AGE": conn_max_age,
    }
    if options:
        config["OPTIONS"] = options
    return config


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    # Development-only fallback so the project runs out of the box.
    "django-insecure-dev-only-change-me-in-production",
)

DEBUG = env_bool("DEBUG", False)

if not DEBUG and (
    not SECRET_KEY
    or SECRET_KEY.startswith("django-insecure")
    or SECRET_KEY in {"change-me-generate-with-django", "changeme"}
):
    raise ImproperlyConfigured(
        "Set a strong SECRET_KEY from the environment when DEBUG=False."
    )

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

# Render injects the public hostname automatically.
_render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)

if not DEBUG and ("*" in ALLOWED_HOSTS or not ALLOWED_HOSTS):
    raise ImproperlyConfigured(
        "ALLOWED_HOSTS must list exact production hostnames when DEBUG=False."
    )

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]
if _render_host:
    _render_origin = f"https://{_render_host}"
    if _render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_render_origin)


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    # Third-party
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.github",
    "django_celery_beat",
    "django_htmx",
    # Local
    "core",
]

SITE_ID = 1

try:
    import whitenoise  # noqa: F401

    HAS_WHITENOISE = True
except ImportError:  # pragma: no cover - optional in local dev
    HAS_WHITENOISE = False

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    *(["whitenoise.middleware.WhiteNoiseMiddleware"] if HAS_WHITENOISE else []),
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Priority:
#   1. SQLite when running tests (ignore local .env Postgres)
#   2. DATABASE_URL (Neon / Render / any managed Postgres)
#   3. USE_POSTGRES=1 with DB_* (docker-compose)
#   4. SQLite (local dev)
_RUNNING_TESTS = (
    os.getenv("PYTEST_CURRENT_TEST") is not None
    or os.getenv("PYTEST_VERSION") is not None
    or any("pytest" in arg for arg in sys.argv)
    or (len(sys.argv) >= 2 and sys.argv[1] == "test")
)

_database_url = os.getenv("DATABASE_URL", "").strip()
if _RUNNING_TESTS:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db_test.sqlite3",
        }
    }
elif _database_url:
    _ssl_env = os.getenv("DB_SSL_REQUIRE")
    _ssl_require = (
        None
        if _ssl_env is None or not str(_ssl_env).strip()
        else env_bool("DB_SSL_REQUIRE", True)
    )
    DATABASES = {
        "default": database_from_url(
            _database_url,
            ssl_require=_ssl_require,
            conn_max_age=600,
        )
    }
elif env_bool("USE_POSTGRES", False):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "opentoall"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ---------------------------------------------------------------------------
# Authentication (django-allauth + GitHub OAuth)
# ---------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SOCIALACCOUNT_PROVIDERS = {
    "github": {
        "APP": {
            "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
            "secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
        },
        "SCOPE": ["read:user", "user:email"],
    }
}

SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_EMAIL_VERIFICATION = "none"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static files (WhiteNoise for production serving)
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
if HAS_WHITENOISE:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# GitHub API
# ---------------------------------------------------------------------------
# Personal Access Token (classic or fine-grained) used for authenticated
# GitHub API calls. Raises the rate limit from 60 to 5000 requests/hour.
GITHUB_PAT = os.getenv("GITHUB_PAT", "")

# Shared secret for the cron-triggered ingestion endpoint (Render free tier).
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
FETCH_ISSUES_TOKEN = os.getenv("FETCH_ISSUES_TOKEN", "")


# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
# Optional: used by docker-compose (worker + beat). On Render free we skip
# Redis/Celery and call /internal/fetch-issues/ from cron-job.org instead.
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_TRANSPORT_OPTIONS = {
    # Ingestion can run long; keep visibility above soft_time_limit.
    "visibility_timeout": 60 * 60,
}

CELERY_BEAT_SCHEDULE = {
    "refresh-issues-every-6h": {
        "task": "core.tasks.fetch_all_issues",
        "schedule": 6 * 60 * 60,
    }
}


# ---------------------------------------------------------------------------
# Cache (Redis in production when REDIS_URL/CACHE_URL is set; LocMem in DEBUG)
# ---------------------------------------------------------------------------
_redis_url = os.getenv("REDIS_URL", "").strip()
_cache_url = os.getenv("CACHE_URL", "").strip()
_use_redis_cache = env_bool(
    "USE_REDIS_CACHE",
    default=(not DEBUG and bool(_cache_url or _redis_url)),
)
if _use_redis_cache and (_cache_url or _redis_url):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _cache_url or _redis_url,
            "KEY_PREFIX": "opentoall",
            "TIMEOUT": 60 * 12,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "opentoall-local",
            "TIMEOUT": 60 * 12,
        }
    }


# ---------------------------------------------------------------------------
# Security (hardened automatically when DEBUG is off)
# ---------------------------------------------------------------------------
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

_LOG_FORMAT = os.getenv("LOG_FORMAT", "json" if not DEBUG else "console").lower()
_LOG_HANDLERS = {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "json" if _LOG_FORMAT == "json" else "simple",
    }
}
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname}] {name}: {message}", "style": "{"},
        "json": {"()": "core.logging_formatters.JsonFormatter"},
    },
    "handlers": _LOG_HANDLERS,
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
    "loggers": {
        "core": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Optional Sentry (errors from Django views + Celery workers).
_SENTRY_DSN = os.getenv("SENTRY_DSN", "").strip()
if _SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=_SENTRY_DSN,
            integrations=[DjangoIntegration(), CeleryIntegration()],
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
            send_default_pii=False,
            environment=os.getenv("SENTRY_ENVIRONMENT", "production" if not DEBUG else "development"),
        )
    except ImportError:  # pragma: no cover
        pass


# ---------------------------------------------------------------------------
# Project metadata (exposed to templates via context processor)
# ---------------------------------------------------------------------------
SITE_NAME = "OpenToAll"
GITHUB_REPO_URL = os.getenv(
    "GITHUB_REPO_URL", "https://github.com/Ymax27/opentoall"
)
