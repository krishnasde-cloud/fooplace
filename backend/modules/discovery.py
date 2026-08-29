"""Discover feature modules under ``backend/modules/``."""

from pathlib import Path

MODULES_ROOT = Path(__file__).resolve().parent


def iter_module_names() -> list[str]:
    """Return dotted Django app names for each feature module."""
    names: list[str] = []
    for child in sorted(MODULES_ROOT.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith(("_", ".")):
            continue
        if not (child / "apps.py").is_file():
            continue
        names.append(f"modules.{child.name}")
    return names


def module_urlpatterns():
    """Mount each module that has ``urls.py`` at ``/api/<name>/``."""
    from django.urls import include, path

    patterns = []
    for name in iter_module_names():
        short = name.rsplit(".", 1)[-1]
        if not (MODULES_ROOT / short / "urls.py").is_file():
            continue
        patterns.append(path(f"api/{short}/", include((f"{name}.urls", short))))
    return patterns
