import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# django-environ reads key=value pairs from a .env file
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Core Django
# ---------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "api"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt",
    "django_ratelimit",
    # local
    "apps.parser",
    "apps.users",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # must be before CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database — loaded from DATABASE_URL env var
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgresql://postgres:postgres@localhost:5432/resume_parser",
    )
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    # Phase 2: all endpoints require a valid JWT access token by default.
    # Individual views that must be public (register, login, refresh) override
    # this with permission_classes = [AllowAny].
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ---------------------------------------------------------------------------
# JWT — access tokens expire in 1 hour; refresh tokens last 7 days
# ---------------------------------------------------------------------------
from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Keep issued-at claim so tokens can be inspected for debugging
    "UPDATE_LAST_LOGIN": True,
}

# ---------------------------------------------------------------------------
# CORS — which frontend origins can call this API
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000", "http://localhost:5173"],
)

# ---------------------------------------------------------------------------
# Local file storage (no S3 in Phase 1)
# ---------------------------------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))

UPLOAD_SETTINGS = {
    "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10 MB
    "ALLOWED_EXTENSIONS": [".pdf"],
}

# ---------------------------------------------------------------------------
# Cache — django-ratelimit requires a shared cache; point it at Redis so it
# works correctly across multiple API worker processes.
# Uses Redis database 1 (Celery uses database 0).
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("CELERY_BROKER_URL", default="redis://localhost:6379/1"),
    }
}

# ---------------------------------------------------------------------------
# Celery — async task queue backed by Redis
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "UTC"

# ---------------------------------------------------------------------------
# LLM — Anthropic Claude
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")

LLM_SETTINGS = {
    "MODEL": env("LLM_MODEL", default="claude-haiku-4-5-20251001"),
    "MAX_TOKENS": int(env("LLM_MAX_TOKENS", default="2000")),
    "TEMPERATURE": float(env("LLM_TEMPERATURE", default="0.1")),
    "MAX_RETRIES": int(env("LLM_MAX_RETRIES", default="3")),
}

# ---------------------------------------------------------------------------
# Internationalisation / static files
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} — {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "loggers": {
        "apps.parser": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        }
    },
}
