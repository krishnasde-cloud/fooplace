from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from clerk_backend_api.security.types import AuthStatus, RequestState
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.models import User as AuthUser
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from modules.users.models import User


def _signed_in(payload: dict) -> RequestState:
    return RequestState(
        status=AuthStatus.SIGNED_IN,
        token="sess_test",
        payload=payload,
    )


def _user(**overrides) -> User:
    now = timezone.now()
    values = {
        "user_id": "user_abc",
        "email": "buyer@example.com",
        "connected_using": "google",
        "user_type": User.UserType.BUYER,
        "is_active": True,
        "is_verified": True,
        "first_logged_in": now,
        "last_logged_in": now,
    }
    values.update(overrides)
    return User.objects.create(**values)


class AdminFlowTests(TestCase):
    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_admin_can_open_and_edit_users(self, mock_authenticate):
        admin_user = _user(
            user_id="user_admin",
            email="admin@example.com",
            user_type=User.UserType.ADMIN,
        )
        buyer = _user(user_id="user_buyer", email="buyer@example.com")
        mock_authenticate.return_value = _signed_in(
            {"sub": "user_admin", "sid": "sess_1"}
        )
        headers = {"HTTP_AUTHORIZATION": "Bearer sess_test"}

        index = self.client.get("/admin/", **headers)
        changelist = self.client.get("/admin/users/user/", **headers)
        saved = self.client.post(
            f"/admin/users/user/{buyer.pk}/change/",
            {
                "email": "seller@example.com",
                "connected_using": "google",
                "user_type": User.UserType.SELLER,
                "is_active": "on",
                "is_verified": "on",
            },
            **headers,
        )
        buyer.refresh_from_db()

        self.assertEqual(
            {
                "index": index.status_code,
                "changelist": changelist.status_code,
                "saved": saved.status_code,
                "buyer": {
                    "email": buyer.email,
                    "user_type": buyer.user_type,
                    "is_active": buyer.is_active,
                    "is_verified": buyer.is_verified,
                },
                "staff": {
                    "is_staff": index.wsgi_request.user.is_staff,
                    "is_superuser": index.wsgi_request.user.is_superuser,
                    "has_perm": index.wsgi_request.user.has_perm("users.change_user"),
                    "has_module_perms": index.wsgi_request.user.has_module_perms("users"),
                },
            },
            {
                "index": 200,
                "changelist": 200,
                "saved": 302,
                "buyer": {
                    "email": "seller@example.com",
                    "user_type": User.UserType.SELLER,
                    "is_active": True,
                    "is_verified": True,
                },
                "staff": {
                    "is_staff": True,
                    "is_superuser": True,
                    "has_perm": True,
                    "has_module_perms": True,
                },
            },
        )
        self.assertEqual(admin_user.user_type, User.UserType.ADMIN)

    @patch("modules.clerk.clerk_auth.authenticate_request")
    def test_buyer_is_sent_to_admin_login(self, mock_authenticate):
        _user()
        mock_authenticate.return_value = _signed_in(
            {"sub": "user_abc", "sid": "sess_1"}
        )
        response = self.client.get("/admin/", HTTP_AUTHORIZATION="Bearer sess_test")
        self.assertEqual(
            {
                "status": response.status_code,
                "login": "/admin/login/" in response.url,
                "is_staff": response.wsgi_request.user.is_staff,
                "is_superuser": response.wsgi_request.user.is_superuser,
                "has_perm": response.wsgi_request.user.has_perm("users.change_user"),
            },
            {
                "status": 302,
                "login": True,
                "is_staff": False,
                "is_superuser": False,
                "has_perm": False,
            },
        )

    def test_anonymous_is_sent_to_admin_login(self):
        response = self.client.get("/admin/")
        login = self.client.get("/admin/login/")
        self.assertEqual(
            {
                "redirect": response.status_code,
                "login_url": "/admin/login/" in response.url,
                "login_page": login.status_code,
            },
            {
                "redirect": 302,
                "login_url": True,
                "login_page": 200,
            },
        )

    def test_module_models_are_registered_and_auth_users_are_not(self):
        self.assertEqual(
            {
                "user": admin.site.is_registered(User),
                "auth_user": admin.site.is_registered(AuthUser),
                "group": admin.site.is_registered(Group),
            },
            {"user": True, "auth_user": False, "group": False},
        )


class PromoteAdminTests(TestCase):
    def test_promoteadmin_sets_admin_type(self):
        first = datetime(2026, 1, 1, tzinfo=dt_timezone.utc)
        user = User.objects.create(
            user_id="user_abc",
            email="buyer@example.com",
            connected_using="google",
            user_type=User.UserType.BUYER,
            is_active=True,
            is_verified=True,
            first_logged_in=first,
            last_logged_in=first,
        )
        call_command("promoteadmin", "buyer@example.com")
        user.refresh_from_db()
        self.assertEqual(
            {
                "user_id": user.user_id,
                "email": user.email,
                "connected_using": user.connected_using,
                "user_type": user.user_type,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "first_logged_in": user.first_logged_in,
                "last_logged_in": user.last_logged_in,
            },
            {
                "user_id": "user_abc",
                "email": "buyer@example.com",
                "connected_using": "google",
                "user_type": User.UserType.ADMIN,
                "is_active": True,
                "is_verified": True,
                "first_logged_in": first,
                "last_logged_in": first,
            },
        )

    def test_promoteadmin_unknown_user_errors(self):
        with self.assertRaises(CommandError):
            call_command("promoteadmin", "missing@example.com")
