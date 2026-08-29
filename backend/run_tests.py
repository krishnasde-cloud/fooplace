"""Run Django's test runner under Bazel."""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fooplace.settings")

import django
from django.conf import settings
from django.test.utils import get_runner

from modules.discovery import iter_module_names


def main() -> None:
    django.setup()
    TestRunner = get_runner(settings)
    failures = TestRunner().run_tests(["modules", *iter_module_names()])
    sys.exit(bool(failures))


if __name__ == "__main__":
    main()
