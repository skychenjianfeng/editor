from django.http import HttpResponse
from django.utils.cache import patch_vary_headers


class DevCorsMiddleware:
    """Minimal CORS for local development (calc app on :5179)."""

    ALLOWED_ORIGINS = {
        "http://localhost:5179",
        "http://127.0.0.1:5179",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("Origin")
        if request.method == "OPTIONS":
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)
        if origin in self.ALLOWED_ORIGINS:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
            response["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
            patch_vary_headers(response, ("Origin",))
        return response
