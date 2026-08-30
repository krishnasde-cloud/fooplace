from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command, get_commands
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from modules.discovery import iter_module_names
from modules.scaffold import BACKEND_FILES, FRONTEND_FILES, write_module


class DiscoveryTests(SimpleTestCase):
    def test_discovers_health_and_skips_non_apps(self):
        names = iter_module_names()
        self.assertIn("modules.health", names)
        self.assertIn("modules.clerk", names)
        self.assertIn("modules.users", names)
        self.assertIn("modules.signup", names)
        self.assertIn("modules.listings", names)
        self.assertIn("modules.orders", names)
        self.assertIn("modules.geoapify", names)
        self.assertIn("modules.admin_flow", names)
        self.assertIn("modules.listings", names)
        self.assertIn("modules.orders", names)
        self.assertNotIn("modules.management", names)


class ModuleUrlTests(TestCase):
    def test_health_and_me_are_mounted(self):
        self.assertEqual(
            {
                "health": reverse("health:health"),
                "me": reverse("clerk:me"),
                "listings": reverse("listings:collection"),
                "orders": reverse("orders:index"),
                "geoapify": reverse("geoapify:autocomplete"),
            },
            {
                "health": "/api/health/",
                "me": "/api/me/",
                "listings": "/api/listings/",
                "orders": "/api/orders/",
                "geoapify": "/api/geoapify/autocomplete/",
            },
        )


class ScaffoldTests(SimpleTestCase):
    def test_write_module_creates_backend_and_frontend_files(self):
        with TemporaryDirectory() as tmp:
            backend_root = Path(tmp) / "modules"
            frontend_root = Path(tmp) / "frontend"
            backend_root.mkdir()
            frontend_root.mkdir()
            created = write_module("places", backend_root, frontend_root)
            expected = [
                str(backend_root / "places" / name) for name in BACKEND_FILES
            ] + [str(frontend_root / "places" / name) for name in FRONTEND_FILES]
            self.assertEqual(created, expected)
            self.assertEqual(
                sorted(path.relative_to(backend_root / "places").as_posix() for path in (backend_root / "places").rglob("*") if path.is_file()),
                sorted(BACKEND_FILES),
            )
            self.assertEqual(
                sorted(path.relative_to(frontend_root / "places").as_posix() for path in (frontend_root / "places").rglob("*") if path.is_file()),
                sorted(FRONTEND_FILES),
            )


class StartmoduleCommandTests(SimpleTestCase):
    def test_startmodule_is_registered(self):
        self.assertIn("startmodule", get_commands())

    def test_rejects_invalid_name(self):
        with self.assertRaises(CommandError):
            call_command("startmodule", "my-places")
