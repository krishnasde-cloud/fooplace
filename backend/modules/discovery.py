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
    """Mount each module that has ``urls.py`` at ``/api/<prefix>/``.

    Prefix defaults to the folder name. Set ``AppConfig.api_prefix`` to override
    (the clerk module uses ``me`` so ``GET /api/me/`` stays stable).
    """
    from django.apps import apps
    from django.urls import include, path

    patterns = []
    for name in iter_module_names():
        short = name.rsplit(".", 1)[-1]
        if not (MODULES_ROOT / short / "urls.py").is_file():
            continue
        config = apps.get_app_config(short)
        prefix = getattr(config, "api_prefix", short)
        patterns.append(path(f"api/{prefix}/", include((f"{name}.urls", short))))
    return patterns
