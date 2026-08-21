from django.urls import path

from . import views

urlpatterns = [
    path("", views.workplace_list, name="workplace_list"),
    path("add/", views.workplace_create, name="workplace_create"),
]
