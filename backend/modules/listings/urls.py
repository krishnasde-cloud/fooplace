from django.urls import path

from . import views

urlpatterns = [
    path("", views.collection, name="collection"),
    path("mine/", views.mine, name="mine"),
    path("<int:listing_id>/", views.detail, name="detail"),
    path("<int:listing_id>/relist/", views.relist, name="relist"),
    path("<int:listing_id>/orders/", views.create_order, name="create_order"),
]
