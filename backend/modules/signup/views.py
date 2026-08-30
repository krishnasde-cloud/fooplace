import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from modules.signup.complete import apply_signup


@csrf_exempt
@require_POST
def complete(request):
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "invalid_json"}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"detail": "invalid_json"}, status=400)

    result = apply_signup(request.user.record, data)
    if isinstance(result, JsonResponse):
        return result

    body = result.as_api()
    body["session_id"] = getattr(request.user, "payload", {}).get("sid")
    return JsonResponse(body)
