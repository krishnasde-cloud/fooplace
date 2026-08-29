"""WSGI app Vercel loads from ``api/index.py``.

File-based Python functions must live under ``/api``. Vercel routes nested
``/api/...`` requests onto that function, so this wrapper restores Django's
URLConf path when PATH_INFO has been collapsed to the function root.
"""

from __future__ import annotations

from urllib.parse import unquote, urlsplit

from fooplace.wsgi import application as _django

_FUNCTION_ROOTS = frozenset({"/api", "/api/"})


def _normalize(path: str) -> str:
    if not path.startswith("/"):
        return f"/{path}"
    return path


def _is_django_path(path: str) -> bool:
    return path == "/api" or path.startswith("/api/") or path == "/admin" or path.startswith("/admin/")


def django_path_info(environ: dict) -> str:
    path = _normalize(environ.get("PATH_INFO") or "/")
    raw = environ.get("REQUEST_URI") or environ.get("RAW_URI") or ""
    orig = unquote(urlsplit(raw).path) if raw else ""
    orig = _normalize(orig) if orig else ""

    candidates = [candidate for candidate in (path, orig) if _is_django_path(candidate)]
    specific = [candidate for candidate in candidates if candidate not in _FUNCTION_ROOTS]
    if specific:
        return max(specific, key=len)
    if candidates:
        return "/api"

    return "/api" if path == "/" else f"/api{path}"


def application(environ: dict, start_response):
    path = django_path_info(environ)
    if path != environ.get("PATH_INFO"):
        environ = {**environ, "PATH_INFO": path, "SCRIPT_NAME": ""}
    return _django(environ, start_response)


app = application
