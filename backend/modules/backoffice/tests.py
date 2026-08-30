import json
from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from clerk_backend_api.security.types import AuthStatus, RequestState
from django.test import TestCase
from django.utils import timezone

from modules.backoffice.models import ListingModeration, SellerReview
from modules.backoffice.payload import listing_as_api, order_as_api, seller_as_api
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

    def _as_buyer(self, mock_authenticate):
        mock_authenticate.return_value = _signed_in(self.buyer.user_id)

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
        review = SellerReview.objects.get(user=self.seller)
        self.assertEqual(
            review.as_api(),
            {
                "status": SellerReview.Status.PENDING,
                "flagged": False,
                "removed": False,
                "note": "",
            },
        )
        self.assertEqual(
            self.seller.as_api()["review"],
            review.as_api(),
        )

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
    def test_buyer_cannot_open_backoffice(self, mock_authenticate):
        self._as_buyer(mock_authenticate)
        response = _auth(self.client, "get", "/api/backoffice/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "admin_required"})

    def test_anonymous_cannot_open_backoffice(self):
        response = self.client.get("/api/backoffice/")
        self.assertEqual(response.status_code, 401)

    def _fresh_seller(self) -> User:
        return User.objects.select_related("seller_profile", "seller_review").get(
            pk=self.seller.pk
        )

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_admin_approves_seller_then_seller_can_list(self, mock_authenticate):
        self._as_admin(mock_authenticate)
        pending = _auth(self.client, "get", "/api/backoffice/sellers/?status=pending")
        self.assertEqual(
            pending.json(),
            {"sellers": [seller_as_api(self._fresh_seller())]},
        )
        approved = _auth(
            self.client,
            "post",
            f"/api/backoffice/sellers/{self.seller.user_id}/",
            {"action": "approve", "note": "Looks good"},
        )
        self.assertEqual(approved.json(), seller_as_api(self._fresh_seller()))
        self.assertEqual(
            approved.json()["review"],
            {
                "status": SellerReview.Status.APPROVED,
                "flagged": False,
                "removed": False,
                "note": "Looks good",
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
        rejected = _auth(
            self.client,
            "post",
            f"/api/backoffice/sellers/{self.seller.user_id}/",
            {"action": "reject"},
        )
        self.assertEqual(rejected.json(), seller_as_api(self._fresh_seller()))
        self.assertEqual(rejected.json()["review"]["status"], SellerReview.Status.REJECTED)
        self.assertEqual(
            self.client.get("/api/listings/").json(),
            {"listings": []},
        )

        removed = _auth(
            self.client,
            "post",
            f"/api/backoffice/sellers/{self.seller.user_id}/",
            {"action": "remove", "note": "Spam"},
        )
        seller = self._fresh_seller()
        self.assertEqual(removed.json(), seller_as_api(seller))
        self.assertEqual(
            {
                "removed": seller.seller_review.removed,
                "flagged": seller.seller_review.flagged,
                "is_active": seller.is_active,
                "listing": Listing.objects.filter(pk=listing.pk).exists(),
            },
            {
                "removed": True,
                "flagged": True,
                "is_active": False,
                "listing": True,
            },
        )

        self._as_seller(mock_authenticate)
        blocked = _auth(self.client, "get", "/api/listings/mine/")
        self.assertEqual(blocked.status_code, 401)
        self.assertEqual(blocked.json(), {"detail": "inactive"})

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_admin_flags_and_removes_listing(self, mock_authenticate):
        SellerReview.objects.filter(user=self.seller).update(
            status=SellerReview.Status.APPROVED
        )
        listing = self._listing()
        order = Order.objects.create(listing=listing, buyer=self.buyer, quantity=1)
        self._as_admin(mock_authenticate)

        before = Listing.objects.select_related("seller", "moderation").prefetch_related(
            "orders"
        ).get(pk=listing.pk)
        index = _auth(self.client, "get", "/api/backoffice/")
        listings = _auth(self.client, "get", "/api/backoffice/listings/")
        orders = _auth(self.client, "get", "/api/backoffice/orders/")
        self.assertEqual(
            index.json(),
            {
                "pending_sellers": 0,
                "flagged_sellers": 0,
                "removed_sellers": 0,
                "listings": 1,
                "flagged_listings": 0,
                "removed_listings": 0,
                "orders": 1,
            },
        )
        self.assertEqual(listings.json(), {"listings": [listing_as_api(before)]})
        self.assertEqual(
            orders.json(),
            {"orders": [order_as_api(Order.objects.select_related(
                "buyer", "listing", "listing__seller"
            ).get(pk=order.pk))]},
        )

        flagged = _auth(
            self.client,
            "post",
            f"/api/backoffice/listings/{listing.pk}/",
            {"action": "flag", "note": "Check photo"},
        )
        listing = Listing.objects.select_related("seller", "moderation").prefetch_related(
            "orders"
        ).get(pk=listing.pk)
        self.assertEqual(flagged.json(), listing_as_api(listing))
        self.assertEqual(
            flagged.json()["moderation"],
            {"flagged": True, "removed": False, "note": "Check photo"},
        )
        self.assertEqual(
            self.client.get("/api/listings/").json(),
            {"listings": [listing.as_api()]},
        )

        removed = _auth(
            self.client,
            "post",
            f"/api/backoffice/listings/{listing.pk}/",
            {"action": "remove"},
        )
        listing = Listing.objects.select_related("seller", "moderation").prefetch_related(
            "orders"
        ).get(pk=listing.pk)
        self.assertEqual(removed.json(), listing_as_api(listing))
        self.assertEqual(
            removed.json()["moderation"],
            {"flagged": True, "removed": True, "note": "Check photo"},
        )
        self.assertEqual(self.client.get("/api/listings/").json(), {"listings": []})
        self.assertEqual(
            self.client.get(f"/api/listings/{listing.pk}/").json(),
            {"detail": "not_found"},
        )
        self.assertEqual(Listing.objects.filter(pk=listing.pk).exists(), True)

        restored = _auth(
            self.client,
            "post",
            f"/api/backoffice/listings/{listing.pk}/",
            {"action": "restore"},
        )
        listing = Listing.objects.select_related("seller", "moderation").prefetch_related(
            "orders"
        ).get(pk=listing.pk)
        self.assertEqual(restored.json(), listing_as_api(listing))
        self.assertEqual(
            self.client.get("/api/listings/").json(),
            {"listings": [listing.as_api()]},
        )

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_admin_can_open_django_admin_reviews(self, mock_authenticate):
        self._as_admin(mock_authenticate)
        response = _auth(self.client, "get", "/admin/backoffice/sellerreview/")
        self.assertEqual(response.status_code, 200)
