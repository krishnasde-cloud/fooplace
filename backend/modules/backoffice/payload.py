from modules.backoffice.models import ListingModeration, SellerReview
from modules.listings.models import Listing, Order
from modules.users.models import User


def empty_review() -> dict:
    return {
        "status": SellerReview.Status.APPROVED,
        "flagged": False,
        "removed": False,
        "note": "",
    }


def empty_moderation() -> dict:
    return {"flagged": False, "removed": False, "note": ""}


def seller_as_api(user: User) -> dict:
    review = getattr(user, "seller_review", None)
    seller = getattr(user, "seller_profile", None)
    return {
        "user_id": user.user_id,
        "email": user.email,
        "is_active": user.is_active,
        "type": user.user_type,
        "seller": None if seller is None else seller.as_api(),
        "review": empty_review() if review is None else review.as_api(),
    }


def listing_as_api(listing: Listing) -> dict:
    moderation = getattr(listing, "moderation", None)
    body = listing.as_api()
    body["seller_user_id"] = listing.seller.user_id
    body["seller_email"] = listing.seller.email
    body["moderation"] = empty_moderation() if moderation is None else moderation.as_api()
    return body


def order_as_api(order: Order) -> dict:
    body = order.as_api()
    body["dish_name"] = order.listing.dish_name
    body["buyer_email"] = order.buyer.email
    body["seller_email"] = order.listing.seller.email
    body["seller_user_id"] = order.listing.seller.user_id
    return body


def review_for(user: User) -> SellerReview:
    review, _created = SellerReview.objects.get_or_create(user=user)
    return review


def moderation_for(listing: Listing) -> ListingModeration:
    moderation, _created = ListingModeration.objects.get_or_create(listing=listing)
    return moderation
