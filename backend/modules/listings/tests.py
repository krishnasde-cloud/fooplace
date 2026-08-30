from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from clerk_backend_api.security.types import (
    AuthStatus,
    RequestState,
    TokenVerificationErrorReason,
)
from django.test import TestCase
from django.utils import timezone

from modules.listings.models import Listing
from modules.signup.models import SellerProfile
from modules.users.models import User


def _listing(**overrides) -> Listing:
    now = timezone.now()
    seller = overrides.pop("seller", None)
    if seller is None:
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


class ListingBrowseTests(TestCase):
    def test_browse_is_public_and_filterable(self):
        thai = _listing()
        mexican = _listing(
            seller=thai.seller,
            dish_name="Birria tacos",
            description="Tacos with consomé",
            cuisine="Mexican",
            neighbourhood="Leslieville",
            price=Decimal("18.00"),
            photos=["https://example.com/birria.jpg"],
        )

        unfiltered = self.client.get("/api/listings/")
        by_hood = self.client.get("/api/listings/", {"neighbourhood": "kensington"})
        by_cuisine = self.client.get("/api/listings/", {"cuisine": "Mexican"})
        by_search = self.client.get("/api/listings/", {"q": "consomé"})

        expected_filters = {
            "neighbourhoods": ["Kensington", "Leslieville"],
            "cuisines": ["Mexican", "Thai"],
        }
        self.assertEqual(
            {
                "unfiltered": unfiltered.status_code,
                "body": unfiltered.json(),
                "kensington": by_hood.json(),
                "mexican": by_cuisine.json(),
                "search": by_search.json(),
            },
            {
                "unfiltered": 200,
                "body": {
                    "listings": [mexican.as_api(), thai.as_api()],
                    "filters": expected_filters,
                },
                "kensington": {
                    "listings": [thai.as_api()],
                    "filters": expected_filters,
                },
                "mexican": {
                    "listings": [mexican.as_api()],
                    "filters": expected_filters,
                },
                "search": {
                    "listings": [mexican.as_api()],
                    "filters": expected_filters,
                },
            },
        )

    def test_detail_includes_buyer_fields(self):
        listing = _listing()
        response = self.client.get(f"/api/listings/{listing.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), listing.as_api())

    def test_missing_listing_is_not_found(self):
        response = self.client.get("/api/listings/999/")
        self.assertEqual(response.json(), {"detail": "not_found"})
        self.assertEqual(response.status_code, 404)

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_invalid_token_is_still_rejected(self, mock_authenticate):
        mock_authenticate.return_value = RequestState(
            status=AuthStatus.SIGNED_OUT,
            reason=TokenVerificationErrorReason.TOKEN_INVALID,
        )
        response = self.client.get("/api/listings/")
        self.assertEqual(
            response.json(),
            {"detail": TokenVerificationErrorReason.TOKEN_INVALID.name},
        )
        self.assertEqual(response.status_code, 401)

    def test_browse_allows_missing_session(self):
        response = self.client.get("/api/listings/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "listings": [],
                "filters": {"neighbourhoods": [], "cuisines": []},
            },
        )
