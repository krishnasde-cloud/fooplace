import json
from datetime import date, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from clerk_backend_api.security.types import AuthErrorReason, AuthStatus, RequestState
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from modules.listings.models import Listing, Order
from modules.orders.models import BuyerNotification
from modules.signup.models import SellerProfile
from modules.users.models import User

PHOTO = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQ"
    "AAAABJRU5ErkJggg=="
)


def _signed_in(user_id: str) -> RequestState:
    return RequestState(
        status=AuthStatus.SIGNED_IN,
        token="sess_test",
        payload={"sub": user_id, "sid": "sess_1"},
    )


def _auth(client, method: str, path: str, body: dict | None = None):
    extras = {"HTTP_AUTHORIZATION": "Bearer sess_test"}
    if body is None:
        return getattr(client, method)(path, **extras)
    return getattr(client, method)(
        path,
        data=json.dumps(body),
        content_type="application/json",
        **extras,
    )


def _listing_fields(**overrides) -> dict:
    fields = {
        "photo": PHOTO,
        "dish_name": "Butter chicken",
        "description": "Homemade, mild spice, includes rice.",
        "price": Decimal("14.00"),
        "quantity_available": 4,
        "neighbourhood": "Kensington",
        "pickup_date": date(2026, 9, 2),
        "pickup_window_start": time(17, 0),
        "pickup_window_end": time(19, 0),
        "status": Listing.Status.ACTIVE,
    }
    fields.update(overrides)
    return fields


class OrderCoordinationTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.seller = User.objects.create(
            user_id="user_seller",
            email="seller@example.com",
            user_type=User.UserType.SELLER,
            first_logged_in=now,
            last_logged_in=now,
        )
        self.buyer = User.objects.create(
            user_id="user_buyer",
            email="buyer@example.com",
            user_type=User.UserType.BUYER,
            first_logged_in=now,
            last_logged_in=now,
        )
        self.other = User.objects.create(
            user_id="user_other",
            email="other@example.com",
            user_type=User.UserType.SELLER,
            first_logged_in=now,
            last_logged_in=now,
        )
        self.listing = Listing.objects.create(seller=self.seller, **_listing_fields())

    def _as_seller(self, mock_authenticate):
        mock_authenticate.return_value = _signed_in(self.seller.user_id)

    def _as_buyer(self, mock_authenticate):
        mock_authenticate.return_value = _signed_in(self.buyer.user_id)

    def _order(self, **overrides) -> Order:
        fields = {"listing": self.listing, "buyer": self.buyer, "quantity": 1}
        fields.update(overrides)
        return Order.objects.create(**fields)

    def _reload(self, order: Order) -> Order:
        return (
            Order.objects.select_related("listing", "buyer")
            .prefetch_related("history")
            .get(pk=order.pk)
        )

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_seller_incoming_orders_and_history_on_create(self, mock_authenticate):
        order = self._order()
        other_listing = Listing.objects.create(
            seller=self.other, **_listing_fields(dish_name="Other stew")
        )
        self._order(listing=other_listing)
        self._as_seller(mock_authenticate)
        response = _auth(self.client, "get", "/api/orders/incoming/")
        order = self._reload(order)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"confirm_hours": 4, "orders": [order.as_api()]},
        )
        self.assertEqual(
            [event.as_api() for event in order.history.all()],
            [
                {
                    "id": order.history.get().pk,
                    "status": Order.Status.PENDING,
                    "note": "created",
                    "created_at": order.history.get().as_api()["created_at"],
                }
            ],
        )

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_confirm_requires_etransfer_check(self, mock_authenticate):
        order = self._order()
        self._as_seller(mock_authenticate)
        denied = _auth(
            self.client,
            "post",
            f"/api/orders/{order.pk}/confirm/",
            {},
        )
        self.assertEqual(denied.status_code, 400)
        self.assertEqual(denied.json(), {"detail": "etransfer_not_checked"})

        confirmed = _auth(
            self.client,
            "post",
            f"/api/orders/{order.pk}/confirm/",
            {"etransfer_received": True},
        )
        order = self._reload(order)
        self.assertEqual(confirmed.status_code, 200)
        self.assertEqual(confirmed.json(), order.as_api())
        self.assertEqual(
            [event.status for event in order.history.all()],
            [Order.Status.PENDING, Order.Status.CONFIRMED],
        )

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_buyer_cannot_confirm_or_list_incoming(self, mock_authenticate):
        order = self._order()
        self._as_buyer(mock_authenticate)
        incoming = _auth(self.client, "get", "/api/orders/incoming/")
        confirm = _auth(
            self.client,
            "post",
            f"/api/orders/{order.pk}/confirm/",
            {"etransfer_received": True},
        )
        self.assertEqual(
            (incoming.status_code, incoming.json()),
            (403, {"detail": "seller_required"}),
        )
        self.assertEqual(
            (confirm.status_code, confirm.json()),
            (403, {"detail": "seller_required"}),
        )

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_other_seller_cannot_confirm(self, mock_authenticate):
        order = self._order()
        mock_authenticate.return_value = _signed_in(self.other.user_id)
        response = _auth(
            self.client,
            "post",
            f"/api/orders/{order.pk}/confirm/",
            {"etransfer_received": True},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "not_found"})

    @override_settings(ORDER_CONFIRM_HOURS=1)
    def test_expire_flips_status_restores_quantity_and_notifies_buyer(self):
        listing = Listing.objects.create(
            seller=self.seller,
            **_listing_fields(quantity_available=0, status=Listing.Status.SOLD_OUT),
        )
        order = self._order(listing=listing, quantity=2)
        Order.objects.filter(pk=order.pk).update(
            created_at=timezone.now() - timedelta(hours=2)
        )

        response = self.client.get("/api/orders/expire/")
        order = self._reload(order)
        listing = Listing.objects.get(pk=listing.pk)
        notices = list(
            BuyerNotification.objects.filter(buyer=self.buyer).select_related(
                "order", "order__listing"
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"expired": [order.as_api()]})
        self.assertEqual(
            {
                "status": order.status,
                "quantity_available": listing.quantity_available,
                "listing_status": listing.status,
                "history": [event.status for event in order.history.all()],
                "notifications": [notice.as_api() for notice in notices],
            },
            {
                "status": Order.Status.EXPIRED,
                "quantity_available": 2,
                "listing_status": Listing.Status.ACTIVE,
                "history": [Order.Status.PENDING, Order.Status.EXPIRED],
                "notifications": [notices[0].as_api()] if notices else [],
            },
        )
        self.assertEqual(notices[0].kind, BuyerNotification.Kind.EXPIRED)
        self.assertEqual(notices[0].order_id, order.pk)
        if mail.outbox:
            self.assertEqual(
                [message.to for message in mail.outbox],
                [[self.buyer.email]],
            )

    @override_settings(ORDER_CONFIRM_HOURS=1)
    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_cannot_confirm_after_window(self, mock_authenticate):
        order = self._order()
        Order.objects.filter(pk=order.pk).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        self._as_seller(mock_authenticate)
        response = _auth(
            self.client,
            "post",
            f"/api/orders/{order.pk}/confirm/",
            {"etransfer_received": True},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "expired"})
        self.assertEqual(self._reload(order).status, Order.Status.EXPIRED)

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_buyer_sees_expiry_notification(self, mock_authenticate):
        order = self._order()
        BuyerNotification.objects.create(
            buyer=self.buyer,
            order=order,
            kind=BuyerNotification.Kind.EXPIRED,
            message="Your order for Butter chicken expired because the seller did not confirm the e-transfer in time.",
        )
        self._as_buyer(mock_authenticate)
        response = _auth(self.client, "get", "/api/orders/notifications/")
        notices = list(
            BuyerNotification.objects.filter(buyer=self.buyer).select_related(
                "order", "order__listing"
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"notifications": [notice.as_api() for notice in notices]},
        )

    @override_settings(ORDER_CONFIRM_HOURS=1)
    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_dashboard_expire_updates_order_status_counts(self, mock_authenticate):
        order = self._order()
        Order.objects.filter(pk=order.pk).update(
            created_at=timezone.now() - timedelta(hours=2)
        )
        self._as_seller(mock_authenticate)
        response = _auth(self.client, "get", "/api/listings/mine/")
        listing = Listing.objects.prefetch_related("orders").get(pk=self.listing.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"listings": [listing.as_api()]})
        self.assertEqual(listing.order_status()[Order.Status.EXPIRED], 1)


def _buyer_signed_in(payload: dict) -> RequestState:
    return RequestState(
        status=AuthStatus.SIGNED_IN,
        token="sess_test",
        payload=payload,
    )


