import json

from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from modules.backoffice.access import hidden_from_marketplace, listing_is_hidden, seller_can_list
from modules.listings.models import Listing, Order, deposit_for
from modules.listings.payload import listing_fields_from
from modules.orders.service import expire_overdue
from modules.users.models import User


def _parse_json(request) -> dict | JsonResponse:
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "invalid_json"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"detail": "invalid_json"}, status=400)
    return data


def _seller_or_error(request) -> User | JsonResponse:
    if not getattr(request.user, "is_authenticated", False):
        return JsonResponse({"detail": "seller_required"}, status=403)
    record = request.user.record
    if record.user_type not in {User.UserType.SELLER, User.UserType.ADMIN}:
        return JsonResponse({"detail": "seller_required"}, status=403)
    if not seller_can_list(record):
        return JsonResponse({"detail": "seller_not_approved"}, status=403)
    return record


def _listings_qs():
    return Listing.objects.select_related(
        "seller",
        "seller__seller_profile",
        "seller__seller_review",
        "moderation",
    ).prefetch_related(
        Prefetch("orders", queryset=Order.objects.order_by("created_at"))
    )


def _live_listings():
    return _listings_qs().filter(
        status=Listing.Status.ACTIVE,
        expires_at__gt=timezone.now(),
    )


def _can_manage(listing: Listing, seller: User) -> bool:
    return listing.seller_id == seller.pk or seller.user_type == User.UserType.ADMIN


@csrf_exempt
@require_http_methods(["GET", "POST"])
def collection(request):
    if request.method == "GET":
        listings = (
            _live_listings()
            .exclude(hidden_from_marketplace())
            .order_by("-created_at")
        )
        neighbourhood = (request.GET.get("neighbourhood") or "").strip()
        cuisine = (request.GET.get("cuisine") or "").strip()
        query = (request.GET.get("q") or "").strip()
        if neighbourhood:
            listings = listings.filter(neighbourhood__iexact=neighbourhood)
        if cuisine:
            listings = listings.filter(cuisine__iexact=cuisine)
        if query:
            listings = listings.filter(
                Q(dish_name__icontains=query) | Q(description__icontains=query)
            )
        return JsonResponse({"listings": [item.as_api() for item in listings]})

    seller = _seller_or_error(request)
    if isinstance(seller, JsonResponse):
        return seller
    data = _parse_json(request)
    if isinstance(data, JsonResponse):
        return data
    fields, error = listing_fields_from(data)
    if error is not None:
        return error
    if fields["quantity_available"] < 1:
        return JsonResponse({"detail": "invalid_listing"}, status=400)
    listing = Listing.objects.create(seller=seller, **fields)
    return JsonResponse(listing.as_api(), status=201)


@csrf_exempt
@require_GET
def mine(request):
    seller = _seller_or_error(request)
    if isinstance(seller, JsonResponse):
        return seller
    expire_overdue()
    listings = _listings_qs().filter(seller=seller).order_by("-created_at")
    return JsonResponse({"listings": [item.as_api() for item in listings]})


@csrf_exempt
@require_http_methods(["GET", "PATCH", "DELETE"])
def detail(request, listing_id: int):
    listing = _listings_qs().filter(pk=listing_id).first()
    if listing is None:
        return JsonResponse({"detail": "not_found"}, status=404)

    if request.method == "GET":
        if listing_is_hidden(listing) or listing.is_expired:
            return JsonResponse({"detail": "not_found"}, status=404)
        return JsonResponse(listing.as_api())

    seller = _seller_or_error(request)
    if isinstance(seller, JsonResponse):
        return seller
    if not _can_manage(listing, seller):
        return JsonResponse({"detail": "not_found"}, status=404)

    if request.method == "DELETE":
        listing.delete()
        return JsonResponse({"ok": True})

    data = _parse_json(request)
    if isinstance(data, JsonResponse):
        return data
    fields, error = listing_fields_from(data, partial=True)
    if error is not None:
        return error
    if "pickup_window_start" in fields or "pickup_window_end" in fields:
        start = fields.get("pickup_window_start", listing.pickup_window_start)
        end = fields.get("pickup_window_end", listing.pickup_window_end)
        if start >= end:
            return JsonResponse({"detail": "invalid_pickup"}, status=400)
    for key, value in fields.items():
        setattr(listing, key, value)
    if listing.quantity_available == 0:
        listing.status = Listing.Status.SOLD_OUT
    listing.save()
    listing = _listings_qs().get(pk=listing.pk)
    return JsonResponse(listing.as_api())


@csrf_exempt
@require_POST
def relist(request, listing_id: int):
    seller = _seller_or_error(request)
    if isinstance(seller, JsonResponse):
        return seller
    listing = _listings_qs().filter(pk=listing_id).first()
    if listing is None or not _can_manage(listing, seller):
        return JsonResponse({"detail": "not_found"}, status=404)
    if not listing.is_expired:
        return JsonResponse({"detail": "not_expired"}, status=400)
    if listing.quantity_available < 1:
        return JsonResponse({"detail": "sold_out"}, status=400)
    listing.relist()
    listing = _listings_qs().get(pk=listing.pk)
    return JsonResponse(listing.as_api())


@csrf_exempt
@require_POST
def create_order(request, listing_id: int):
    if not getattr(request.user, "is_authenticated", False):
        return JsonResponse({"detail": "unauthorized"}, status=401)
    buyer = request.user.record
    data = _parse_json(request)
    if isinstance(data, JsonResponse):
        return data
    try:
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        return JsonResponse({"detail": "invalid_listing"}, status=400)
    if quantity < 1:
        return JsonResponse({"detail": "invalid_listing"}, status=400)

    with transaction.atomic():
        listing = (
            Listing.objects.select_for_update()
            .filter(pk=listing_id, status=Listing.Status.ACTIVE)
            .first()
        )
        if listing is None or listing_is_hidden(listing) or listing.is_expired:
            return JsonResponse({"detail": "not_found"}, status=404)
        if listing.seller_id == buyer.pk:
            return JsonResponse({"detail": "own_listing"}, status=400)
        if listing.quantity_available < quantity:
            return JsonResponse({"detail": "sold_out"}, status=400)
        listing.quantity_available -= quantity
        if listing.quantity_available == 0:
            listing.status = Listing.Status.SOLD_OUT
        listing.save(update_fields=["quantity_available", "status", "updated_at"])
        order = Order.objects.create(
            listing=listing,
            buyer=buyer,
            quantity=quantity,
            unit_price=listing.price,
            deposit_amount=deposit_for(listing.price, quantity),
            status=Order.Status.PENDING,
        )

    listing = _listings_qs().get(pk=listing.pk)
    return JsonResponse({"listing": listing.as_api(), "order": order.as_api()}, status=201)
