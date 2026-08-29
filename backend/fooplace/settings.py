"""Django 6.1 settings for the fooplace backend."""

import os
from pathlib import Path

from fooplace.database import databases

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-fooplace-dev-only-change-me",
)

_ON_VERCEL = bool(os.environ.get("VERCEL"))
_debug_default = "false" if _ON_VERCEL else "true"
DEBUG = os.environ.get("DJANGO_DEBUG", _debug_default).lower() in {"1", "true", "yes"}

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")
    if host.strip()
]
if _ON_VERCEL:
    ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
if _ON_VERCEL:
    CSRF_TRUSTED_ORIGINS.append("https://*.vercel.app")
    if os.environ.get("VERCEL_URL"):
        CSRF_TRUSTED_ORIGINS.append(f"https://{os.environ['VERCEL_URL']}")

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


def _csv_env(name: str, default: str = "") -> list[str]:
    return [
        item.strip()
        for item in os.environ.get(name, default).split(",")
        if item.strip()
    ]


# Required on Vercel (Django runs there) and locally to verify session JWTs.
CLERK_SECRET_KEY = os.environ.get("CLERK_SECRET_KEY", "")
# Optional PEM public key for networkless verification (Dashboard → API keys).
CLERK_JWT_KEY = os.environ.get("CLERK_JWT_KEY") or None
# Frontend origins allowed in the session token azp claim.
# CLERK_AUTHORIZED_PARTIES is already set on Vercel; local default is Vite.
CLERK_AUTHORIZED_PARTIES = _csv_env(
    "CLERK_AUTHORIZED_PARTIES",
    "http://localhost:5173,http://127.0.0.1:5173",
)
if os.environ.get("VERCEL_URL"):
    vercel_origin = f"https://{os.environ['VERCEL_URL']}"
    if vercel_origin not in CLERK_AUTHORIZED_PARTIES:
        CLERK_AUTHORIZED_PARTIES.append(vercel_origin)

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

DATABASES = databases(base_dir=BASE_DIR)

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
STATIC_ROOT = BASE_DIR / "staticfiles"

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
