"""ASGI config for fooplace."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fooplace.settings")

application = get_asgi_application()
