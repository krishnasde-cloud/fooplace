import json

from django.db.models import Case, IntegerField, When
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from modules.listings.models import Order
from modules.orders.models import BuyerNotification
from modules.orders.place import place_order
from modules.orders.service import confirm_hours, confirm_order, expire_overdue
from modules.users.models import User

_ORDER_SELECT = (
    "listing",
    "listing__seller",
    "listing__seller__seller_profile",
    "buyer",
)


def _json_body(request) -> dict | JsonResponse:
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
    return record


def _seller_orders(seller: User):
    orders = Order.objects.select_related(*_ORDER_SELECT).prefetch_related("history")
    if seller.user_type != User.UserType.ADMIN:
        orders = orders.filter(listing__seller=seller)
    return orders.order_by(
        Case(
            When(status=Order.Status.PENDING, then=0),
            default=1,
            output_field=IntegerField(),
        ),
        "-created_at",
    )


def _buyer_order(request, order_id) -> Order | JsonResponse:
    order = (
        Order.objects.select_related(*_ORDER_SELECT)
        .prefetch_related("history")
        .filter(pk=order_id, buyer=request.user.record)
        .first()
    )
    if order is None:
        return JsonResponse({"detail": "not_found"}, status=404)
    return order


def _serialize(order: Order) -> JsonResponse:
    order.refresh_status()
    return JsonResponse(order.as_api())


@csrf_exempt
@require_GET
def incoming(request):
    seller = _seller_or_error(request)
    if isinstance(seller, JsonResponse):
        return seller
    expire_overdue()
    orders = _seller_orders(seller)
    return JsonResponse(
        {
            "confirm_hours": confirm_hours(),
            "orders": [order.as_api() for order in orders],
        }
    )


@csrf_exempt
def index(request):
    if request.method == "POST":
        return _create(request)
    if request.method != "GET":
        return JsonResponse({"detail": "method_not_allowed"}, status=405)
    expire_overdue()
    orders = (
        Order.objects.filter(buyer=request.user.record)
        .select_related(*_ORDER_SELECT)
        .prefetch_related("history")
        .order_by("-created_at")
    )
    return JsonResponse(
        {"orders": [order.refresh_status().as_api() for order in orders]}
    )


def _create(request):
    data = _json_body(request)
    if isinstance(data, JsonResponse):
        return data
    result = place_order(
        request.user.record,
        data.get("listing_id"),
        data.get("quantity", 1),
    )
    if isinstance(result, JsonResponse):
        return result
    result = (
        Order.objects.select_related(*_ORDER_SELECT)
        .prefetch_related("history")
        .get(pk=result.pk)
    )
    return JsonResponse(result.as_api(), status=201)


@require_GET
def detail(request, order_id):
    order = _buyer_order(request, order_id)
    if isinstance(order, JsonResponse):
        return order
    return _serialize(order)


@csrf_exempt
@require_POST
def confirm(request, order_id: int):
    seller = _seller_or_error(request)
    if isinstance(seller, JsonResponse):
        return seller
    orders = Order.objects.select_related(*_ORDER_SELECT)
    if seller.user_type != User.UserType.ADMIN:
        orders = orders.filter(listing__seller=seller)
    order = orders.filter(pk=order_id).first()
    if order is None:
        return JsonResponse({"detail": "not_found"}, status=404)

    data = _json_body(request)
    if isinstance(data, JsonResponse):
        return data
    result = confirm_order(order, etransfer_received=data.get("etransfer_received"))
    if isinstance(result, JsonResponse):
        return result
    result = (
        Order.objects.select_related(*_ORDER_SELECT)
        .prefetch_related("history")
        .get(pk=result.pk)
    )
    return JsonResponse(result.as_api())


@csrf_exempt
@require_GET
def expire(request):
    expired = expire_overdue()
    orders = (
        Order.objects.filter(pk__in=[order.pk for order in expired])
        .select_related(*_ORDER_SELECT)
        .prefetch_related("history")
    )
    by_id = {order.pk: order for order in orders}
    return JsonResponse(
        {"expired": [by_id[order.pk].as_api() for order in expired]}
    )


@csrf_exempt
@require_GET
def notifications(request):
    if not getattr(request.user, "is_authenticated", False):
        return JsonResponse({"detail": "unauthorized"}, status=401)
    notices = BuyerNotification.objects.filter(
        buyer=request.user.record
    ).select_related("order", "order__listing")
    return JsonResponse(
        {"notifications": [notice.as_api() for notice in notices]}
    )


@csrf_exempt
@require_POST
def deposit_sent(request, order_id):
    order = _buyer_order(request, order_id)
    if isinstance(order, JsonResponse):
        return order
    if order.deposit_sent:
        return JsonResponse({"detail": "deposit_already_sent"}, status=400)
    if order.status != Order.Status.PENDING:
        return JsonResponse({"detail": "invalid_status"}, status=400)
    order.deposit_sent = True
    order.deposit_sent_at = timezone.now()
    order.status = Order.Status.CONFIRMED
    order.save(
        update_fields=["deposit_sent", "deposit_sent_at", "status", "updated_at"]
    )
    return _serialize(order)


@csrf_exempt
@require_POST
def complete(request, order_id):
    order = _buyer_order(request, order_id)
    if isinstance(order, JsonResponse):
        return order
    order.refresh_status()
    if order.status != Order.Status.READY_FOR_PICKUP:
        return JsonResponse({"detail": "invalid_status"}, status=400)
    order.status = Order.Status.COMPLETED
    order.save(update_fields=["status", "updated_at"])
    return JsonResponse(order.as_api())
