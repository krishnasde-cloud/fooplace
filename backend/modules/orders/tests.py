import json
from datetime import date, time, timedelta
from decimal import Decimal
from unittest.mock import patch

from clerk_backend_api.security.types import AuthStatus, RequestState
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from modules.listings.models import Listing, Order
from modules.orders.models import BuyerNotification
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
