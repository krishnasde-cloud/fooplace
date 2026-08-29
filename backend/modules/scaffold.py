"""Create a new backend (and matching frontend) feature module."""

from __future__ import annotations

from pathlib import Path

BACKEND_FILES = (
    "__init__.py",
    "admin.py",
    "apps.py",
    "migrations/__init__.py",
    "models.py",
    "tests.py",
    "urls.py",
    "views.py",
)

FRONTEND_FILES = (
    "api.ts",
    "index.ts",
)


def class_name(module: str) -> str:
    return "".join(part.title() for part in module.split("_"))


def write_module(name: str, backend_root: Path, frontend_root: Path | None) -> list[str]:
    """Write module files. Returns repo-relative paths of created files."""
    created: list[str] = []
    for relative, contents in _backend_contents(name).items():
        path = backend_root / name / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
        created.append(str(path))

    if frontend_root is not None:
        for relative, contents in _frontend_contents(name).items():
            path = frontend_root / name / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)
            created.append(str(path))

    return created


def _backend_contents(name: str) -> dict[str, str]:
    cls = class_name(name)
    verbose = name.replace("_", " ")
    return {
        "__init__.py": "",
        "admin.py": f"# Register {verbose} models with the admin site here.\n",
        "apps.py": (
            "from django.apps import AppConfig\n"
            "\n"
            "\n"
            f"class {cls}Config(AppConfig):\n"
            '    default_auto_field = "django.db.models.BigAutoField"\n'
            f'    name = "modules.{name}"\n'
            f'    verbose_name = "{verbose}"\n'
        ),
        "migrations/__init__.py": "",
        "models.py": f"# Models for the {verbose} module.\n",
        "tests.py": (
            "from django.test import TestCase\n"
            "\n"
            "\n"
            f"class {cls}Tests(TestCase):\n"
            f'    """Tests for the {verbose} module."""\n'
            "\n"
        ),
        "urls.py": (
            "from django.urls import path\n"
            "\n"
            "from . import views\n"
            "\n"
            "urlpatterns = [\n"
            '    path("", views.index, name="index"),\n'
            "]\n"
        ),
        "views.py": (
            "from django.http import JsonResponse\n"
            "\n"
            "\n"
            "def index(_request):\n"
            f'    return JsonResponse({{"module": "{name}"}})\n'
        ),
    }


def _frontend_contents(name: str) -> dict[str, str]:
    return {
        "api.ts": (
            f'const PREFIX = "/api/{name}/";\n'
            "\n"
            "export async function fetchIndex(signal?: AbortSignal): Promise<unknown> {\n"
            "  const response = await fetch(PREFIX, { signal });\n"
            "  if (!response.ok) {\n"
            "    throw new Error(`Backend returned HTTP ${response.status}`);\n"
            "  }\n"
            "  return response.json();\n"
            "}\n"
        ),
        "index.ts": 'export { fetchIndex } from "./api.ts";\n',
    }
