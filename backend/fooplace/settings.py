"""Django 6.1 settings for the fooplace backend."""

import os
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-fooplace-dev-only-change-me",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in {"1", "true", "yes"}

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Clerk is the only auth. This overwrites session users on every request.
    "api.clerk_auth.ClerkAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Clerk session tokens only — no ModelBackend / password / session login.
AUTHENTICATION_BACKENDS = [
    "api.clerk_auth.ClerkBackend",
]

# Required on the Django host to verify Clerk JWTs (not used by the Vite SPA).
# Add on the API server; skip on Vercel unless Django is also deployed there.
CLERK_SECRET_KEY = os.environ.get("CLERK_SECRET_KEY", "")
# Optional PEM public key for networkless verification (Dashboard → API keys).
CLERK_JWT_KEY = os.environ.get("CLERK_JWT_KEY") or None
# Frontend origins allowed in the session token azp claim.
CLERK_AUTHORIZED_PARTIES = [
    party.strip()
    for party in os.environ.get(
        "CLERK_AUTHORIZED_PARTIES",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if party.strip()
]

ROOT_URLCONF = "fooplace.urls"

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

WSGI_APPLICATION = "fooplace.wsgi.application"

_default_db_dir = BASE_DIR if os.access(BASE_DIR, os.W_OK) else Path(tempfile.gettempdir()) / "fooplace"
_default_db_dir.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("FOOPLACE_DB", str(_default_db_dir / "db.sqlite3")),
    }
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

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "FOOPLACE_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
