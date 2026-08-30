import json

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from modules.backoffice.access import admin_or_error
from modules.backoffice.models import SellerReview
from modules.backoffice.payload import (
    listing_as_api,
    moderation_for,
    order_as_api,
    review_for,
    seller_as_api,
)
from modules.listings.models import Listing, Order
from modules.users.models import User

SELLER_ACTIONS = frozenset({"approve", "reject", "flag", "unflag", "remove", "restore"})
LISTING_ACTIONS = frozenset({"flag", "unflag", "remove", "restore"})


def _parse_json(request) -> dict | JsonResponse:
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "invalid_json"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"detail": "invalid_json"}, status=400)
    return data


def _sellers_qs():
    return (
        User.objects.filter(
            Q(user_type=User.UserType.SELLER) | Q(seller_profile__isnull=False)
        )
        .select_related("seller_profile", "seller_review")
        .distinct()
        .order_by("email", "user_id")
    )


def _listings_qs():
    return Listing.objects.select_related(
        "seller", "seller__seller_review", "moderation"
    ).prefetch_related("orders")


def _orders_qs():
    return Order.objects.select_related(
        "buyer", "listing", "listing__seller"
    ).order_by("-created_at")


def _filter_sellers(queryset, status: str):
    if status == "pending":
        return queryset.filter(seller_review__status=SellerReview.Status.PENDING)
    if status == "approved":
        return queryset.filter(
            Q(seller_review__status=SellerReview.Status.APPROVED)
            | Q(seller_review__isnull=True)
        )
    if status == "rejected":
        return queryset.filter(seller_review__status=SellerReview.Status.REJECTED)
    if status == "flagged":
        return queryset.filter(seller_review__flagged=True)
    if status == "removed":
        return queryset.filter(Q(seller_review__removed=True) | Q(is_active=False))
    return queryset


@csrf_exempt
@require_GET
def index(request):
    admin = admin_or_error(request)
    if isinstance(admin, JsonResponse):
        return admin
    sellers = _sellers_qs()
    listings = _listings_qs()
    return JsonResponse(
        {
            "pending_sellers": sellers.filter(
                seller_review__status=SellerReview.Status.PENDING
            ).count(),
            "flagged_sellers": sellers.filter(seller_review__flagged=True).count(),
            "removed_sellers": sellers.filter(
                Q(seller_review__removed=True) | Q(is_active=False)
            ).count(),
            "listings": listings.count(),
            "flagged_listings": listings.filter(moderation__flagged=True).count(),
            "removed_listings": listings.filter(moderation__removed=True).count(),
            "orders": _orders_qs().count(),
        }
    )


@csrf_exempt
@require_GET
def sellers(request):
    admin = admin_or_error(request)
    if isinstance(admin, JsonResponse):
        return admin
    status = str(request.GET.get("status") or "")
    rows = _filter_sellers(_sellers_qs(), status)
    return JsonResponse({"sellers": [seller_as_api(user) for user in rows]})


@csrf_exempt
@require_http_methods(["POST"])
def seller_action(request, user_id: str):
    admin = admin_or_error(request)
    if isinstance(admin, JsonResponse):
        return admin
    user = User.objects.filter(user_id=user_id).select_related(
        "seller_profile", "seller_review"
    ).first()
    if user is None:
        return JsonResponse({"detail": "not_found"}, status=404)
    data = _parse_json(request)
    if isinstance(data, JsonResponse):
        return data
    action = data.get("action")
    if action not in SELLER_ACTIONS:
        return JsonResponse({"detail": "invalid_action"}, status=400)
    note = str(data.get("note") or "").strip()
    review = review_for(user)
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
    else:
        review.removed = False
        review.flagged = False
        if review.status == SellerReview.Status.REJECTED:
            review.status = SellerReview.Status.APPROVED
        user.is_active = True
    if note:
        review.note = note
    review.save()
    user.save(update_fields=["is_active"])
    user = User.objects.select_related("seller_profile", "seller_review").get(pk=user.pk)
    return JsonResponse(seller_as_api(user))


@csrf_exempt
@require_GET
def listings(request):
    admin = admin_or_error(request)
    if isinstance(admin, JsonResponse):
        return admin
    rows = _listings_qs().order_by("-created_at")
    return JsonResponse({"listings": [listing_as_api(item) for item in rows]})


@csrf_exempt
@require_http_methods(["POST"])
def listing_action(request, listing_id: int):
    admin = admin_or_error(request)
    if isinstance(admin, JsonResponse):
        return admin
    listing = _listings_qs().filter(pk=listing_id).first()
    if listing is None:
        return JsonResponse({"detail": "not_found"}, status=404)
    data = _parse_json(request)
    if isinstance(data, JsonResponse):
        return data
    action = data.get("action")
    if action not in LISTING_ACTIONS:
        return JsonResponse({"detail": "invalid_action"}, status=400)
    note = str(data.get("note") or "").strip()
    moderation = moderation_for(listing)
    if action == "flag":
        moderation.flagged = True
    elif action == "unflag":
        moderation.flagged = False
    elif action == "remove":
        moderation.removed = True
        moderation.flagged = True
    else:
        moderation.removed = False
        moderation.flagged = False
    if note:
        moderation.note = note
    moderation.save()
    listing = _listings_qs().get(pk=listing.pk)
    return JsonResponse(listing_as_api(listing))


@csrf_exempt
@require_GET
def orders(request):
    admin = admin_or_error(request)
    if isinstance(admin, JsonResponse):
        return admin
    return JsonResponse({"orders": [order_as_api(item) for item in _orders_qs()]})
