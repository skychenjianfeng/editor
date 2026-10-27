from rest_framework.authentication import SessionAuthentication


class SessionAuthentication401(SessionAuthentication):
    """Keep anonymous session requests as 401 instead of DRF's default 403."""

    def authenticate_header(self, request):
        return "Session"
