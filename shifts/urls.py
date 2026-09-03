from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("statistics/", views.shift_statistics, name="shift_statistics"),
    path("calendar/", views.shift_calendar, name="shift_calendar"),
    path("calendar/day/", views.calendar_day, name="calendar_day"),
    path("shifts/", views.shift_list, name="shift_list"),
    path("shifts/export/", views.shift_export_form, name="shift_export"),
    path("shifts/export/csv/", views.shift_export_csv, name="shift_export_csv"),
    path("shifts/add/", views.shift_create, name="shift_create"),
    path("shifts/<int:pk>/edit/", views.shift_update, name="shift_update"),
    path("shifts/<int:pk>/delete/", views.shift_delete, name="shift_delete"),
]
