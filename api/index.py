"""Vercel Python function for Django (must live under /api)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from fooplace.vercel_wsgi import app, application  # noqa: E402, F401
