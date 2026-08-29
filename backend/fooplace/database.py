"""Build Django DATABASES from DATABASE_URL, Postgres env vars, or SQLite."""

from __future__ import annotations

import os
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any


def postgres_from_url(raw: str) -> dict[str, Any]:
    url = urllib.parse.urlparse(raw)
    query = urllib.parse.parse_qs(url.query)
    config: dict[str, Any] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": url.path.lstrip("/"),
        "USER": urllib.parse.unquote(url.username) if url.username else "",
        "PASSWORD": urllib.parse.unquote(url.password) if url.password else "",
        "HOST": url.hostname or "",
        "PORT": str(url.port or "5432"),
    }
    if "sslmode" in query:
        config["OPTIONS"] = {"sslmode": query["sslmode"][0]}
    return config


def postgres_from_env() -> dict[str, Any]:
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "fooplace"),
        "USER": os.environ.get("POSTGRES_USER", "fooplace"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "fooplace"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }


def sqlite_default(base_dir: Path) -> dict[str, Any]:
    db_dir = base_dir if os.access(base_dir, os.W_OK) else Path(tempfile.gettempdir()) / "fooplace"
    db_dir.mkdir(parents=True, exist_ok=True)
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("FOOPLACE_DB", str(db_dir / "db.sqlite3")),
    }


def databases(*, base_dir: Path) -> dict[str, dict[str, Any]]:
    """Postgres is the application database.

    Set FOOPLACE_USE_SQLITE=1 for hermetic unit tests (Bazel) that should not
    need a running Postgres. DATABASE_URL wins over discrete POSTGRES_* vars.
    """
    if os.environ.get("FOOPLACE_USE_SQLITE") == "1":
        return {"default": sqlite_default(base_dir)}
    raw = os.environ.get("DATABASE_URL")
    if raw:
        return {"default": postgres_from_url(raw)}
    return {"default": postgres_from_env()}
