"""URL configuration for the fooplace project."""

from django.contrib import admin
from django.urls import path

from modules.discovery import module_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    *module_urlpatterns(),
]
