from types import SimpleNamespace
from unittest.mock import patch

from clerk_backend_api.security.types import AuthStatus, RequestState
from django.test import TestCase
from django.utils import timezone

from api.models import User
from api.user_sync import ClerkProfile, profile_from_clerk_user


def _signed_in(payload: dict) -> RequestState:
    return RequestState(
        status=AuthStatus.SIGNED_IN,
        token="sess_test",
        payload=payload,
    )


class UserLinkTests(TestCase):
    @patch("api.clerk_auth.authenticate_request")
    def test_me_creates_user_from_clerk_session(self, mock_authenticate):
        mock_authenticate.return_value = _signed_in(
            {
                "sub": "user_abc",
                "sid": "sess_1",
                "email": "buyer@example.com",
                "email_verified": True,
                "connected_using": "google",
            }
        )
        response = self.client.get("/api/me/", HTTP_AUTHORIZATION="Bearer sess_test")
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(
            user_id="user_abc",
            email="buyer@example.com",
            connected_using="google",
            user_type=User.UserType.BUYER,
            is_active=True,
            is_verified=True,
        )
        self.assertEqual(
            response.json(),
            {**user.as_api(), "session_id": "sess_1"},
        )

    @patch("api.user_sync.fetch_clerk_profile")
    @patch("api.clerk_auth.authenticate_request")
    def test_me_fills_profile_from_clerk(self, mock_authenticate, mock_fetch):
        mock_fetch.return_value = ClerkProfile(
            email="buyer@example.com",
            connected_using="google",
            is_verified=True,
            is_active=True,
        )
        mock_authenticate.return_value = _signed_in(
            {"sub": "user_abc", "sid": "sess_1"}
        )
        response = self.client.get("/api/me/", HTTP_AUTHORIZATION="Bearer sess_test")
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(
            user_id="user_abc",
            email="buyer@example.com",
            connected_using="google",
            user_type=User.UserType.BUYER,
            is_active=True,
            is_verified=True,
        )
        self.assertEqual(
            response.json(),
            {**user.as_api(), "session_id": "sess_1"},
        )

    @patch("api.clerk_auth.authenticate_request")
    def test_second_sign_in_updates_the_same_user(self, mock_authenticate):
        first = timezone.now()
        User.objects.create(
            user_id="user_abc",
            email="buyer@example.com",
            connected_using="google",
            user_type=User.UserType.SELLER,
            is_active=True,
            is_verified=True,
            first_logged_in=first,
            last_logged_in=first,
        )
        mock_authenticate.return_value = _signed_in(
            {"sub": "user_abc", "sid": "sess_2"}
        )
        response = self.client.get("/api/me/", HTTP_AUTHORIZATION="Bearer sess_test")
        user = User.objects.get(user_id="user_abc")
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.user_type, User.UserType.SELLER)
        self.assertEqual(user.first_logged_in, first)
        self.assertGreaterEqual(user.last_logged_in, first)
        self.assertEqual(
            response.json(),
            {**user.as_api(), "session_id": "sess_2"},
        )

    @patch("api.clerk_auth.authenticate_request")
    def test_inactive_user_is_rejected(self, mock_authenticate):
        now = timezone.now()
        User.objects.create(
            user_id="user_abc",
            email="buyer@example.com",
            is_active=False,
            first_logged_in=now,
            last_logged_in=now,
        )
        mock_authenticate.return_value = _signed_in(
            {"sub": "user_abc", "sid": "sess_1"}
        )
        response = self.client.get("/api/me/", HTTP_AUTHORIZATION="Bearer sess_test")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "inactive"})


class ClerkProfileTests(TestCase):
    def test_profile_from_clerk_user(self):
        clerk_user = SimpleNamespace(
            primary_email_address_id="idn_1",
            email_addresses=[
                SimpleNamespace(
                    id="idn_1",
                    email_address="buyer@example.com",
                    verification=SimpleNamespace(status="verified"),
                )
            ],
            external_accounts=[SimpleNamespace(provider="oauth_google")],
            password_enabled=False,
            banned=False,
            locked=False,
        )
        self.assertEqual(
            profile_from_clerk_user(clerk_user),
            ClerkProfile(
                email="buyer@example.com",
                connected_using="google",
                is_verified=True,
                is_active=True,
            ),
        )
