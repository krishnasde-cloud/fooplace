from django.urls import path

from . import views

urlpatterns = [
    path("incoming/", views.incoming, name="incoming"),
    path("expire/", views.expire, name="expire"),
    path("notifications/", views.notifications, name="notifications"),
    path("<int:order_id>/confirm/", views.confirm, name="confirm"),
]