def _buyer_auth(client, method, path, user_id="buyer_1", body=None):
    handler = getattr(client, method)
    kwargs = {"HTTP_AUTHORIZATION": "Bearer sess_test"}
    if body is not None:
        kwargs["data"] = json.dumps(body)
        kwargs["content_type"] = "application/json"
    with patch("modules.clerk.clerk_auth.authenticate_request") as mock_authenticate:
        mock_authenticate.return_value = _buyer_signed_in({"sub": user_id, "sid": "sess_1"})
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
        "photo": "https://example.com/pad-thai.jpg",
        "pickup_date": timezone.localdate() + timedelta(days=1),
        "pickup_window_start": time(17, 0),
        "pickup_window_end": time(21, 0),
        "status": Listing.Status.ACTIVE,
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
        created = _buyer_auth(
            self.client,
            "post",
            "/api/orders/",
            body={"listing_id": self.listing.pk, "quantity": 2},
        )
        self.listing.refresh_from_db()
        order = Order.objects.select_related(
            "listing", "listing__seller", "listing__seller__seller_profile", "buyer"
        ).prefetch_related("history").get()
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

        marked = _buyer_auth(
            self.client,
            "post",
            f"/api/orders/{order.pk}/deposit-sent/",
        )
        order = Order.objects.select_related(
            "listing", "listing__seller", "listing__seller__seller_profile", "buyer"
        ).prefetch_related("history").get()
        self.assertEqual(marked.status_code, 200)
        self.assertEqual(marked.json(), order.as_api())
        self.assertEqual(
            {"status": order.status, "deposit_sent": order.deposit_sent},
            {"status": Order.Status.CONFIRMED, "deposit_sent": True},
        )

    def test_deposit_during_pickup_window_is_ready(self):
        self.listing.pickup_date = timezone.localdate()
        self.listing.pickup_window_start = time(0, 0)
        self.listing.pickup_window_end = time(23, 59)
        self.listing.save()

        created = _buyer_auth(
            self.client,
            "post",
            "/api/orders/",
            body={"listing_id": self.listing.pk, "quantity": 1},
        )
        order_id = created.json()["id"]
        marked = _buyer_auth(self.client, "post", f"/api/orders/{order_id}/deposit-sent/")
        self.assertEqual(marked.json()["status"], Order.Status.READY_FOR_PICKUP)

        completed = _buyer_auth(self.client, "post", f"/api/orders/{order_id}/complete/")
        self.assertEqual(completed.json()["status"], Order.Status.COMPLETED)

    def test_order_expires_after_pickup_window(self):
        created = _buyer_auth(
            self.client,
            "post",
            "/api/orders/",
            body={"listing_id": self.listing.pk, "quantity": 2},
        )
        self.listing.pickup_date = timezone.localdate() - timedelta(days=1)
        self.listing.save(update_fields=["pickup_date"])

        detail = _buyer_auth(self.client, "get", f"/api/orders/{created.json()['id']}/")
        self.listing.refresh_from_db()
        self.assertEqual(detail.json()["status"], Order.Status.EXPIRED)
        self.assertEqual(self.listing.quantity_available, 8)

    def test_buyer_only_sees_own_orders(self):
        _buyer_auth(
            self.client,
            "post",
            "/api/orders/",
            body={"listing_id": self.listing.pk, "quantity": 1},
        )
        other = _buyer("buyer_2")
        mine = _buyer_auth(self.client, "get", "/api/orders/", user_id=other.user_id)
        self.assertEqual(mine.json(), {"orders": []})
        hidden = _buyer_auth(
            self.client,
            "get",
            f"/api/orders/{Order.objects.get().pk}/",
            user_id=other.user_id,
        )
        self.assertEqual(hidden.json(), {"detail": "not_found"})
        self.assertEqual(hidden.status_code, 404)

    def test_cannot_order_expired_listing(self):
        self.listing.expires_at = timezone.now() - timedelta(minutes=1)
        self.listing.save(update_fields=["expires_at"])
        response = _auth(
            self.client,
            "post",
            "/api/orders/",
            body={"listing_id": self.listing.pk, "quantity": 1},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "listing_unavailable"})

    def test_cannot_order_more_than_available(self):
        response = _buyer_auth(
            self.client,
            "post",
            "/api/orders/",
            body={"listing_id": self.listing.pk, "quantity": 20},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "insufficient_quantity"})
