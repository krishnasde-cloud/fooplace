from django.urls import path

from . import views

urlpatterns = [
    path("", views.create, name="create"),
    path("orders/", views.orders, name="orders"),
    path("orders/<int:order_id>/complete/", views.complete, name="complete"),
    path("sellers/<int:seller_id>/", views.seller, name="seller"),
]
