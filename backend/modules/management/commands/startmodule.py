import keyword
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from modules.scaffold import write_module


class Command(BaseCommand):
    help = "Create a feature module under backend/modules and frontend/src/modules."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Python identifier used as the module folder name.")
        parser.add_argument(
            "--backend-only",
            action="store_true",
            help="Skip creating the matching frontend module.",
        )

    def handle(self, *args, **options):
        name = options["name"]
        if not name.isidentifier() or keyword.iskeyword(name) or name.startswith("_"):
            raise CommandError(
                f"{name!r} is not a valid module name. Use a Python identifier such as places."
            )

        backend_root = Path(settings.BASE_DIR) / "modules"
        backend_dir = backend_root / name
        if backend_dir.exists():
            raise CommandError(f"Backend module already exists: {backend_dir}")

        frontend_root = None
        if not options["backend_only"]:
            frontend_root = Path(settings.BASE_DIR).parent / "frontend" / "src" / "modules"
            frontend_dir = frontend_root / name
            if frontend_dir.exists():
                raise CommandError(f"Frontend module already exists: {frontend_dir}")

        created = write_module(name, backend_root, frontend_root)
        for path in created:
            self.stdout.write(self.style.SUCCESS(f"Created {path}"))
        self.stdout.write(
            f"Module {name!r} is mounted at /api/{name}/. "
            "Import the frontend client from @/modules/"
            f"{name}/index.ts."
        )
