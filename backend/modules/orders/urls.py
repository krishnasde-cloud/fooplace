from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("incoming/", views.incoming, name="incoming"),
    path("expire/", views.expire, name="expire"),
    path("notifications/", views.notifications, name="notifications"),
    path("<int:order_id>/", views.detail, name="detail"),
    path("<int:order_id>/confirm/", views.confirm, name="confirm"),
    path("<int:order_id>/deposit-sent/", views.deposit_sent, name="deposit_sent"),
    path("<int:order_id>/complete/", views.complete, name="complete"),
]
