from django.http import JsonResponse


def me(request):
    """Return the Clerk user attached by ClerkAuthenticationMiddleware."""
    payload = getattr(request.user, "payload", {})
    return JsonResponse(
        {
            "user_id": request.user.id,
            "session_id": payload.get("sid"),
        }
    )
