import json
from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from clerk_backend_api.security.types import AuthStatus, RequestState
from django.test import TestCase
from django.utils import timezone

from modules.listings.models import Listing, Order
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


def _listing_body(**overrides) -> dict:
    payload = {
        "photo": PHOTO,
        "dish_name": "Butter chicken",
        "description": "Homemade, mild spice, includes rice.",
        "price": "14.00",
        "quantity_available": 4,
        "neighbourhood": "Kensington",
        "pickup_date": "2026-09-02",
        "pickup_window_start": "17:00",
        "pickup_window_end": "19:00",
    }
    payload.update(overrides)
    return payload


class ListingsTests(TestCase):
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

    def _as_seller(self, mock_authenticate):
        mock_authenticate.return_value = _signed_in(self.seller.user_id)

    def _as_buyer(self, mock_authenticate):
        mock_authenticate.return_value = _signed_in(self.buyer.user_id)

    def _create_listing(self, **overrides) -> Listing:
        return Listing.objects.create(seller=self.seller, **_listing_fields(**overrides))

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_seller_creates_listing(self, mock_authenticate):
        self._as_seller(mock_authenticate)
        response = _auth(self.client, "post", "/api/listings/", _listing_body())
        self.assertEqual(response.status_code, 201)
        listing = Listing.objects.get()
        self.assertEqual(response.json(), listing.as_api())

    def test_dashboard_requires_session(self):
        response = self.client.get("/api/listings/mine/")
        self.assertEqual(response.status_code, 401)

    def test_browse_is_public_and_hides_sold_out(self):
        active = self._create_listing()
        self._create_listing(dish_name="Sold stew", status=Listing.Status.SOLD_OUT)
        response = self.client.get("/api/listings/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"listings": [active.as_api()]})

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_dashboard_includes_order_status(self, mock_authenticate):
        listing = self._create_listing()
        Order.objects.create(listing=listing, buyer=self.buyer, quantity=1)
        Order.objects.create(
            listing=listing,
            buyer=self.buyer,
            quantity=1,
            status=Order.Status.CONFIRMED,
        )
        self._as_seller(mock_authenticate)
        response = _auth(self.client, "get", "/api/listings/mine/")
        listing = Listing.objects.prefetch_related("orders").get(pk=listing.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"listings": [listing.as_api()]})

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_edit_delete_and_mark_sold_out(self, mock_authenticate):
        listing = self._create_listing()
        self._as_seller(mock_authenticate)

        edited = _auth(
            self.client,
            "patch",
            f"/api/listings/{listing.pk}/",
            {"dish_name": "Chicken biryani", "quantity_available": 2},
        )
        listing = Listing.objects.prefetch_related("orders").get(pk=listing.pk)
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.json(), listing.as_api())

        sold = _auth(
            self.client,
            "patch",
            f"/api/listings/{listing.pk}/",
            {"status": Listing.Status.SOLD_OUT},
        )
        listing = Listing.objects.prefetch_related("orders").get(pk=listing.pk)
        self.assertEqual(sold.json(), listing.as_api())

        deleted = _auth(self.client, "delete", f"/api/listings/{listing.pk}/")
        self.assertEqual(deleted.json(), {"ok": True})
        self.assertEqual(Listing.objects.count(), 0)

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_buyer_cannot_create_listing(self, mock_authenticate):
        self._as_buyer(mock_authenticate)
        response = _auth(self.client, "post", "/api/listings/", _listing_body())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "seller_required"})

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_seller_cannot_edit_someone_elses_listing(self, mock_authenticate):
        listing = self._create_listing()
        mock_authenticate.return_value = _signed_in(self.other.user_id)
        response = _auth(
            self.client,
            "patch",
            f"/api/listings/{listing.pk}/",
            {"dish_name": "Stolen recipe"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "not_found"})

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_neighbourhood_rejects_street_address(self, mock_authenticate):
        self._as_seller(mock_authenticate)
        response = _auth(
            self.client,
            "post",
            "/api/listings/",
            _listing_body(neighbourhood="14 Maple Street"),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "exact_address_not_allowed"})

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_buyer_order_updates_listing_status(self, mock_authenticate):
        listing = self._create_listing(quantity_available=1)
        self._as_buyer(mock_authenticate)
        response = _auth(
            self.client,
            "post",
            f"/api/listings/{listing.pk}/orders/",
            {"quantity": 1},
        )
        listing = Listing.objects.prefetch_related("orders").get(pk=listing.pk)
        order = Order.objects.get()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {"listing": listing.as_api(), "order": order.as_api()},
        )

    def test_browse_filters_by_neighbourhood_and_cuisine(self):
        kensington = self._create_listing(cuisine="Thai")
        mexican = self._create_listing(
            dish_name="Birria tacos",
            neighbourhood="Leslieville",
            cuisine="Mexican",
        )
        by_hood = self.client.get("/api/listings/", {"neighbourhood": "kensington"})
        by_cuisine = self.client.get("/api/listings/", {"cuisine": "Mexican"})
        by_search = self.client.get("/api/listings/", {"q": "birria"})
        self.assertEqual(
            {
                "hood": by_hood.json(),
                "cuisine": by_cuisine.json(),
                "search": by_search.json(),
            },
            {
                "hood": {"listings": [kensington.as_api()]},
                "cuisine": {"listings": [mexican.as_api()]},
                "search": {"listings": [mexican.as_api()]},
            },
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
