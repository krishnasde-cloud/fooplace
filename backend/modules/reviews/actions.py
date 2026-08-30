from django.http import JsonResponse

from modules.listings.models import Order
from modules.reviews.models import Review
from modules.reviews.profile import COMPLETED, seller_card
from modules.signup.complete import clean_text
from modules.users.models import User


def buyer_order_api(order: Order) -> dict:
    review = getattr(order, "review", None)
    return {
        **order.as_api(),
        "dish_name": order.listing.dish_name,
        "seller": seller_card(order.listing.seller),
        "review": review.as_api() if review is not None else None,
    }


def buyer_orders(buyer: User) -> list[dict]:
    orders = (
        Order.objects.filter(buyer=buyer)
        .select_related(
            "listing",
            "listing__seller",
            "listing__seller__seller_profile",
            "review",
            "review__buyer",
        )
        .order_by("-created_at")
    )
    return [buyer_order_api(order) for order in orders]


def complete_order(buyer: User, order_id) -> dict | JsonResponse:
    order = (
        Order.objects.select_related(
            "listing",
            "listing__seller",
            "listing__seller__seller_profile",
            "review",
            "review__buyer",
        )
        .filter(pk=order_id, buyer=buyer)
        .first()
    )
    if order is None:
        return JsonResponse({"detail": "not_found"}, status=404)
    if order.status in {Order.Status.CANCELLED, Order.Status.EXPIRED}:
        return JsonResponse({"detail": "invalid_status"}, status=400)
    if order.status not in COMPLETED:
        order.status = Order.Status.COMPLETED
        order.save(update_fields=["status"])
        order.refresh_from_db()
    return buyer_order_api(order)


def create_review(buyer: User, data: dict) -> dict | JsonResponse:
    try:
        order_id = int(data.get("order_id"))
    except (TypeError, ValueError):
        return JsonResponse({"detail": "invalid_order"}, status=400)
    try:
        stars = int(data.get("stars"))
    except (TypeError, ValueError):
        return JsonResponse({"detail": "invalid_stars"}, status=400)
    if stars < 1 or stars > 5:
        return JsonResponse({"detail": "invalid_stars"}, status=400)

    comment = clean_text(data.get("comment"))
    if len(comment) > 1000:
        return JsonResponse({"detail": "invalid_comment"}, status=400)

    order = (
        Order.objects.select_related("listing", "listing__seller")
        .filter(pk=order_id, buyer=buyer)
        .first()
    )
    if order is None:
        return JsonResponse({"detail": "not_found"}, status=404)
    if order.status not in COMPLETED:
        return JsonResponse({"detail": "order_not_completed"}, status=400)
    if Review.objects.filter(order=order).exists():
        return JsonResponse({"detail": "already_reviewed"}, status=400)

    review = Review.objects.create(
        order=order,
        buyer=buyer,
        seller=order.listing.seller,
        stars=stars,
        comment=comment,
    )
    review.buyer = buyer
    return review.as_api()
