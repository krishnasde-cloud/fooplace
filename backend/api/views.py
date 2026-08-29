from django.http import JsonResponse


def health(_request):
    """Lightweight liveness endpoint used by the React frontend."""
    return JsonResponse(
        {
            "status": "ok",
            "service": "fooplace-backend",
        }
    )


def me(request):
    """Return the local User linked to the current Clerk session."""
    payload = getattr(request.user, "payload", {})
    body = request.user.record.as_api()
    body["session_id"] = payload.get("sid")
    return JsonResponse(body)
