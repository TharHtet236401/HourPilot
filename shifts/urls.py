from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("shifts/", views.shift_list, name="shift_list"),
    path("shifts/add/", views.shift_create, name="shift_create"),
]