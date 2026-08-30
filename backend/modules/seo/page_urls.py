from django.urls import path

from . import views

urlpatterns = [
    path("robots.txt", views.robots, name="robots"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
    path("listings/<int:listing_id>/", views.listing, name="listing"),
    path("sellers/<int:seller_id>/", views.seller, name="seller"),
    path("", views.browse, name="browse"),
]
