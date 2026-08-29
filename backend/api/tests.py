from unittest.mock import patch

from clerk_backend_api.security.types import (
    AuthenticateRequestOptions,
    AuthErrorReason,
    AuthStatus,
    RequestState,
    TokenVerificationErrorReason,
)
from django.contrib.auth import authenticate
from django.test import RequestFactory, TestCase, override_settings

from api.clerk_auth import verify_clerk_request


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

    @override_settings(
        CLERK_SECRET_KEY="sk_test",
        CLERK_JWT_KEY=None,
        CLERK_AUTHORIZED_PARTIES=["https://fooplace.example"],
    )
    @patch("api.clerk_auth.authenticate_request")
    def test_verify_passes_session_token_and_authorized_parties(self, mock_authenticate):
        mock_authenticate.return_value = RequestState(
            status=AuthStatus.SIGNED_OUT,
            reason=AuthErrorReason.SESSION_TOKEN_MISSING,
        )
        verify_clerk_request(RequestFactory().get("/api/me/"))
        request, options = mock_authenticate.call_args.args
        self.assertEqual(request.path, "/api/me/")
        self.assertEqual(
            options,
            AuthenticateRequestOptions(
                secret_key="sk_test",
                jwt_key=None,
                authorized_parties=["https://fooplace.example"],
                accepts_token=["session_token"],
            ),
        )
