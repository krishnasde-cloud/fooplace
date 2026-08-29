from django.test import SimpleTestCase

from fooplace.database import postgres_from_url


class PostgresUrlTests(SimpleTestCase):
    def test_postgres_from_url(self):
        self.assertEqual(
            postgres_from_url("postgresql://u:p@host:5432/db?sslmode=require"),
            {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "db",
                "USER": "u",
                "PASSWORD": "p",
                "HOST": "host",
                "PORT": "5432",
                "OPTIONS": {"sslmode": "require"},
            },
        )
