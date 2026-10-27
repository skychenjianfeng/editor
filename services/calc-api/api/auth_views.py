from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


User = get_user_model()


def _current_user(user) -> dict:
    return {
        "user_id": user.pk,
        "email": user.email,
        "display_name": user.get_full_name() or user.username,
    }


def _normalized_email(data: dict) -> str:
    return str(data.get("email") or "").strip().lower()


@method_decorator(ensure_csrf_cookie, name="get")
class CsrfView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrf": True})


@method_decorator(csrf_protect, name="dispatch")
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        email = _normalized_email(data)
        password = str(data.get("password") or "")
        confirm = str(data.get("password_confirm") or "")
        errors = {}

        try:
            validate_email(email)
        except ValidationError:
            errors["email"] = ["请输入有效邮箱"]
        else:
            if len(email) > User._meta.get_field(User.USERNAME_FIELD).max_length:
                errors["email"] = ["邮箱过长"]
            elif User.objects.filter(
                Q(username__iexact=email) | Q(email__iexact=email)
            ).exists():
                errors["email"] = ["该邮箱已注册"]

        if password != confirm:
            errors["password"] = ["两次输入的密码不一致"]
        else:
            user = User(username=email, email=email)
            try:
                validate_password(password, user=user)
            except ValidationError as exc:
                errors["password"] = list(exc.messages)

        if errors:
            return Response(
                {"detail": "注册信息有误", "errors": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User(username=email, email=email)
        user.set_password(password)
        try:
            with transaction.atomic():
                user.save()
        except IntegrityError:
            errors["email"] = ["该邮箱已注册"]
            return Response(
                {"detail": "注册信息有误", "errors": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        request.session.cycle_key()
        return Response(_current_user(user), status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        email = _normalized_email(data)
        password = str(data.get("password") or "")
        user = authenticate(request, username=email, password=password)
        if user is None:
            return Response(
                {"detail": "邮箱或密码错误"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        request.session.cycle_key()
        return Response(_current_user(user))


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(_current_user(request.user))
