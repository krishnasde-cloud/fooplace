import json

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from modules.orders.models import Order
from modules.orders.place import place_order

_ORDER_SELECT = (
    "listing",
    "listing__seller",
    "listing__seller__seller_profile",
)


def _json_body(request) -> dict | JsonResponse:
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "invalid_json"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"detail": "invalid_json"}, status=400)
    return data


def _buyer_order(request, order_id) -> Order | JsonResponse:
    order = (
        Order.objects.select_related(*_ORDER_SELECT)
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
def index(request):
    if request.method == "POST":
        return _create(request)
    if request.method != "GET":
        return JsonResponse({"detail": "method_not_allowed"}, status=405)
    orders = (
        Order.objects.filter(buyer=request.user.record)
        .select_related(*_ORDER_SELECT)
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
    return JsonResponse(result.as_api(), status=201)


@require_GET
def detail(request, order_id):
    order = _buyer_order(request, order_id)
    if isinstance(order, JsonResponse):
        return order
    return _serialize(order)


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
