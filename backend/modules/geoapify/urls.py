from django.urls import path

from . import views

urlpatterns = [
    path("autocomplete/", views.autocomplete, name="autocomplete"),
]
