from django.urls import path

from . import views

urlpatterns = [
    path("", views.workplace_list, name="workplace_list"),
    path("add/", views.workplace_create, name="workplace_create"),
    path("<int:pk>/edit/", views.workplace_update, name="workplace_update"),
    path("<int:pk>/delete/", views.workplace_delete, name="workplace_delete"),
]
