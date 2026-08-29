"""WSGI config for fooplace."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fooplace.settings")

application = get_wsgi_application()
app = application
