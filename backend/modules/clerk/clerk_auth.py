"""Clerk-only authentication for the Django API.

Password, session, and other Django backends are not used. A request is
authenticated only when it carries a valid Clerk session token.
"""

from dataclasses import dataclass

from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import (
    AuthenticateRequestOptions,
    AuthErrorReason,
    RequestState,
)
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from modules.users.models import User
from modules.users.user_sync import link_clerk_user

# Liveness stays public so the SPA can check Django without a session.
PUBLIC_API_PATHS = frozenset({"/api/health/", "/api/health"})


@dataclass
class ClerkUser:
    """Minimal request.user backed by a verified Clerk session token."""

    id: str
    payload: dict
    record: User | None = None

    is_authenticated: bool = True
    is_anonymous: bool = False
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False

    def __post_init__(self) -> None:
        self.pk = self.id
        if self.record is not None:
            self.is_active = self.record.is_active

    def get_username(self) -> str:
        return self.id

    def __str__(self) -> str:
        return self.id


class ClerkBackend:
    """The only AUTHENTICATION_BACKENDS entry. Credentials are never accepted."""

    def authenticate(self, request=None, **credentials):
        return None

    def get_user(self, user_id):
        return None


def verify_clerk_request(request) -> RequestState:
    parties = list(settings.CLERK_AUTHORIZED_PARTIES)
    return authenticate_request(
        request,
        AuthenticateRequestOptions(
            secret_key=settings.CLERK_SECRET_KEY or None,
            jwt_key=settings.CLERK_JWT_KEY or None,
            authorized_parties=parties or None,
            accepts_token=["session_token"],
        ),
    )


def _unauthorized(state: RequestState) -> JsonResponse:
    reason = state.reason.name if state.reason else "unauthorized"
    return JsonResponse({"detail": reason}, status=401)


class ClerkAuthenticationMiddleware(MiddlewareMixin):
    """Resolve request.user from a Clerk session token only.

    Invalid or unsupported tokens are rejected. Missing tokens are anonymous
    on public paths and 401 on every other /api/ route.
    """

    def process_request(self, request):
        state = verify_clerk_request(request)
        request.clerk_state = state

        if state.is_signed_in and state.payload and state.payload.get("sub"):
            record = link_clerk_user(state.payload["sub"], state.payload)
            request.user = ClerkUser(
                id=record.user_id,
                payload=state.payload,
                record=record,
            )
            if not record.is_active:
                return JsonResponse({"detail": "inactive"}, status=401)
            return None

        request.user = AnonymousUser()

        if not request.path.startswith("/api/"):
            return None

        if (
            request.path in PUBLIC_API_PATHS
            and state.reason is AuthErrorReason.SESSION_TOKEN_MISSING
        ):
            return None

        return _unauthorized(state)
