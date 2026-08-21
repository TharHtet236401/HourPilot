from django.urls import path

from . import views

urlpatterns = [
    path("", views.workplace_list, name="workplace_list"),
]
