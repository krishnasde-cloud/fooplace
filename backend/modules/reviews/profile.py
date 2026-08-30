import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg, Count
from django.http import JsonResponse

from modules.listings.models import Order
from modules.reviews.models import Review
from modules.users.models import User


def completed_orders_for(seller: User) -> int:
    return Order.objects.filter(
        listing__seller=seller, status=Order.Status.PICKED_UP
    ).count()


def seller_card(user: User) -> dict:
    profile = getattr(user, "seller_profile", None)
    stats = Review.objects.filter(seller=user).aggregate(
        average_rating=Avg("stars"),
        review_count=Count("id"),
    )
    average = stats["average_rating"]
    raw = {
        "id": user.pk,
        "name": user.display_name,
        "neighbourhood": profile.neighbourhood if profile is not None else "",
        "has_food_handler_certification": bool(
            profile and profile.has_food_handler_certification
        ),
        "joined_at": user.first_logged_in,
        "completed_orders": completed_orders_for(user),
        "average_rating": round(float(average), 2) if average is not None else None,
        "review_count": stats["review_count"],
    }
    return json.loads(json.dumps(raw, cls=DjangoJSONEncoder))


def seller_public_api(seller_id) -> dict | JsonResponse:
    seller = (
        User.objects.select_related("seller_profile")
        .filter(pk=seller_id, user_type=User.UserType.SELLER)
        .first()
    )
    if seller is None:
        return JsonResponse({"detail": "not_found"}, status=404)
    reviews = (
        Review.objects.filter(seller=seller)
        .select_related("buyer")
        .order_by("-created_at")
    )
    return {**seller_card(seller), "reviews": [review.as_api() for review in reviews]}
