import json
from io import BytesIO

from django.test import SimpleTestCase

from fooplace.vercel_wsgi import application, django_path_info


def _wsgi_call(environ: dict) -> tuple[str, dict]:
    status_headers: dict[str, str] = {}

    def start_response(status: str, _headers: list) -> None:
        status_headers["status"] = status

    body = b"".join(application(environ, start_response))
    return status_headers["status"], json.loads(body)


def _health_environ(**overrides: str) -> dict:
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/api",
        "REQUEST_URI": "/api/health/",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "443",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "https",
        "wsgi.input": BytesIO(),
        "wsgi.errors": BytesIO(),
        "wsgi.multithread": False,
        "wsgi.multiprocess": True,
        "wsgi.run_once": False,
    }
    environ.update(overrides)
    return environ


class DjangoPathInfoTests(SimpleTestCase):
    def test_preserves_and_restores_api_paths(self):
        self.assertEqual(
            {
                "full": django_path_info({"PATH_INFO": "/api/health/"}),
                "rewritten": django_path_info(
                    {"PATH_INFO": "/api", "REQUEST_URI": "/api/health/?x=1"}
                ),
                "stripped": django_path_info({"PATH_INFO": "/health/"}),
                "prefers_specific_over_function_root": django_path_info(
                    {"PATH_INFO": "/api/health/", "REQUEST_URI": "/api"}
                ),
                "admin_rewritten": django_path_info(
                    {"PATH_INFO": "/api", "REQUEST_URI": "/admin/"}
                ),
                "admin_direct": django_path_info({"PATH_INFO": "/admin/users/user/"}),
            },
            {
                "full": "/api/health/",
                "rewritten": "/api/health/",
                "stripped": "/api/health/",
                "prefers_specific_over_function_root": "/api/health/",
                "admin_rewritten": "/admin/",
                "admin_direct": "/admin/users/user/",
            },
        )


class VercelWsgiTests(SimpleTestCase):
    def test_health_when_path_rewritten_to_function_root(self):
        status, body = _wsgi_call(_health_environ())
        self.assertEqual(
            {"status": status, "body": body},
            {
                "status": "200 OK",
                "body": {"status": "ok", "service": "fooplace-backend"},
            },
        )

    def test_health_when_function_root_is_in_request_uri(self):
        status, body = _wsgi_call(
            _health_environ(PATH_INFO="/api/health/", REQUEST_URI="/api")
        )
        self.assertEqual(
            {"status": status, "body": body},
            {
                "status": "200 OK",
                "body": {"status": "ok", "service": "fooplace-backend"},
            },
        )
