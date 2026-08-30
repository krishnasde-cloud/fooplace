from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:order_id>/", views.detail, name="detail"),
    path("<int:order_id>/deposit-sent/", views.deposit_sent, name="deposit_sent"),
    path("<int:order_id>/complete/", views.complete, name="complete"),
]
