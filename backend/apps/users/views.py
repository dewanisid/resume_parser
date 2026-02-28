"""
Auth views: register, login (via simplejwt), token refresh, and /me.

RegisterView and LoginView are custom subclasses so we can attach rate
limiting and audit logging.  RefreshView re-exports TokenRefreshView directly
since there is nothing extra to do there.
"""
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.parser.audit import log_action
from apps.parser.models import AuditLog

from .serializers import RegisterSerializer, UserSerializer


@method_decorator(
    # 5 registrations/hour per IP — prevents mass account creation
    ratelimit(key="ip", rate="5/h", method="POST", block=True),
    name="dispatch",
)
class RegisterView(APIView):
    """
    POST /api/v1/auth/register

    Open endpoint — no auth required.
    Validates the payload, creates the user, and immediately returns a
    JWT access + refresh token pair so the client can start making
    authenticated requests without a second round-trip to /login.

    Rate limit: 5 registrations/hour per IP.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        log_action(request, AuditLog.ACTION_REGISTER, details={"username": user.username})

        # Issue tokens immediately so the caller doesn't need to login separately
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(
    # 10 login attempts/minute per IP — slows down credential stuffing attacks
    ratelimit(key="ip", rate="10/m", method="POST", block=True),
    name="dispatch",
)
class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login

    Subclasses simplejwt's TokenObtainPairView to add rate limiting and
    audit logging on successful login.  Accepts the same payload:
        {"username": "...", "password": "..."}
    Returns the same response:
        {"access": "...", "refresh": "..."}

    Rate limit: 10 attempts/minute per IP.
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # super() returns 200 on success and 401 on bad credentials.
        # Only log successful logins.
        if response.status_code == status.HTTP_200_OK:
            log_action(request, AuditLog.ACTION_LOGIN, details={"username": request.data.get("username", "")})

        return response


# RefreshView — POST /api/v1/auth/refresh
# TokenRefreshView accepts {"refresh": "..."} and returns a new {"access": "..."}.
# No audit logging needed for token refresh — it is a purely technical operation.
RefreshView = TokenRefreshView


class MeView(APIView):
    """
    GET /api/v1/auth/me

    Returns the currently authenticated user's profile.
    Requires a valid JWT access token in the Authorization header:
        Authorization: Bearer <access_token>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
