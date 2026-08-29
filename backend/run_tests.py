"""Run Django's test runner under Bazel."""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fooplace.settings")

import django
from django.conf import settings
from django.test.utils import get_runner


def main() -> None:
    django.setup()
    TestRunner = get_runner(settings)
    failures = TestRunner().run_tests(["api"])
    sys.exit(bool(failures))


if __name__ == "__main__":
    main()
