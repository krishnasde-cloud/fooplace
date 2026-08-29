import json
from io import BytesIO

from django.test import SimpleTestCase

from fooplace.vercel_wsgi import application, django_path_info


class DjangoPathInfoTests(SimpleTestCase):
    def test_preserves_and_restores_api_paths(self):
        self.assertEqual(
            {
                "full": django_path_info({"PATH_INFO": "/api/health/"}),
                "rewritten": django_path_info(
                    {"PATH_INFO": "/api", "REQUEST_URI": "/api/health/?x=1"}
                ),
                "stripped": django_path_info({"PATH_INFO": "/health/"}),
            },
            {
                "full": "/api/health/",
                "rewritten": "/api/health/",
                "stripped": "/api/health/",
            },
        )


class VercelWsgiTests(SimpleTestCase):
    def test_health_when_path_rewritten_to_function_root(self):
        status_headers: dict[str, str] = {}

        def start_response(status: str, _headers: list) -> None:
            status_headers["status"] = status

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
        body = b"".join(application(environ, start_response))
        self.assertEqual(
            {"status": status_headers["status"], "body": json.loads(body)},
            {
                "status": "200 OK",
                "body": {"status": "ok", "service": "fooplace-backend"},
            },
        )
