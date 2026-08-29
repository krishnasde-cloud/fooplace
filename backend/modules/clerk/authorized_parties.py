"""Frontend origins allowed in a Clerk session token's azp claim.

Vercel serves the SPA on the production alias (project.vercel.app) while
VERCEL_URL is the unique deployment host. Clerk sets azp to the origin the
user signed in on, so both must be accepted or /api/me/ returns 401 and
the users_user row is never created.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

_VERCEL_HOST_ENV = (
    "VERCEL_URL",
    "VERCEL_BRANCH_URL",
    "VERCEL_PROJECT_PRODUCTION_URL",
)


def origin_from_host(host: str) -> str:
    host = host.strip()
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    return f"https://{host}"


def vercel_frontend_origins(environ: dict | None = None) -> list[str]:
    env = os.environ if environ is None else environ
    origins: list[str] = []
    for key in _VERCEL_HOST_ENV:
        raw = (env.get(key) or "").strip()
        if not raw:
            continue
        origin = origin_from_host(raw)
        if origin not in origins:
            origins.append(origin)
    return origins


def request_frontend_origins(request) -> list[str]:
    origins: list[str] = []
    for header in ("Origin", "Referer"):
        raw = request.headers.get(header)
        if not raw:
            continue
        parsed = urlparse(raw)
        if parsed.scheme and parsed.netloc:
            origin = f"{parsed.scheme}://{parsed.netloc}"
            if origin not in origins:
                origins.append(origin)

    host = request.get_host()
    if host:
        on_vercel = bool(os.environ.get("VERCEL"))
        scheme = "https" if on_vercel or request.is_secure() else request.scheme
        origin = f"{scheme}://{host}"
        if origin not in origins:
            origins.append(origin)
    return origins


def merge_authorized_parties(configured: list[str], request) -> list[str]:
    parties: list[str] = []
    for origin in [*configured, *request_frontend_origins(request)]:
        if origin and origin not in parties:
            parties.append(origin)
    return parties
