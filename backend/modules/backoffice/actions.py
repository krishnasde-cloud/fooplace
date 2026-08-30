from modules.backoffice.models import ListingModeration, SellerReview
from modules.listings.models import Listing


def apply_seller_review(review: SellerReview, action: str) -> SellerReview:
    user = review.user
    if action == "approve":
        review.status = SellerReview.Status.APPROVED
        review.removed = False
        user.is_active = True
    elif action == "reject":
        review.status = SellerReview.Status.REJECTED
        review.removed = False
    elif action == "flag":
        review.flagged = True
    elif action == "unflag":
        review.flagged = False
    elif action == "remove":
        review.removed = True
        review.flagged = True
        user.is_active = False
    elif action == "restore":
        review.removed = False
        review.flagged = False
        if review.status == SellerReview.Status.REJECTED:
            review.status = SellerReview.Status.APPROVED
        user.is_active = True
    else:
        raise ValueError(action)
    review.save()
    user.save(update_fields=["is_active"])
    return review


def apply_listing_moderation(listing: Listing, action: str) -> ListingModeration:
    moderation, _created = ListingModeration.objects.get_or_create(listing=listing)
    if action == "flag":
        moderation.flagged = True
    elif action == "unflag":
        moderation.flagged = False
    elif action == "remove":
        moderation.removed = True
        moderation.flagged = True
    elif action == "restore":
        moderation.removed = False
        moderation.flagged = False
    else:
        raise ValueError(action)
    moderation.save()
    return moderation
