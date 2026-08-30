import json
from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from clerk_backend_api.security.types import AuthStatus, RequestState
from django.test import TestCase
from django.utils import timezone

from modules.backoffice.models import ListingModeration, SellerReview
from modules.listings.models import Listing, Order
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


def _admin_action(client, path: str, action: str, pks: list[int]):
    return client.post(
        path,
        {"action": action, "_selected_action": pks},
        HTTP_AUTHORIZATION="Bearer sess_test",
    )


class BackofficeTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.admin = User.objects.create(
            user_id="user_admin",
            email="admin@example.com",
            user_type=User.UserType.ADMIN,
            first_logged_in=now,
            last_logged_in=now,
        )
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
        self.profile = SellerProfile.objects.create(
            user=self.seller,
            has_food_handler_certification=True,
            accepted_terms=True,
            facebook_marketplace_url="https://facebook.com/marketplace/profile/1",
            etransfer_email="payouts@example.com",
        )
        self.seller.refresh_from_db()

    def _as_admin(self, mock_authenticate):
        mock_authenticate.return_value = _signed_in(self.admin.user_id)

    def _as_seller(self, mock_authenticate):
        mock_authenticate.return_value = _signed_in(self.seller.user_id)

    def _review(self) -> SellerReview:
        return SellerReview.objects.select_related("user").get(user=self.seller)

    def _listing(self, **overrides) -> Listing:
        fields = {
            "seller": self.seller,
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
        return Listing.objects.create(**fields)

    def test_signup_queues_pending_seller_review(self):
        review = self._review()
        self.assertEqual(
            review.as_api(),
            {
                "status": SellerReview.Status.PENDING,
                "flagged": False,
                "removed": False,
                "note": "",
            },
        )
        self.assertEqual(self.seller.as_api()["review"], review.as_api())

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_pending_seller_cannot_create_listing(self, mock_authenticate):
        self._as_seller(mock_authenticate)
        response = _auth(
            self.client,
            "post",
            "/api/listings/",
            {
                "photo": PHOTO,
                "dish_name": "Butter chicken",
                "description": "Homemade, mild spice, includes rice.",
                "price": "14.00",
                "quantity_available": 4,
                "neighbourhood": "Kensington",
                "pickup_date": "2026-09-02",
                "pickup_window_start": "17:00",
                "pickup_window_end": "19:00",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "seller_not_approved"})
        self.assertEqual(Listing.objects.count(), 0)

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_admin_approves_seller_then_seller_can_list(self, mock_authenticate):
        self._as_admin(mock_authenticate)
        review = self._review()
        pending = _auth(self.client, "get", "/admin/backoffice/sellerreview/")
        approved = _admin_action(
            self.client,
            "/admin/backoffice/sellerreview/",
            "approve_sellers",
            [review.pk],
        )
        review = self._review()
        self.assertEqual(
            {
                "pending": pending.status_code,
                "approved": approved.status_code,
                "review": review.as_api(),
            },
            {
                "pending": 200,
                "approved": 302,
                "review": {
                    "status": SellerReview.Status.APPROVED,
                    "flagged": False,
                    "removed": False,
                    "note": "",
                },
            },
        )

        self._as_seller(mock_authenticate)
        created = _auth(
            self.client,
            "post",
            "/api/listings/",
            {
                "photo": PHOTO,
                "dish_name": "Butter chicken",
                "description": "Homemade, mild spice, includes rice.",
                "price": "14.00",
                "quantity_available": 4,
                "neighbourhood": "Kensington",
                "pickup_date": "2026-09-02",
                "pickup_window_start": "17:00",
                "pickup_window_end": "19:00",
            },
        )
        listing = Listing.objects.prefetch_related("orders").get()
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json(), listing.as_api())

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_admin_rejects_and_removes_seller(self, mock_authenticate):
        listing = self._listing()
        self._as_admin(mock_authenticate)
        review = self._review()
        rejected = _admin_action(
            self.client,
            "/admin/backoffice/sellerreview/",
            "reject_sellers",
            [review.pk],
        )
        review = self._review()
        self.assertEqual(rejected.status_code, 302)
        self.assertEqual(
            review.as_api(),
            {
                "status": SellerReview.Status.REJECTED,
                "flagged": False,
                "removed": False,
                "note": "",
            },
        )
        self.assertEqual(self.client.get("/api/listings/").json(), {"listings": []})

        removed = _admin_action(
            self.client,
            "/admin/backoffice/sellerreview/",
            "remove_sellers",
            [review.pk],
        )
        review = self._review()
        self.assertEqual(removed.status_code, 302)
        self.assertEqual(
            {
                "review": review.as_api(),
                "is_active": review.user.is_active,
                "listing": Listing.objects.filter(pk=listing.pk).exists(),
            },
            {
                "review": {
                    "status": SellerReview.Status.REJECTED,
                    "flagged": True,
                    "removed": True,
                    "note": "",
                },
                "is_active": False,
                "listing": True,
            },
        )

        self._as_seller(mock_authenticate)
        blocked = _auth(self.client, "get", "/api/listings/mine/")
        self.assertEqual(blocked.status_code, 401)
        self.assertEqual(blocked.json(), {"detail": "inactive"})

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_admin_views_and_removes_listings_and_orders(self, mock_authenticate):
        SellerReview.objects.filter(user=self.seller).update(
            status=SellerReview.Status.APPROVED
        )
        listing = self._listing()
        Order.objects.create(listing=listing, buyer=self.buyer, quantity=1)
        self._as_admin(mock_authenticate)

        listings = _auth(self.client, "get", "/admin/listings/listing/")
        orders = _auth(self.client, "get", "/admin/listings/order/")
        flagged = _admin_action(
            self.client,
            "/admin/listings/listing/",
            "flag_listings",
            [listing.pk],
        )
        listing = Listing.objects.select_related("moderation").prefetch_related(
            "orders"
        ).get(pk=listing.pk)
        self.assertEqual(
            {
                "listings": listings.status_code,
                "orders": orders.status_code,
                "flagged": flagged.status_code,
                "moderation": listing.moderation.as_api(),
                "public": self.client.get("/api/listings/").json(),
            },
            {
                "listings": 200,
                "orders": 200,
                "flagged": 302,
                "moderation": {"flagged": True, "removed": False, "note": ""},
                "public": {"listings": [listing.as_api()]},
            },
        )

        removed = _admin_action(
            self.client,
            "/admin/listings/listing/",
            "remove_listings",
            [listing.pk],
        )
        listing = Listing.objects.select_related("moderation").prefetch_related(
            "orders"
        ).get(pk=listing.pk)
        self.assertEqual(removed.status_code, 302)
        self.assertEqual(
            listing.moderation.as_api(),
            {"flagged": True, "removed": True, "note": ""},
        )
        self.assertEqual(self.client.get("/api/listings/").json(), {"listings": []})
        self.assertEqual(
            self.client.get(f"/api/listings/{listing.pk}/").json(),
            {"detail": "not_found"},
        )
        self.assertEqual(Listing.objects.filter(pk=listing.pk).exists(), True)

        restored = _admin_action(
            self.client,
            "/admin/listings/listing/",
            "restore_listings",
            [listing.pk],
        )
        listing = Listing.objects.select_related("moderation").prefetch_related(
            "orders"
        ).get(pk=listing.pk)
        self.assertEqual(restored.status_code, 302)
        self.assertEqual(
            listing.moderation.as_api(),
            {"flagged": False, "removed": False, "note": ""},
        )
        self.assertEqual(
            self.client.get("/api/listings/").json(),
            {"listings": [listing.as_api()]},
        )
