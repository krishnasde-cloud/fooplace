"""WSGI app Vercel loads from ``api/index.py``.

File-based Python functions must live under ``/api``. This wrapper keeps
Django's URLConf (``/api/...``) when Vercel rewrites those requests onto
that function.
"""

from __future__ import annotations

from urllib.parse import unquote, urlsplit

from fooplace.wsgi import application as _django


def django_path_info(environ: dict) -> str:
    path = environ.get("PATH_INFO") or "/"
    raw = environ.get("REQUEST_URI") or environ.get("RAW_URI") or ""
    orig = unquote(urlsplit(raw).path) if raw else ""
    if orig.startswith("/api"):
        return orig
    if path.startswith("/api"):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return "/api" if path == "/" else f"/api{path}"


def application(environ: dict, start_response):
    path = django_path_info(environ)
    if path != environ.get("PATH_INFO"):
        environ = {**environ, "PATH_INFO": path, "SCRIPT_NAME": ""}
    return _django(environ, start_response)


app = application
