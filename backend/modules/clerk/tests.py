import os
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

from modules.clerk.authorized_parties import (
    merge_authorized_parties,
    request_frontend_origins,
    vercel_frontend_origins,
)
from modules.clerk.clerk_auth import verify_clerk_request
from modules.users.models import User


class ClerkAuthTests(TestCase):
    def test_me_requires_clerk_session(self):
        response = self.client.get("/api/me/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"detail": AuthErrorReason.SESSION_TOKEN_MISSING.name},
        )

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_me_returns_clerk_user(self, mock_authenticate):
        mock_authenticate.return_value = RequestState(
            status=AuthStatus.SIGNED_IN,
            token="sess_test",
            payload={"sub": "user_abc", "sid": "sess_1"},
        )
        response = self.client.get("/api/me/", HTTP_AUTHORIZATION="Bearer sess_test")
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(user_id="user_abc")
        self.assertEqual(
            response.json(),
            {**user.as_api(), "session_id": "sess_1"},
        )

    @patch("modules.clerk.clerk_auth.authenticate_request")
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
    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_verify_passes_session_token_and_authorized_parties(self, mock_authenticate):
        mock_authenticate.return_value = RequestState(
            status=AuthStatus.SIGNED_OUT,
            reason=AuthErrorReason.SESSION_TOKEN_MISSING,
        )
        factory_request = RequestFactory().get(
            "/api/me/", HTTP_ORIGIN="https://project-7tqn4.vercel.app"
        )
        verify_clerk_request(factory_request)
        request, options = mock_authenticate.call_args.args
        self.assertEqual(request.path, "/api/me/")
        self.assertEqual(
            options,
            AuthenticateRequestOptions(
                secret_key="sk_test",
                jwt_key=None,
                authorized_parties=[
                    "https://fooplace.example",
                    "https://project-7tqn4.vercel.app",
                    "http://testserver",
                ],
                accepts_token=["session_token"],
            ),
        )


class AuthorizedPartiesTests(TestCase):
    def test_vercel_hosts_include_production_alias(self):
        self.assertEqual(
            vercel_frontend_origins(
                {
                    "VERCEL_URL": "project-7tqn4-awtxdckm0-k-corpp.vercel.app",
                    "VERCEL_PROJECT_PRODUCTION_URL": "project-7tqn4.vercel.app",
                    "VERCEL_BRANCH_URL": "project-7tqn4-git-main-k-corpp.vercel.app",
                }
            ),
            [
                "https://project-7tqn4-awtxdckm0-k-corpp.vercel.app",
                "https://project-7tqn4-git-main-k-corpp.vercel.app",
                "https://project-7tqn4.vercel.app",
            ],
        )

    def test_request_origin_covers_production_alias(self):
        request = RequestFactory().get(
            "/api/me/",
            HTTP_ORIGIN="https://project-7tqn4.vercel.app",
        )
        configured = [
            "http://localhost:5173",
            "https://project-7tqn4-awtxdckm0-k-corpp.vercel.app",
        ]
        self.assertEqual(
            {
                "from_request": request_frontend_origins(request),
                "merged": merge_authorized_parties(configured, request),
            },
            {
                "from_request": [
                    "https://project-7tqn4.vercel.app",
                    "http://testserver",
                ],
                "merged": [
                    "http://localhost:5173",
                    "https://project-7tqn4-awtxdckm0-k-corpp.vercel.app",
                    "https://project-7tqn4.vercel.app",
                    "http://testserver",
                ],
            },
        )

    @patch.dict(os.environ, {"VERCEL": "1"})
    def test_vercel_request_host_uses_https(self):
        request = RequestFactory().get(
            "/api/me/", HTTP_HOST="project-7tqn4.vercel.app"
        )
        self.assertEqual(
            request_frontend_origins(request),
            ["https://project-7tqn4.vercel.app"],
        )
