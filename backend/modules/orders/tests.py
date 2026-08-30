import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from clerk_backend_api.security.types import AuthErrorReason, AuthStatus, RequestState
from django.test import TestCase
from django.utils import timezone

from modules.listings.models import Listing
from modules.orders.models import Order
from modules.signup.models import SellerProfile
from modules.users.models import User


def _signed_in(payload: dict) -> RequestState:
    return RequestState(
        status=AuthStatus.SIGNED_IN,
        token="sess_test",
        payload=payload,
    )


def _auth(client, method, path, user_id="buyer_1", body=None):
    handler = getattr(client, method)
    kwargs = {"HTTP_AUTHORIZATION": "Bearer sess_test"}
    if body is not None:
        kwargs["data"] = json.dumps(body)
        kwargs["content_type"] = "application/json"
    with patch("modules.clerk.clerk_auth.authenticate_request") as mock_authenticate:
        mock_authenticate.return_value = _signed_in({"sub": user_id, "sid": "sess_1"})
        return handler(path, **kwargs)


def _seller_listing(**overrides) -> Listing:
    now = timezone.now()
    seller = User.objects.create(
        user_id="seller_1",
        email="kitchen@example.com",
        user_type=User.UserType.SELLER,
        first_logged_in=now,
        last_logged_in=now,
    )
    SellerProfile.objects.create(
        user=seller,
        accepted_terms=True,
        facebook_marketplace_url="https://www.facebook.com/marketplace/profile/1",
        etransfer_email="payouts@example.com",
    )
    defaults = {
        "seller": seller,
        "dish_name": "Pad Thai",
        "description": "Tamarind noodles",
        "cuisine": "Thai",
        "neighbourhood": "Kensington",
        "price": Decimal("16.00"),
        "quantity_available": 8,
        "photos": ["https://example.com/pad-thai.jpg"],
        "pickup_start": now + timedelta(hours=2),
        "pickup_end": now + timedelta(hours=8),
    }
    defaults.update(overrides)
    return Listing.objects.create(**defaults)


def _buyer(user_id="buyer_1") -> User:
    now = timezone.now()
    return User.objects.create(
        user_id=user_id,
        email=f"{user_id}@example.com",
        user_type=User.UserType.BUYER,
        first_logged_in=now,
        last_logged_in=now,
    )


class OrderFlowTests(TestCase):
    def setUp(self):
        self.listing = _seller_listing()
        self.buyer = _buyer()

    def test_orders_require_a_session(self):
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {"detail": AuthErrorReason.SESSION_TOKEN_MISSING.name},
        )

    def test_place_order_then_mark_deposit_sent(self):
        created = _auth(
            self.client,
            "post",
            "/api/orders/",
            body={"listing_id": self.listing.pk, "quantity": 2},
        )
        self.listing.refresh_from_db()
        order = Order.objects.get()
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json(), order.as_api())
        self.assertEqual(
            {
                "status": order.status,
                "deposit_amount": order.deposit_amount,
                "deposit_sent": order.deposit_sent,
                "quantity_left": self.listing.quantity_available,
                "etransfer": created.json()["seller_etransfer_email"],
            },
            {
                "status": Order.Status.PENDING,
                "deposit_amount": Decimal("16.00"),
                "deposit_sent": False,
                "quantity_left": 6,
                "etransfer": "payouts@example.com",
            },
        )

        marked = _auth(
            self.client,
            "post",
            f"/api/orders/{order.pk}/deposit-sent/",
        )
        order.refresh_from_db()
        self.assertEqual(marked.status_code, 200)
        self.assertEqual(marked.json(), order.as_api())
        self.assertEqual(
            {"status": order.status, "deposit_sent": order.deposit_sent},
            {"status": Order.Status.CONFIRMED, "deposit_sent": True},
        )

    def test_deposit_during_pickup_window_is_ready(self):
        now = timezone.now()
        self.listing.pickup_start = now - timedelta(minutes=10)
        self.listing.pickup_end = now + timedelta(hours=3)
        self.listing.save()

        created = _auth(
            self.client,
            "post",
            "/api/orders/",
            body={"listing_id": self.listing.pk, "quantity": 1},
        )
        order_id = created.json()["id"]
        marked = _auth(self.client, "post", f"/api/orders/{order_id}/deposit-sent/")
        self.assertEqual(marked.json()["status"], Order.Status.READY_FOR_PICKUP)

        completed = _auth(self.client, "post", f"/api/orders/{order_id}/complete/")
        self.assertEqual(completed.json()["status"], Order.Status.COMPLETED)

    def test_order_expires_after_pickup_window(self):
        created = _auth(
            self.client,
            "post",
            "/api/orders/",
            body={"listing_id": self.listing.pk, "quantity": 2},
        )
        self.listing.pickup_end = timezone.now() - timedelta(minutes=1)
        self.listing.save(update_fields=["pickup_end"])

        detail = _auth(self.client, "get", f"/api/orders/{created.json()['id']}/")
        self.listing.refresh_from_db()
        self.assertEqual(detail.json()["status"], Order.Status.EXPIRED)
        self.assertEqual(self.listing.quantity_available, 8)

    def test_buyer_only_sees_own_orders(self):
        _auth(
            self.client,
            "post",
            "/api/orders/",
            body={"listing_id": self.listing.pk, "quantity": 1},
        )
        other = _buyer("buyer_2")
        mine = _auth(self.client, "get", "/api/orders/", user_id=other.user_id)
        self.assertEqual(mine.json(), {"orders": []})
        hidden = _auth(
            self.client,
            "get",
            f"/api/orders/{Order.objects.get().pk}/",
            user_id=other.user_id,
        )
        self.assertEqual(hidden.json(), {"detail": "not_found"})
        self.assertEqual(hidden.status_code, 404)

    def test_cannot_order_more_than_available(self):
        response = _auth(
            self.client,
            "post",
            "/api/orders/",
            body={"listing_id": self.listing.pk, "quantity": 20},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "insufficient_quantity"})
