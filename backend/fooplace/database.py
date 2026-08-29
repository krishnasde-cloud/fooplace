"""Build Django DATABASES from DATABASE_URL (Neon/Vercel) or local SQLite."""

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
        "USER": url.username or "",
        "PASSWORD": url.password or "",
        "HOST": url.hostname or "",
        "PORT": str(url.port or ""),
    }
    if "sslmode" in query:
        config["OPTIONS"] = {"sslmode": query["sslmode"][0]}
    return config


def sqlite_default(base_dir: Path) -> dict[str, Any]:
    db_dir = base_dir if os.access(base_dir, os.W_OK) else Path(tempfile.gettempdir()) / "fooplace"
    db_dir.mkdir(parents=True, exist_ok=True)
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("FOOPLACE_DB", str(db_dir / "db.sqlite3")),
    }


def databases(*, base_dir: Path) -> dict[str, dict[str, Any]]:
    raw = os.environ.get("DATABASE_URL")
    if raw:
        return {"default": postgres_from_url(raw)}
    return {"default": sqlite_default(base_dir)}
