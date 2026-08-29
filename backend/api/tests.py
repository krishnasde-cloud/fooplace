from unittest.mock import patch

from clerk_backend_api.security.types import (
    AuthErrorReason,
    AuthStatus,
    RequestState,
    TokenVerificationErrorReason,
)
from django.contrib.auth import authenticate
from django.test import TestCase


class HealthTests(TestCase):
    def test_health_returns_ok(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "fooplace-backend"},
        )


class ClerkAuthTests(TestCase):
    def test_me_requires_clerk_session(self):
        response = self.client.get("/api/me/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"detail": AuthErrorReason.SESSION_TOKEN_MISSING.name},
        )

    @patch("api.clerk_auth.authenticate_request")
    def test_me_returns_clerk_user(self, mock_authenticate):
        mock_authenticate.return_value = RequestState(
            status=AuthStatus.SIGNED_IN,
            token="sess_test",
            payload={"sub": "user_abc", "sid": "sess_1"},
        )
        response = self.client.get("/api/me/", HTTP_AUTHORIZATION="Bearer sess_test")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"user_id": "user_abc", "session_id": "sess_1"},
        )

    @patch("api.clerk_auth.authenticate_request")
    def test_invalid_clerk_token_is_rejected(self, mock_authenticate):
        mock_authenticate.return_value = RequestState(
            status=AuthStatus.SIGNED_OUT,
            reason=TokenVerificationErrorReason.TOKEN_INVALID,
        )
        response = self.client.get("/api/health/", HTTP_AUTHORIZATION="Bearer not-a-jwt")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"detail": TokenVerificationErrorReason.TOKEN_INVALID.name},
        )

    def test_password_authenticate_is_disabled(self):
        self.assertIsNone(authenticate(username="anyone", password="secret"))
