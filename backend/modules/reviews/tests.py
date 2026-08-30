import json
from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from clerk_backend_api.security.types import AuthStatus, RequestState
from django.test import TestCase
from django.utils import timezone

from modules.backoffice.models import SellerReview
from modules.listings.models import Listing, Order
from modules.reviews.models import Review
from modules.reviews.profile import seller_public_api
from modules.signup.models import SellerProfile
from modules.users.models import User


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


class ReviewsTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.seller = User.objects.create(
            user_id="user_seller",
            name="Priya Shah",
            email="seller@example.com",
            user_type=User.UserType.SELLER,
            first_logged_in=now,
            last_logged_in=now,
        )
        SellerProfile.objects.create(
            user=self.seller,
            neighbourhood="Kensington",
            has_food_handler_certification=True,
            accepted_terms=True,
            facebook_marketplace_url="https://www.facebook.com/marketplace/profile/1",
            etransfer_email="payouts@example.com",
        )
        SellerReview.objects.update_or_create(
            user=self.seller,
            defaults={"status": SellerReview.Status.APPROVED},
        )
        self.buyer = User.objects.create(
            user_id="user_buyer",
            name="Asha Patel",
            email="buyer@example.com",
            phone="416-555-0100",
            user_type=User.UserType.BUYER,
            first_logged_in=now,
            last_logged_in=now,
        )
        self.listing = Listing.objects.create(
            seller=self.seller,
            photo="https://example.com/dish.png",
            dish_name="Butter chicken",
            description="Homemade, mild spice.",
            price=Decimal("14.00"),
            quantity_available=4,
            neighbourhood="Kensington",
            pickup_date=date(2026, 9, 2),
            pickup_window_start=time(17, 0),
            pickup_window_end=time(19, 0),
        )

    def _as_buyer(self, mock_authenticate):
        mock_authenticate.return_value = _signed_in(self.buyer.user_id)

    def test_seller_profile_is_public(self):
        order = Order.objects.create(
            listing=self.listing,
            buyer=self.buyer,
            quantity=1,
            status=Order.Status.COMPLETED,
        )
        Review.objects.create(
            order=order,
            buyer=self.buyer,
            seller=self.seller,
            stars=5,
            comment="Still hot at pickup.",
        )
        response = self.client.get(f"/api/reviews/sellers/{self.seller.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), seller_public_api(self.seller.pk))

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_buyer_completes_order_then_reviews(self, mock_authenticate):
        self._as_buyer(mock_authenticate)
        placed = _auth(
            self.client,
            "post",
            "/api/orders/",
            {"listing_id": self.listing.pk, "quantity": 1},
        )
        order = (
            Order.objects.select_related(
                "listing",
                "listing__seller",
                "listing__seller__seller_profile",
                "buyer",
            )
            .prefetch_related("history")
            .get()
        )
        self.assertEqual(placed.status_code, 201)
        self.assertEqual(placed.json(), order.as_api())

        completed = _auth(
            self.client, "post", f"/api/reviews/orders/{order.pk}/complete/"
        )
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.COMPLETED)
        self.assertEqual(completed.status_code, 200)

        reviewed = _auth(
            self.client,
            "post",
            "/api/reviews/",
            {"order_id": order.pk, "stars": 4, "comment": "Great rice."},
        )
        review = Review.objects.get()
        self.assertEqual(reviewed.status_code, 201)
        self.assertEqual(reviewed.json(), review.as_api())

        orders = _auth(self.client, "get", "/api/reviews/orders/")
        profile = self.client.get(f"/api/reviews/sellers/{self.seller.pk}/")
        self.assertEqual(orders.json(), {"orders": [self._buyer_order_payload(order)]})
        self.assertEqual(profile.json(), seller_public_api(self.seller.pk))
        self.assertEqual(profile.json()["completed_orders"], 1)
        self.assertEqual(profile.json()["average_rating"], 4.0)

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_review_requires_completed_order(self, mock_authenticate):
        self._as_buyer(mock_authenticate)
        order = Order.objects.create(
            listing=self.listing, buyer=self.buyer, quantity=1
        )
        response = _auth(
            self.client,
            "post",
            "/api/reviews/",
            {"order_id": order.pk, "stars": 5, "comment": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "order_not_completed"})

    def _buyer_order_payload(self, order: Order) -> dict:
        from modules.reviews.actions import buyer_order_api

        order = (
            Order.objects.select_related(
                "listing",
                "listing__seller",
                "listing__seller__seller_profile",
                "review",
                "review__buyer",
            ).get(pk=order.pk)
        )
        return buyer_order_api(order)
