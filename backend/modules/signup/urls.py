from django.urls import path

from . import views

urlpatterns = [
    path("", views.complete, name="complete"),
]
