from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("sellers/", views.sellers, name="sellers"),
    path("sellers/<str:user_id>/", views.seller_action, name="seller_action"),
    path("listings/", views.listings, name="listings"),
    path("listings/<int:listing_id>/", views.listing_action, name="listing_action"),
    path("orders/", views.orders, name="orders"),
]
