from django.http import JsonResponse


def health(_request):
    """Lightweight liveness endpoint used by the React frontend."""
    return JsonResponse(
        {
            "status": "ok",
            "service": "fooplace-backend",
        }
    )
