"""Create and update the local User row from a verified Clerk session."""

from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone

from modules.users.models import User


@dataclass(frozen=True)
class ClerkProfile:
    email: str = ""
    connected_using: str = ""
    is_verified: bool = False
    is_active: bool = True


def link_clerk_user(clerk_user_id: str, payload: dict) -> User:
    """Return the local User for this Clerk id, creating it on first sign-in."""
    now = timezone.now()
    existing = User.objects.filter(user_id=clerk_user_id).first()
    if existing is None:
        profile = profile_for(clerk_user_id, payload)
        return User.objects.create(
            user_id=clerk_user_id,
            email=profile.email,
            connected_using=profile.connected_using,
            is_verified=profile.is_verified,
            is_active=profile.is_active,
            first_logged_in=now,
            last_logged_in=now,
        )

    existing.last_logged_in = now
    fields = ["last_logged_in"]
    if not existing.email:
        profile = profile_for(clerk_user_id, payload)
        if profile.email:
            existing.email = profile.email
            existing.connected_using = profile.connected_using
            existing.is_verified = profile.is_verified
            fields.extend(["email", "connected_using", "is_verified"])
    existing.save(update_fields=fields)
    return existing


def profile_for(clerk_user_id: str, payload: dict) -> ClerkProfile:
    email = payload.get("email") or ""
    if email:
        return ClerkProfile(
            email=email,
            connected_using=str(payload.get("connected_using") or ""),
            is_verified=bool(payload.get("email_verified", False)),
            is_active=True,
        )
    return fetch_clerk_profile(clerk_user_id)


def fetch_clerk_profile(user_id: str) -> ClerkProfile:
    secret = settings.CLERK_SECRET_KEY
    if not secret:
        return ClerkProfile()

    from clerk_backend_api import Clerk

    try:
        clerk_user = Clerk(bearer_auth=secret).users.get(user_id=user_id)
    except Exception:
        return ClerkProfile()

    return profile_from_clerk_user(clerk_user)


def profile_from_clerk_user(clerk_user) -> ClerkProfile:
    emails = list(getattr(clerk_user, "email_addresses", None) or [])
    primary_id = getattr(clerk_user, "primary_email_address_id", None)
    primary = next((item for item in emails if item.id == primary_id), None)
    if primary is None and emails:
        primary = emails[0]

    email = getattr(primary, "email_address", "") if primary else ""
    verification = getattr(primary, "verification", None) if primary else None
    status = getattr(verification, "status", "")
    status_value = getattr(status, "value", status) or ""
    is_verified = str(status_value).lower() == "verified"

    accounts = list(getattr(clerk_user, "external_accounts", None) or [])
    if accounts:
        provider = getattr(accounts[0], "provider", "") or ""
        connected_using = provider.removeprefix("oauth_")
    elif getattr(clerk_user, "password_enabled", False):
        connected_using = "password"
    else:
        connected_using = ""

    banned = bool(getattr(clerk_user, "banned", False))
    locked = bool(getattr(clerk_user, "locked", False))
    return ClerkProfile(
        email=email or "",
        connected_using=connected_using,
        is_verified=is_verified,
        is_active=not (banned or locked),
    )
