"""
Django settings for core project.
"""

from pathlib import Path
import os
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-CHANGE-THIS-IN-PRODUCTION")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,.onrender.com",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()],
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "channels",
    "game",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

_db_url = config("DATABASE_URL", default="")
DATABASES = {
    "default": dj_database_url.config(
        default=_db_url or f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}",
        conn_max_age=600,
        conn_health_checks=bool(_db_url),
        ssl_require=not DEBUG and bool(_db_url),
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

TELEGRAM_BOT_TOKEN = config("TELEGRAM_BOT_TOKEN", default="")
JWT_SECRET_KEY = config("JWT_SECRET_KEY", default="CHANGE_THIS_TO_A_RANDOM_SECRET")
JWT_ALGORITHM = config("JWT_ALGORITHM", default="HS256")
JWT_EXP_DELTA_SECONDS = config("JWT_EXP_DELTA_SECONDS", default=60 * 60 * 24, cast=int)

CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=DEBUG, cast=bool)
CORS_ALLOW_CREDENTIALS = True

def _normalize_origins(value):
    """Split, strip, and remove trailing slashes to match browser Origin header."""
    if not value:
        return []
    return [s.strip().rstrip("/") for s in value.split(",") if s.strip()]


if not CORS_ALLOW_ALL_ORIGINS:
    _origins = config("CORS_ALLOWED_ORIGINS", default="")
    CORS_ALLOWED_ORIGINS = _normalize_origins(_origins)

# CSRF trusted origins - required when frontend is on a different origin (e.g. ngrok)
_csrf_origins = config("CSRF_TRUSTED_ORIGINS", default="")
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = _normalize_origins(_csrf_origins)

# Production security
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
