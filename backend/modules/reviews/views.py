import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from modules.reviews.actions import buyer_orders, complete_order, create_review
from modules.reviews.profile import seller_public_api


def _json_body(request) -> dict | JsonResponse:
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "invalid_json"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"detail": "invalid_json"}, status=400)
    return data


@require_GET
def seller(request, seller_id: int):
    result = seller_public_api(seller_id)
    if isinstance(result, JsonResponse):
        return result
    return JsonResponse(result)


@csrf_exempt
@require_GET
def orders(request):
    return JsonResponse({"orders": buyer_orders(request.user.record)})


@csrf_exempt
@require_POST
def complete(request, order_id: int):
    result = complete_order(request.user.record, order_id)
    if isinstance(result, JsonResponse):
        return result
    return JsonResponse(result)


@csrf_exempt
@require_POST
def create(request):
    data = _json_body(request)
    if isinstance(data, JsonResponse):
        return data
    result = create_review(request.user.record, data)
    if isinstance(result, JsonResponse):
        return result
    return JsonResponse(result, status=201)
