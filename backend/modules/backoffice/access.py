from django.db.models import Q

from modules.backoffice.models import SellerReview
from modules.users.models import User


def seller_can_list(user: User) -> bool:
    if user.user_type == User.UserType.ADMIN:
        return True
    if user.user_type != User.UserType.SELLER:
        return False
    review = getattr(user, "seller_review", None)
    if review is None:
        return True
    return review.can_sell()


def hidden_from_marketplace() -> Q:
    return (
        Q(moderation__removed=True)
        | Q(seller__is_active=False)
        | Q(seller__seller_review__removed=True)
        | Q(seller__seller_review__status=SellerReview.Status.PENDING)
        | Q(seller__seller_review__status=SellerReview.Status.REJECTED)
    )


def listing_is_hidden(listing) -> bool:
    review = getattr(listing.seller, "seller_review", None)
    moderation = getattr(listing, "moderation", None)
    if not listing.seller.is_active:
        return True
    if review is not None and (
        review.removed or review.status in {SellerReview.Status.PENDING, SellerReview.Status.REJECTED}
    ):
        return True
    return bool(moderation is not None and moderation.removed)
