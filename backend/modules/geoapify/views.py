from django.http import JsonResponse

from modules.geoapify.client import Geoapify, GeoapifyError


def autocomplete(request):
    text = str(request.GET.get("text") or "").strip()
    if len(text) < 3:
        return JsonResponse({"results": []})
    try:
        places = Geoapify().autocomplete(text)
    except GeoapifyError:
        return JsonResponse({"detail": "geocode_unavailable"}, status=503)
    return JsonResponse({"results": [place.as_api() for place in places]})
