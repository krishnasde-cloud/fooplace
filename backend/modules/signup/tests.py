import json
from unittest.mock import patch

from clerk_backend_api.security.types import AuthStatus, RequestState
from django.test import TestCase
from django.utils import timezone

from modules.geoapify.client import Place
from modules.users.models import User

QUEEN = Place(
    formatted="123 Queen St W, Toronto, ON, Canada",
    lat=43.652,
    lon=-79.38,
)


def _signed_in(payload: dict) -> RequestState:
    return RequestState(
        status=AuthStatus.SIGNED_IN,
        token="sess_test",
        payload=payload,
    )


def _auth_post(client, body: dict):
    return client.post(
        "/api/signup/",
        data=json.dumps(body),
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer sess_test",
    )


class SignupTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.user = User.objects.create(
            user_id="user_abc",
            email="buyer@example.com",
            first_logged_in=now,
            last_logged_in=now,
        )

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_buyer_signup(self, mock_authenticate):
        mock_authenticate.return_value = _signed_in(
            {"sub": "user_abc", "sid": "sess_1"}
        )
        response = _auth_post(self.client, {"type": "buyer"})
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                **self.user.as_api(),
                "type": User.UserType.BUYER,
                "seller": None,
                "session_id": "sess_1",
            },
        )

    @patch("modules.signup.complete.Geoapify.geocode", return_value=QUEEN)
    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_seller_signup(self, mock_authenticate, _mock_geocode):
        mock_authenticate.return_value = _signed_in(
            {"sub": "user_abc", "sid": "sess_1"}
        )
        payload = {
            "type": "seller",
            "has_food_handler_certification": True,
            "accepted_terms": True,
            "facebook_marketplace_url": "https://www.facebook.com/marketplace/profile/123",
            "etransfer_email": "payouts@example.com",
            "pickup_address": "123 Queen St W, Toronto",
        }
        response = _auth_post(self.client, payload)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {**self.user.as_api(), "session_id": "sess_1"},
        )
        self.assertEqual(
            self.user.as_api()["seller"],
            {
                "has_food_handler_certification": True,
                "accepted_terms": True,
                "facebook_marketplace_url": "https://www.facebook.com/marketplace/profile/123",
                "etransfer_email": "payouts@example.com",
                "pickup_address": QUEEN.formatted,
                "pickup_lat": QUEEN.lat,
                "pickup_lon": QUEEN.lon,
            },
        )

    @patch("modules.signup.complete.Geoapify.geocode", return_value=QUEEN)
    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_seller_signup_accepts_pasted_marketplace_url(
        self, mock_authenticate, _mock_geocode
    ):
        mock_authenticate.return_value = _signed_in(
            {"sub": "user_abc", "sid": "sess_1"}
        )
        payload = {
            "type": "seller",
            "has_food_handler_certification": True,
            "accepted_terms": True,
            "facebook_marketplace_url": "\u200bfacebook.com/marketplace/profile/123",
            "etransfer_email": "payouts@example.com",
            "pickup_address": "123 Queen St W, Toronto",
        }
        response = _auth_post(self.client, payload)
        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {**self.user.as_api(), "session_id": "sess_1"},
        )
        self.assertEqual(
            self.user.as_api()["seller"],
            {
                "has_food_handler_certification": True,
                "accepted_terms": True,
                "facebook_marketplace_url": "https://facebook.com/marketplace/profile/123",
                "etransfer_email": "payouts@example.com",
                "pickup_address": QUEEN.formatted,
                "pickup_lat": QUEEN.lat,
                "pickup_lon": QUEEN.lon,
            },
        )

    @patch("modules.signup.complete.Geoapify.geocode", return_value=None)
    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_seller_signup_rejects_unknown_address(
        self, mock_authenticate, _mock_geocode
    ):
        mock_authenticate.return_value = _signed_in(
            {"sub": "user_abc", "sid": "sess_1"}
        )
        response = _auth_post(
            self.client,
            {
                "type": "seller",
                "has_food_handler_certification": True,
                "accepted_terms": True,
                "facebook_marketplace_url": "https://www.facebook.com/marketplace/profile/123",
                "etransfer_email": "payouts@example.com",
                "pickup_address": "not a real place",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "invalid_pickup_address"})

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_seller_must_accept_terms(self, mock_authenticate):
        mock_authenticate.return_value = _signed_in(
            {"sub": "user_abc", "sid": "sess_1"}
        )
        response = _auth_post(
            self.client,
            {
                "type": "seller",
                "has_food_handler_certification": False,
                "accepted_terms": False,
                "facebook_marketplace_url": "https://www.facebook.com/marketplace/profile/123",
                "etransfer_email": "payouts@example.com",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "terms_required"})

    def test_signup_requires_clerk_session(self):
        response = self.client.post(
            "/api/signup/",
            data=json.dumps({"type": "buyer"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
